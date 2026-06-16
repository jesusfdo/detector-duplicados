"""Módulo de Limpieza Inteligente (Smart Deletion).

Implementa heurísticas para sugerir qué archivos eliminar, pero
MANTIENE SIEMPRE la decisión final en manos del usuario (Human-in-the-Loop).
Soporta "Papelera de Reciclaje" en lugar de borrado permanente.
Soporta análisis de metadatos (resolución, calidad de formato).
"""

import logging
import os
import shutil
import struct
from datetime import datetime
from pathlib import Path

from .theme import console

logger = logging.getLogger(__name__)

# Rutas que se consideran "seguras" para mantener
SAFE_PATHS = {
    "/home/",
    "/usr/",
    "/etc/",
    "/var/",
    "/opt/",
}

# Rutas que se consideran "inseguras" (temporales) y candidatas a borrado
INSECURE_PATHS = {
    "/tmp/",
    "/var/tmp/",
    "/scratch/",
    "/cache/",
}

# Calificación de calidad por extensión
# Cuanto mayor el score, mas probable es que se quiera mantener
FORMATO_CALIDAD = {
    ".mkv": 90,
    ".mp4": 85,
    ".mov": 80,
    ".avi": 40,
    ".mpg": 30,
    ".mpeg": 30,
    ".wmv": 35,
    ".flv": 20,
}

# Extensiones que soportan análisis de resolución
FORMATOS_RESOLUCION = {
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".mp4": "video",
    ".mkv": "video",
    ".mov": "video",
    ".avi": "video",
    ".mpg": "video",
}


def obtener_metadata_archivo(ruta: str) -> dict:
    """Intenta obtener metadatos básicos del archivo (resolución, calidad).

    Args:
        ruta: Ruta del archivo.

    Returns:
        Dict con 'calidad', 'resolucion', 'tipo'.
    """
    resultado = {
        "calidad": 0,
        "resolucion": None,
        "tipo": "otro",
    }

    extension = Path(ruta).suffix.lower()

    # 1. Calificación por formato
    if extension in FORMATO_CALIDAD:
        resultado["calidad"] = FORMATO_CALIDAD[extension]

    # 2. Análisis de resolución (solo para imágenes y videos comunes)
    if extension in FORMATOS_RESOLUCION:
        try:
            with open(ruta, "rb") as f:
                # Intento de lectura segura
                header = f.read(256)

                if FORMATOS_RESOLUCION[extension] == "image":
                    if extension in [".jpg", ".jpeg"]:
                        # JPEG: buscar marcador SOS/EOI (FF D9)
                        if b"\xff\xd9" in header:
                            # Simplificado: si tiene tamaño > 1MB, asumimos alta resolución
                            stat = os.stat(ruta)
                            if stat.st_size > 2000000:  # > 2MB
                                resultado["resolucion"] = "alta"
                            else:
                                resultado["resolucion"] = "baja"

                    elif extension == ".png":
                        # PNG: IDAT chunk starts at offset 16
                        if len(header) >= 24:
                            width = struct.unpack(">I", header[16:20])[0]
                            height = struct.unpack(">I", header[20:24])[0]
                            if width > 1920 and height > 1080:
                                resultado["resolucion"] = "4K"
                            elif width > 1280:
                                resultado["resolucion"] = "HD"
                            else:
                                resultado["resolucion"] = "SD"

                elif FORMATOS_RESOLUCION[extension] == "video":
                    if extension == ".mp4":
                        # MP4: box size + type at offset 4 (usually 'ftyp' at 4)
                        # Resolution is inside 'stsz' or 'tkhd', but complex to parse.
                        # Usamos tamaño de archivo como proxy:
                        stat = os.stat(ruta)
                        if stat.st_size > 500 * 1024 * 1024:  # > 500MB
                            resultado["resolucion"] = "HD"
                        elif stat.st_size > 100 * 1024 * 1024:  # > 100MB
                            resultado["resolucion"] = "SD"

                    elif extension == ".mkv":
                        # MKV: Header starts with EBML.
                        # Simplificado: tamaño como proxy
                        stat = os.stat(ruta)
                        if stat.st_size > 2 * 1024 * 1024 * 1024:  # > 2GB
                            resultado["resolucion"] = "HD"
                        else:
                            resultado["resolucion"] = "baja"

                    elif extension in [".avi", ".mov"]:
                        stat = os.stat(ruta)
                        if stat.st_size > 100 * 1024 * 1024:
                            resultado["resolucion"] = "SD"

        except (OSError, PermissionError, struct.error) as e:
            logger.debug(f"No se pudo analizar metadata de {ruta}: {e}")

    return resultado


