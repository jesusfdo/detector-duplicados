"""Módulo de escaneo — motor multi-ubicación.

Escanea una o más rutas (locales o UNC), filtra exclusiones,
y recopila información de archivos y carpetas con barra de progreso Rich.
Soporta hashing SHA256 incremental para detección precisa.
"""

import hashlib
import logging
import os
from pathlib import Path

from .config import DEFAULT_EXCLUSIONS, SUBTITLE_EXTENSIONS, VIDEO_EXTENSIONS

logger = logging.getLogger(__name__)
CHUNK_SIZE = 65536  # 64KB — chunk más grande para mejor rendimiento


def _es_subtitulo_excluido(nombre: str, extension: str, archivos_vista_previa: set) -> bool:
    """Determina si un archivo de subtítulos debe ser excluido.

    Un subtítulo se excluye si existe un archivo de video con el mismo
    nombre base en la lista de archivos vista previa.

    Args:
        nombre: Nombre del archivo sin extensión.
        extension: Extensión del archivo (ej: '.srt').
        archivos_vista_previa: Conjunto de nombres base de archivos de video vistos.

    Returns:
        True si el subtítulo debe ser excluido.
    """
    if extension.lower() not in SUBTITLE_EXTENSIONS:
        return False

    nombre_base = nombre.lower()
    return nombre_base in archivos_vista_previa


def validar_ruta(ruta: str) -> tuple[bool, str]:
    """Valida una ruta antes de escanear.

    Verifica existencia y accesibilidad (incluye rutas UNC de Windows).

    Args:
        ruta: Ruta a validar.

    Returns:
        (es_valida, mensaje)
    """
    ruta_path = Path(ruta)

    if not ruta_path.exists():
        return False, f"[red]Ruta inexistente: {ruta}"

    if not ruta_path.is_dir():
        return False, f"[red]No es un directorio: {ruta}"

    if not os.access(str(ruta_path), os.R_OK):
        return False, f"[red]Sin permisos de lectura: {ruta}"

    return True, ""


def parse_rutas(ruta_input: str) -> list[str]:
    """Parsea la entrada del usuario en una lista de rutas.

    Acepta:
    - Una sola ruta: "/media/disco1"
    - Múltiples rutas separadas por coma: "/a,/b,/c"
    - Múltiples rutas separadas por coma con espacios: "/a, /b, /c"

    Args:
        ruta_input: Entrada cruda del usuario.

    Returns:
        Lista de rutas normalizadas (stripped, filtradas vacías).
    """
    if not ruta_input:
        return []

    partes = ruta_input.replace("\n", ",").split(",")
    rutas = [r.strip() for r in partes if r.strip()]
    return rutas


def _walk_directory(
    ruta: Path,
    exclusiones: frozenset[str],
    extensiones: set | None,
    barra: object | None,
    bar_task: object | None,
    archivos: list,
    carpetas: list,
    archivos_video_nombres: set | None = None,
) -> None:
    """Recorre un directorio recursivamente, aplicando exclusiones.

    Los directorios excluidos se saltan completamente (no se visita su subtree).

    FASE 2.0: Soporta exclusión automática de subtítulos cuando existe
    un video con el mismo nombre base.

    Args:
        ruta: Ruta del directorio actual.
        exclusiones: Nombres de directorios/archivos a excluir.
        extensiones: Filtro de extensiones.
        barra: Progress de Rich (opcional).
        bar_task: Tarea de progreso de Rich (opcional).
        archivos: Lista acumuladora de archivos encontrados.
        carpetas: Lista acumuladora de carpetas encontradas.
        archivos_video_nombres: Nombres base de videos para exclusión de subtítulos.
    """
    try:
        elementos = list(ruta.iterdir())
    except (PermissionError, OSError) as e:
        print(f"[red]⚠ No se puede listar {ruta}: {e}")
        return

    for elemento in elementos:
        try:
            # Excluir directorios por nombre (salta TODO el subtree)
            if elemento.name in exclusiones:
                if barra and bar_task is not None:
                    barra.update(bar_task, advance=1)
                continue

            if elemento.is_dir():
                if barra and bar_task is not None:
                    barra.update(bar_task, advance=1)
                carpetas.append(
                    {
                        "nombre": elemento.name,
                        "ruta": str(elemento.resolve()),
                    }
                )
                # Recursivamente explorar el subdirectorio (exclusiones aplicadas recursivamente)
                _walk_directory(
                    elemento,
                    exclusiones,
                    extensiones,
                    barra,
                    bar_task,
                    archivos,
                    carpetas,
                )
            elif elemento.is_file():
                nombre_base = elemento.stem.lower()
                extension = elemento.suffix.lower()

                # FASE 2.0: Excluir subtítulos si existe video con mismo nombre base
                if archivos_video_nombres and _es_subtitulo_excluido(
                    nombre_base, extension, archivos_video_nombres
                ):
                    if barra and bar_task is not None:
                        barra.update(bar_task, advance=1)
                    continue

                if extensiones and extension not in extensiones:
                    if barra and bar_task is not None:
                        barra.update(bar_task, advance=1)
                    continue
                if barra and bar_task is not None:
                    barra.update(bar_task, advance=1)
                stat = elemento.stat()
                archivos.append(
                    {
                        "nombre": elemento.stem,
                        "extension": elemento.suffix,
                        "ruta": str(elemento.resolve()),
                        "tamanio": stat.st_size,
                        "mtime": stat.st_mtime,
                    }
                )
        except (PermissionError, OSError) as e:
            print(f"[red]⚠ Error al procesar {elemento}: {e}")
            if barra and bar_task is not None:
                barra.update(bar_task, advance=1)
            continue


