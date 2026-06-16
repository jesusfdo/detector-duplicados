"""Módulo de escaneo — motor multi-ubicación.

Escanea una o más rutas (locales o UNC), filtra exclusiones,
y recopila información de archivos y carpetas con barra de progreso Rich.
Soporta hashing SHA256 incremental para detección precisa.
"""

import hashlib
import logging
import os
from pathlib import Path

from .config import DEFAULT_EXCLUSIONS

logger = logging.getLogger(__name__)
CHUNK_SIZE = 8192  # Lee en chunks de 8KB para archivos grandes


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
) -> None:
    """Recorre un directorio recursivamente, aplicando exclusiones.

    Los directorios excluidos se saltan completamente (no se visita su subtree).

    Args:
        ruta: Ruta del directorio actual.
        exclusiones: Nombres de directorios/archivos a excluir.
        extensiones: Filtro de extensiones.
        barra: Progress de Rich (opcional).
        bar_task: Tarea de progreso de Rich (opcional).
        archivos: Lista acumuladora de archivos encontrados.
        carpetas: Lista acumuladora de carpetas encontradas.
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
                if barra and bar_task:
                    barra.update(bar_task, advance=1)
                continue

            if elemento.is_dir():
                if barra and bar_task:
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
                if extensiones and elemento.suffix.lower() not in extensiones:
                    if barra and bar_task:
                        barra.update(bar_task, advance=1)
                    continue
                if barra and bar_task:
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
            if barra and bar_task:
                barra.update(bar_task, advance=1)
            continue


def recopilar_info(
    rutas: list[str],
    extensiones: set | None = None,
    exclusiones: frozenset[str] | None = None,
    barra: object | None = None,
) -> tuple[list[dict[str, str]], list[dict[str, str]], int, int, int, list[str]]:
    """Escanea múltiples rutas y recopila información de archivos y carpetas.

    Equivalente a recopilar_info() del script original, pero soporta
    múltiples rutas, exclusiones configurables y barra de progreso Rich.

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

            # Contar elementos totales para la barra de progreso
            total_elementos = sum(1 for _ in ruta_path.rglob("*"))
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

    Lee el archivo en chunks para manejar archivos grandes sin consumir
    memoria excesiva.

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