def calcular_puntuacion(archivo: dict, metadata: dict | None = None) -> int:
    """Calcula una puntuación de riesgo para un archivo.

    Cuanto MAYOR sea el score, MAS probable es que deba ser eliminado.

    Critérios:
        - Fecha: Archivos recientes tienen MENOR riesgo (se mantienen).
        - Ruta: Archivos en /tmp tienen MAYOR riesgo (se borran).
        - Tamaño: Archivos muy grandes tienen MENOR riesgo (peligrosos de borrar).
        - Calidad: Archivos con alta calidad (MKV/MP4) tienen MENOR riesgo.
        - Resolución: Archivos de alta resolución tienen MENOR riesgo.

    Args:
        archivo: Dict con informacion del archivo.
        metadata: Dict con metadatos (calidad, resolucion). Si None, se obtienen.

    Returns:
        Score de 0 a 100 (0 = seguro, 100 = riesgo).
    """
    score = 0
    ruta = Path(archivo.get("ruta", ""))

    # Obtener metadata si no se proporciono
    if metadata is None:
        metadata = obtener_metadata_archivo(str(ruta))

    # 1. Factor Calidad (30% peso)
    if "calidad" in metadata and metadata["calidad"] > 0:
        # Si calidad > 70 (alto), reducir riesgo
        if metadata["calidad"] >= 80:
            score -= 30
        elif metadata["calidad"] < 40:
            score += 20  # Bajo formato = mas riesgo

    # 2. Factor Resolución (20% peso)
    if metadata.get("resolucion"):
        res = metadata["resolucion"]
        if res in ["4K", "HD"]:
            score -= 20  # Alta res = proteger
        elif res == "SD":
            score += 5
        elif res == "baja":
            score += 10

    # 3. Factor Ruta (40% peso) - Mantener de original
    for unsafe in INSECURE_PATHS:
        if str(ruta).startswith(unsafe):
            score += 40
            break
    else:
        for safe in SAFE_PATHS:
            if str(ruta).startswith(safe):
                score += 5
                break

    # 4. Factor Fecha (20% peso)
    # Archivos antiguos son mas propensos a ser obsoletos/junk
    mtime = archivo.get("mtime", 0)
    if mtime:
        fecha_mod = datetime.fromtimestamp(mtime)
        dias_antiguo = (datetime.now() - fecha_mod).days

        if dias_antiguo > 365:
            score += 25  # >1 año = muy probable que sea basura
        elif dias_antiguo > 180:
            score += 15  # 6+ meses = probable junk
        elif dias_antiguo > 30:
            score += 5  # 1+ meses = leve riesgo
    else:
        score += 5  # Sin mtime = riesgo leve

    # 5. Factor Tamaño (15% peso)
    # Archivos pequenos en rutas seguras son sospechosos
    tamanio = archivo.get("tamanio", 0)
    if tamanio < 1024:
        score += 25  # <1KB = casi seguro junk/temp
    elif tamanio < 102400:
        score += 10  # <100KB = posible junk

    return max(0, min(100, score))