def _count_all(base: Path) -> int:
    """Cuenta todos los archivos y carpetas en un arbol usando os.scandir."""
    count = 0
    stack: list[Path] = [base]
    while stack:
        dirpath = stack.pop()
        try:
            with os.scandir(dirpath) as it:
                for entry in it:
                    count += 1  # este elemento
                    if entry.is_dir():
                        stack.append(Path(entry.path))
        except (PermissionError, OSError):
            pass
    return count


def _collect_video_names(base: Path) -> set:
    """Recolecta nombres base de videos usando os.scandir (no rglob)."""
    nombres: set[str] = set()
    stack: list[Path] = [base]
    while stack:
        dirpath = stack.pop()
        try:
            with os.scandir(dirpath) as it:
                for entry in it:
                    if entry.is_dir():
                        stack.append(Path(entry.path))
                    elif entry.is_file():
                        path_obj = Path(entry.path)
                        ext = path_obj.suffix.lower()
                        if ext in VIDEO_EXTENSIONS:
                            nombres.add(path_obj.stem.lower())
        except (PermissionError, OSError):
            pass
    return nombres


def recopilar_info(
    rutas: list[str],
    extensiones: set | None = None,
    exclusiones: frozenset[str] | None = None,
    barra: object | None = None,
) -> tuple[list[dict[str, str | int]], list[dict[str, str]], int, int, int, list[str]]:
    """Escanea múltiples rutas y recopila información de archivos y carpetas.

    Equivalente a recopilar_info() del script original, pero soporta
    múltiples rutas, exclusiones configurables y barra de progreso Rich.

    FASE 2.0: Incluye exclusión automática de subtítulos cuando existe
    un video con el mismo nombre base.

    Args:
        rutas: Lista de rutas a escanear.
        extensiones: Conjunto de extensiones a filtrar. None = todos.
        exclusiones: Conjuntos de nombres de carpetas/archivos a omitir.
                     Si None, usa DEFAULT_EXCLUSIONS de config.
        barra: Instancia de rich.progress.Progress para mostrar progreso.

    Returns:
        (archivos, carpetas, total_archivos, total_carpetas, total, rutas_no_escaneadas)
    """
    if exclusiones is None:
        exclusiones = DEFAULT_EXCLUSIONS

    archivos: list[dict[str, str | int]] = []
    carpetas: list[dict[str, str]] = []
    rutas_no_escaneadas: list[str] = []

    # Primera pasada: recolectar nombres base de videos usando os.scandir
    archivos_video_nombres: set[str] = set()
    for ruta in rutas:
        ruta_path = Path(ruta)
        if ruta_path.exists() and ruta_path.is_dir():
            archivos_video_nombres.update(_collect_video_names(ruta_path))

    # Segunda pasada: recopilar archivos excluyendo subtítulos duplicados
    for ruta in rutas:
        ruta_path = Path(ruta)
        try:
            if not ruta_path.exists():
                print(f"[red]⚠ Ruta inexistente, omitida: {ruta}")
                rutas_no_escaneadas.append(ruta)
                continue

            if not ruta_path.is_dir():
                print(f"[red]⚠ No es un directorio: {ruta}")
                rutas_no_escaneadas.append(ruta)
                continue

            if not os.access(str(ruta_path), os.R_OK):
                print(f"[red]⚠ Sin permisos de lectura: {ruta}")
                rutas_no_escaneadas.append(ruta)
                continue

            # Contar elementos totales para la barra de progreso usando os.scandir
            total_elementos = _count_all(ruta_path)
            bar_task = (
                barra.add_task(f"Escaneando {ruta}...", total=total_elementos) if barra else None
            )

            _walk_directory(
                ruta_path,
                exclusiones,
                extensiones,
                barra,
                bar_task,
                archivos,
                carpetas,
                archivos_video_nombres,  # Pasar nombres de videos para exclusion
            )

        except (PermissionError, OSError) as e:
            print(f"[red]⚠ Error al acceder a {ruta}: {e}")
            rutas_no_escaneadas.append(ruta)
            continue

    total_archivos = len(archivos)
    total_carpetas = len(carpetas)
    total = total_archivos + total_carpetas

    return archivos, carpetas, total_archivos, total_carpetas, total, rutas_no_escaneadas