def sugerir_eliminado(archivos: list[dict], umbral_riesgo: int = 50) -> dict:
    """Analiza una lista de archivos y sugiere cuáles eliminar.

    Args:
        archivos: Lista de archivos a analizar.
        umbral_riesgo: Score minimo para ser considerado candidato a borrado.

    Returns:
        Dict con claves: 'sugeridos_borrar', 'sugeridos_mantener', 'score_map'.
    """
    resultado = {
        "sugeridos_borrar": [],
        "sugeridos_mantener": [],
        "score_map": {},
    }

    for archivo in archivos:
        metadata = obtener_metadata_archivo(archivo.get("ruta", ""))
        score = calcular_puntuacion(archivo, metadata)
        ruta = archivo.get("ruta", "Desconocido")
        resultado["score_map"][ruta] = score

        # Agregar metadata al resultado para mostrar
        archivo["metadata"] = metadata
        archivo["score"] = score

        if score >= umbral_riesgo:
            resultado["sugeridos_borrar"].append(archivo)
        else:
            resultado["sugeridos_mantener"].append(archivo)

    # Ordenar por score descendente (mayor riesgo primero)
    resultado["sugeridos_borrar"].sort(key=lambda x: x["score"], reverse=True)

    return resultado


def mover_a_papelera(ruta: str, escaneo_id: int | None = None) -> bool:
    """Mueve un archivo a la papelera de reciclaje del sistema.

    En Linux, esto significa la carpeta ~/.local/share/Trash.
    En caso de fallo, intenta mover al home con prefijo TRASH_.
    NO hace borrado permanente.

    Args:
        ruta: Ruta absoluta al archivo a eliminar.
        escaneo_id: ID del escaneo asociado (para log).

    Returns:
        True si se movio exitosamente, False en caso de error.
    """
    try:
        trash_dir = os.path.expanduser("~/.local/share/Trash/files")
        os.makedirs(trash_dir, exist_ok=True)

        nombre_origen = Path(ruta).name
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        nombre_trash = f"{nombre_origen}_{timestamp}"

        destino = os.path.join(trash_dir, nombre_trash)
        shutil.move(ruta, destino)
        logger.info(f"Archivo movido a papelera: {ruta} -> {destino}")

        # Log de accion
        try:
            from .db import create_connection, registrar_accion

            conn = create_connection()
            registrar_accion(conn, "mover", ruta, destino, escaneo_id, exito=True)
        except Exception:
            pass  # No crash si la DB falla

        return True
    except OSError as e:
        logger.error(f"No se pudo mover a papelera {ruta}: {e}")
        # Fallback: intentar mover al home con prefijo TRASH_
        try:
            home_trash = os.path.join(
                os.path.expanduser("~"),
                "TRASH_" + datetime.now().strftime("%Y%m%d%H%M%S") + "_" + Path(ruta).name,
            )
            shutil.move(ruta, home_trash)
            logger.warning(f"Fallback: archivo movido a {home_trash} (no en papelera del SO)")
            return True
        except OSError as e2:
            logger.error(f"Fallback fallido para {ruta}: {e2}")
            return False


def validar_papelera(ruta_archivo: str) -> bool:
    """Verifica si un archivo ya está en la papelera.

    Args:
        ruta_archivo: Ruta del archivo a verificar.

    Returns:
        True si está en papelera, False si no.
    """
    trash_dir = os.path.expanduser("~/.local/share/Trash/files")
    return str(os.path.abspath(ruta_archivo)).startswith(str(os.path.abspath(trash_dir)))


def limpiar_con_interactividad(archivos_duplicados: dict, modo: str = "papelera") -> None:
    """Modo de limpieza interactivo (Human-in-the-Loop).

    Muestra sugerencias basadas en heurísticas, pero el usuario decide.

    Args:
        archivos_duplicados: Diccionario con los grupos de duplicados.
        modo: 'papelera' (mover) o 'borrar' (eliminar directo).
    """
    from .ui import confirmar_accion, menu_interactivo, mostrar_estado_mensaje

    console.print("\n[bold highlight]=== Modo Limpieza Inteligente (v4.5) ===[/]")
    mostrar_estado_mensaje("Analizando duplicados con metadatos y calidad...", "info")

    # Agrupar todos los archivos duplicados para analisis
    todos_archivos = []
    for _grupo, info in archivos_duplicados.items():
        for ruta in info.get("rutas", []):
            # Reconstruir el dict de archivo (simplificado)
            try:
                stat = Path(ruta).stat()
                todos_archivos.append(
                    {
                        "ruta": ruta,
                        "tamanio": stat.st_size,
                        "mtime": stat.st_mtime,
                        "nombre": Path(ruta).name,
                    }
                )
            except OSError:
                pass

    # Analizar y sugerir
    analisis = sugerir_eliminado(todos_archivos)

    if not analisis["sugeridos_borrar"]:
        mostrar_estado_mensaje("No se encontraron candidatos riesgosos para limpieza.", "success")
        return

    console.print(
        f"\n[bold warning]Se encontraron {len(analisis['sugeridos_borrar'])} candidatos a limpiar.[/]\n"  # noqa: E501
    )

    # Mostrar tabla de sugerencias (incluyendo metadata)
    from rich import box
    from rich.table import Table

    table = Table(show_header=True, header_style="bold", box=box.ROUNDED)
    table.add_column("Archivo", style="path")
    table.add_column("Riesgo", style="duplicate", justify="right")
    table.add_column("Calidad", style="highlight")
    table.add_column("Resolución", style="info")
    table.add_column("Tamaño", justify="right")
    table.add_column("Motivo", style="warning")

    for archivo in analisis["sugeridos_borrar"]:
        score = archivo["score"]
        metadata = archivo["metadata"]
        ruta = Path(archivo["ruta"])

        # Calidad
        calidad = "-"
        if metadata.get("calidad"):
            if metadata["calidad"] >= 80:
                calidad = "Alta"
            elif metadata["calidad"] < 40:
                calidad = "Baja"

        # Resolución
        resolucion = "-"
        if metadata.get("resolucion"):
            resolucion = metadata["resolucion"]

        motivo = ""
        for unsafe in INSECURE_PATHS:
            if str(ruta).startswith(unsafe):
                motivo = "Ruta temporal"
                break
        else:
            dias = (datetime.now() - datetime.fromtimestamp(archivo.get("mtime", 0))).days
            if dias > 365:
                motivo = "Antiguo (>1 año)"
            elif dias > 30:
                motivo = "Antiguo (>1 mes)"
            elif archivo.get("tamanio", 0) < 1024:
                motivo = "Archivo pequeno"
            elif metadata.get("calidad", 0) < 40:
                motivo = "Baja calidad (MPG/AVI)"

        table.add_row(
            str(ruta),
            f"[duplicate]{score}[/]",
            f"[warning]{calidad}[/]",
            f"[info]{resolucion}[/]",
            f"{archivo.get('tamanio', 0):,} bytes",
            f"{motivo}",
        )

    console.print(table)

    # Opciones de limpieza
    opciones = [
        "Limpiar todos los candidatos sugeridos",
        "Seleccionar candidatos manualmente",
        "Cancelar limpieza",
    ]

    opcion = menu_interactivo(opciones)

    if opcion == 0:
        console.print("[warning]Cancelando limpieza.[/]")
        return

    elif opcion == 1:
        # Modo manual: listar con IDs
        console.print("\n[bold info]Seleccione los archivos a limpiar (IDs separados por coma):[/]")
        for i, archivo in enumerate(analisis["sugeridos_borrar"], 1):
            metadata = archivo["metadata"]
            calidad_str = ""
            if metadata.get("calidad"):
                calidad_str = f" (Calidad: {metadata['calidad']})"
            res_str = ""
            if metadata.get("resolucion"):
                res_str = f" (Res: {metadata['resolucion']})"
            console.print(f"  [info]{i}[/]. {archivo['ruta']}{calidad_str}{res_str}")

        seleccion = input("IDs a limpiar: ").strip()
        indices = [int(x.strip()) - 1 for x in seleccion.split(",") if x.strip().isdigit()]

        archivos_a_limpiar = [x for i, x in enumerate(analisis["sugeridos_borrar"]) if i in indices]

    elif opcion == 2:
        # Limpiar todos
        archivos_a_limpiar = analisis["sugeridos_borrar"]
    else:
        return

    # Confirmacion final
    if not confirmar_accion(f"¿Proceder con limpieza de {len(archivos_a_limpiar)} archivos?"):
        console.print("[warning]Limpieza cancelada por el usuario.[/]")
        return

    # Ejecutar limpieza
    exitos = 0
    fallos = 0

    for archivo in archivos_a_limpiar:
        ruta = archivo.get("ruta")
        if not ruta:
            continue

        console.print(f"[info]Procesando: {ruta}[/]")

        # Usar shutil para mover a trash (importado arriba)
        exito = mover_a_papelera(ruta)

        if exito:
            console.print("[success]✓ Procesado[/]")
            exitos += 1
        else:
            console.print("[error]✗ Error[/]")
            fallos += 1

    console.print(
        f"\n[bold highlight]Limpieza completada: {exitos} exitosos, {fallos} fallos.[/]\n"
    )