def calcular_hash_sha256(ruta_archivo: str) -> str:
    """Calcula el hash SHA256 de un archivo.

    FASE 2.0: Usa un chunk de 64KB para mejor rendimiento en archivos grandes.

    Args:
        ruta_archivo: Ruta al archivo.

    Returns:
        Hash hexadecimal SHA256.

    Raises:
        OSError: Si no se puede leer el archivo.
    """
    sha256 = hashlib.sha256()
    try:
        with open(ruta_archivo, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                sha256.update(chunk)
        return sha256.hexdigest()
    except (PermissionError, OSError) as e:
        logger.warning("No se pudo leer %s: %s", ruta_archivo, e)
        raise


def calcular_hash_grupo_con_thread(
    archivos: list[dict[str, str | int]],
    max_workers: int = 4,
) -> dict[str, str]:
    """Calcula hashes SHA256 en paralelo con ThreadPoolExecutor.

    FASE 2.0: Optimización de rendimiento usando hilos para
    calcular hashes simultáneamente en archivos independientes.

    Args:
        archivos: Lista de dicts con clave 'ruta'.
        max_workers: Número máximo de hilos (default 4).

    Returns:
        Dict: {ruta: hash_sha256}
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    hashes: dict[str, str] = {}

    def hash_one(archivo: dict) -> tuple[str, str | None]:
        """Calcula el hash de un solo archivo."""
        ruta = archivo["ruta"]
        try:
            h = calcular_hash_sha256(ruta)
            return (ruta, h)
        except OSError as e:
            logger.warning("No se pudo hash %s: %s", ruta, e)
            return (ruta, None)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(hash_one, arch): arch for arch in archivos}
        for future in as_completed(futures):
            ruta, h = future.result()
            if h is not None:
                hashes[ruta] = h
            else:
                hashes[ruta] = None  # type: ignore

    return hashes


def agrupar_por_tamanio(
    archivos: list[dict[str, str | int]],
) -> dict[int, list[dict[str, str | int]]]:
    """Agrupa archivos por tamaño en bytes.

    Optimización: solo se necesita hash SHA256 de archivos que comparten
    tamaño, ya que dos archivos de tamaño diferente nunca son idénticos.

    Args:
        archivos: Lista de dicts con 'ruta' y 'tamanio'.

    Returns:
        Dict: {tamanio_bytes: [archivos_con_ese_tamanio]}
    """
    grupos: dict[int, list[dict[str, str | int]]] = {}
    for archivo in archivos:
        tamanio = archivo["tamanio"]
        if tamanio not in grupos:
            grupos[tamanio] = []
        grupos[tamanio].append(archivo)

    # Filtrar grupos de tamaño único — no pueden ser duplicados
    return {
        tam: archivos_con_tam
        for tam, archivos_con_tam in grupos.items()
        if len(archivos_con_tam) > 1
    }


def calcular_hash_grupo(
    archivos: list[dict[str, str | int]],
) -> dict[str, str]:
    """Calcula SHA256 para cada archivo de un grupo de mismo tamaño.

    Args:
        archivos: Lista de dicts con clave 'ruta'.

    Returns:
        Dict: {ruta: hash_sha256}
    """
    hashes: dict[str, str] = {}
    for archivo in archivos:
        ruta = archivo["ruta"]
        try:
            hashes[ruta] = calcular_hash_sha256(ruta)
        except OSError:
            hashes[ruta] = None  # No pudo hash — marca para reporte
    return hashes