# ============================================================
# Politicas de conservacion (Fase 4 — politica engine)
#
from .config import cargar_perfil  # noqa: E402
from .policies import PolicyError, aplicar_politica  # noqa: E402


def aplicar_politica_a_grupo(
    grupo: dict,
    politica: str = "default",
    perfil: str | None = None,
) -> dict:
    """Aplica una politica de conservacion a un grupo de duplicados.

    Args:
        grupo: Dict con claves 'id', 'rutas', 'tamanio', 'hash', 'escaneo_id'.
        politica: Nombre de la politica.
        perfil: Nombre del perfil de configuracion (usa PERFILES si None).

    Returns:
        Dict con 'accion', 'eliminar', 'mantener', 'motivo'.
    """
    # Determinar politica desde perfil
    politica_real = politica

    if perfil:
        config = cargar_perfil(perfil)
        politica_real = config.get("politica", politica_real)

    # Determinar rutas protegidas
    rutas_protegidas = []
    if perfil:
        config = cargar_perfil(perfil)
        rutas_protegidas = config.get("rutas_protegidas", [])

    return aplicar_politica(grupo, politica_real, rutas_protegidas)


def dry_run_cleanup(
    archivos_duplicados: dict,
    politica: str = "default",
    perfil: str | None = None,
) -> dict:
    """Simula la limpieza sin ejecutar acciones.

    Args:
        archivos_duplicados: Dict con grupos de duplicados.
        politica: Politica a simular.
        perfil: Perfil de configuracion.

    Returns:
        Dict con resumen del dry-run:
            - 'total_archivos': total de archivos duplicados
            - 'total_duplicados': total de grupos
            - 'espacio_total': espacio total ocupado por duplicados
            - 'espacio_recuperable': espacio que se recuperaria con la politica
            - 'acciones': lista de acciones que se ejecutarian
            - 'error': error si la politica no es valida
    """
    resultado = {
        "total_archivos": 0,
        "total_duplicados": len(archivos_duplicados),
        "espacio_total": 0,
        "espacio_recuperable": 0,
        "acciones": [],
        "error": None,
    }

    for grupo_id, info in archivos_duplicados.items():
        rutas = info.get("rutas", [])
        tamanio = info.get("tamanio", 0)

        grupo_dict = {
            "id": grupo_id,
            "rutas": rutas,
            "tamanio": tamanio,
            "hash": info.get("hash"),
            "escaneo_id": info.get("escaneo_id"),
        }

        resultado["total_archivos"] += len(rutas)
        resultado["espacio_total"] += len(rutas) * tamanio

        try:
            decision = aplicar_politica_a_grupo(grupo_dict, politica, perfil)

            resultado["acciones"].append(
                {
                    "grupo_id": grupo_id,
                    "accion": decision["accion"],
                    "eliminar": decision["eliminar"],
                    "mantener": decision["mantener"],
                    "motivo": decision["motivo"],
                    "espacio_recuperable": len(decision["eliminar"]) * tamanio,
                }
            )

            resultado["espacio_recuperable"] += len(decision["eliminar"]) * tamanio

        except PolicyError as e:
            resultado["error"] = str(e)
            break

    return resultado


def ejecutar_cleanup(
    archivos_duplicados: dict,
    politica: str = "default",
    perfil: str | None = None,
    modo: str = "papelera",
    escaneo_id: int | None = None,
    confirmar: bool = True,
) -> dict:
    """Ejecuta la limpieza de duplicados segun politica.

    Args:
        archivos_duplicados: Dict con grupos de duplicados.
        politica: Politica de conservacion a aplicar.
        perfil: Perfil de configuracion.
        modo: 'papelera' (mover a trash) o 'renombrar'.
        escaneo_id: ID del escaneo asociado.
        confirmar: Si True, requiere confirmacion del usuario.

    Returns:
        Dict con 'exitosos', 'fallos', 'acciones_realizadas'.
    """
    dry = dry_run_cleanup(archivos_duplicados, politica, perfil)

    if dry["error"]:
        return {"exitosos": 0, "fallos": 0, "acciones_realizadas": [], "error": dry["error"]}

    if not dry["acciones"]:
        return {
            "exitosos": 0,
            "fallos": 0,
            "acciones_realizadas": [],
            "error": "No hay acciones para ejecutar.",
        }

    # Mostrar resumen
    console.print("\n[bold highlight]=== Resumen de Limpieza (v4.0 — Politica-based) ===[/]\n")
    console.print(f"  Total grupos duplicados: {dry['total_duplicados']}")
    console.print(f"  Total archivos: {dry['total_archivos']}")
    console.print(f"  Espacio total ocupado: {dry['espacio_total']:,} bytes")
    console.print(
        f"  Espacio recuperable: [bold green]{dry['espacio_recuperable']:,} bytes[/bold green]\n"
    )

    # Mostrar acciones propuestas
    for accion in dry["acciones"]:
        console.print(f"  [bold]Grupo #{accion['grupo_id']}:[/]")
        console.print(f"    Accion: {accion['accion']}")
        console.print(f"    Mantener: {len(accion['mantener'])} copia(s)")
        console.print(f"    Eliminar: {len(accion['eliminar'])} copia(s)")
        console.print(f"    Recuperar: [green]{accion['espacio_recuperable']:,} bytes[/green]\n")

    if confirmar:
        from .ui import confirmar_accion

        if not confirmar_accion("¿Proceder con la limpieza segun las acciones propuestas?"):
            return {
                "exitosos": 0,
                "fallos": 0,
                "acciones_realizadas": [],
                "error": "Cancelado por el usuario.",
            }

    # Ejecutar acciones
    exitos = 0
    fallos = 0
    acciones_realizadas = []

    for accion in dry["acciones"]:
        if accion["accion"] == "ninguna":
            continue

        for ruta in accion["eliminar"]:
            try:
                if modo == "papelera":
                    result = mover_a_papelera(ruta, escaneo_id)
                    if result:
                        exitos += 1
                        acciones_realizadas.append({"ruta": ruta, "estado": "movido_a_papelera"})
                else:
                    # Renombrar con sufijo de hash
                    nombre = Path(ruta).name
                    sufijo = f".dup_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    nuevo_nombre = Path(ruta).parent / f"{nombre}{sufijo}"
                    os.rename(ruta, nuevo_nombre)
                    exitos += 1
                    acciones_realizadas.append(
                        {"ruta": ruta, "nuevo_nombre": nuevo_nombre, "estado": "renombrado"}
                    )
            except OSError as e:
                fallos += 1
                acciones_realizadas.append({"ruta": ruta, "error": str(e), "estado": "error"})

    console.print(
        f"\n[bold highlight]Limpieza completada: {exitos} exitosos, {fallos} fallos.[/]\n"
    )

    return {
        "exitosos": exitos,
        "fallos": fallos,
        "acciones_realizadas": acciones_realizadas,
        "espacio_recuperado": dry["espacio_recuperable"],
    }
