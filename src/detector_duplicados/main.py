"""Orquestador principal del programa.

Une scanner, duper y exporter manteniendo el flujo original.
Soporta deteccion por hash (Fase 1) y deteccion por nombre (legacy).
Persiste resultados en SQLite (Fase 2).
"""

import time

from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

from .config import EXTENSIONES_MULTIMEDIA
from .db import (
    create_connection,
    create_tables,
    guardar_archivos,
    guardar_escaneo,
    guardar_grupos_duplicados,
    obtener_duplicados,
    obtener_escaneo,
    obtener_escaneos,
    obtener_espacio_usado,
)
from .duper import encontrar_duplicados
from .exporter import guardar_resultados_txt
from .scanner import parse_rutas, recopilar_info
from .theme import console
from .ui import (
    mostrar_arbol_resultados,
    mostrar_bienvenida,
    mostrar_comparacion_escaneos,
    mostrar_estado_mensaje,
    mostrar_resultados_tabla,
    preguntar_ruta,
)


def run(
    rutas: list[str] | None = None,
    extensiones: set[str] | None = None,
    modo: str = "preciso",
    persistir: bool = True,
) -> dict:
    """Ejecuta el flujo completo del programa.

    Args:
        rutas: Lista de rutas a escanear. Si None, se pregunta al usuario.
        extensiones: Extensiones a filtrar. None = todos.
        modo: 'preciso' (hash) o 'rapido' (solo nombre).
        persistir: Si True, guarda resultados en SQLite.

    Returns:
        Dict con claves: 'archivos', 'carpetas', 'confirmados',
        'sospechosos', 'escaneo_id', 'total_archivos', 'total_carpetas'.
    """
    from .config import get_current_user

    # Si no se proporcionan rutas, preguntar al usuario
    if rutas is None:
        mostrar_bienvenida(get_current_user())
        ruta_input = preguntar_ruta()
        tipo = "todos"  # Simplificado para Fase 3
        if tipo == "multimedia":
            extensiones = set(EXTENSIONES_MULTIMEDIA)
        rutas = parse_rutas(ruta_input)

    mostrar_bienvenida(get_current_user())
    mostrar_estado_mensaje(f"Escaneando {len(rutas)} ruta(s) en modo [{modo}]...", "info")

    # --- Escaneo con barra de progreso ---
    archivos = []
    carpetas = []
    total_archivos_global = 0
    total_carpetas_global = 0
    total_global = 0
    rutas_no_escaneadas: list[str] = []

    start_time = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as barra:
        for ruta in rutas:
            mostrar_estado_mensaje(f"Escaneando: {ruta}", "info")
            resultado = recopilar_info(
                [ruta],
                extensiones=extensiones,
                barra=barra,
            )
            a, c, ta, tc, t, rne = resultado
            archivos.extend(a)
            carpetas.extend(c)
            total_archivos_global += ta
            total_carpetas_global += tc
            total_global += t
            rutas_no_escaneadas.extend(rne)

    duracion_ms = int((time.time() - start_time) * 1000)

    total_global = total_archivos_global + total_carpetas_global
    mostrar_estado_mensaje(
        f"Escaneo completado. {total_archivos_global} archivos, {total_carpetas_global} carpetas.",
        "success",
    )

    # --- Deteccion ---
    if modo == "preciso":
        confirmados, sospechosos, total_conf, total_sos = encontrar_duplicados(
            archivos, carpetas, confirmar_por_hash=True
        )
    else:
        confirmados, sospechosos, total_conf, total_sos = encontrar_duplicados(
            archivos, carpetas, confirmar_por_hash=False
        )

    mostrar_estado_mensaje(
        f"Duplicados encontrados: {total_conf} confirmados, {total_sos} sospechosos.",
        "warning" if total_conf or total_sos else "success",
    )

    # --- Persistencia en SQLite ---
    escaneo_id = None
    if persistir and archivos:
        conn = create_connection()
        create_tables(conn)
        escaneo_id = guardar_escaneo(
            conn,
            rutas,
            total_archivos_global,
            total_carpetas_global,
            modo,
            duracion_ms,
        )
        guardar_archivos(conn, escaneo_id, archivos)
        guardar_grupos_duplicados(conn, escaneo_id, confirmados, sospechosos)
        conn.close()

    resultado = {
        "archivos": archivos,
        "carpetas": carpetas,
        "confirmados": confirmados,
        "sospechosos": sospechosos,
        "total_conf": total_conf,
        "total_sos": total_sos,
        "escaneo_id": escaneo_id,
        "total_archivos": total_archivos_global,
        "total_carpetas": total_carpetas_global,
        "rutas": rutas,
        "rutas_no_escaneadas": rutas_no_escaneadas,
        "duracion_ms": duracion_ms,
    }

    if total_conf or total_sos:
        guardar_resultados_txt(
            {
                "archivos_duplicados": confirmados,
                "carpetas_duplicadas": sospechosos,
            }
        )

        # FASE 2.0: Generar y abrir HTML automáticamente
        from .html_report import generar_reporte_html

        reporte_html = generar_reporte_html(
            confirmados,
            sospechosos,
            total_archivos_global,
            total_carpetas_global,
            nombre_reporte="resultado.html",
            abrir_navegador=True,
        )
        if reporte_html:
            mostrar_estado_mensaje(f"Reporte generado: {reporte_html}", "success")

        # Mostrar resultados con UI Rich
        mostrar_resultados_tabla(
            confirmados,
            sospechosos,
            total_archivos_global,
            total_carpetas_global,
            rutas_no_escaneadas if rutas_no_escaneadas else None,
        )
        mostrar_arbol_resultados(confirmados)
    else:
        mostrar_estado_mensaje("No se encontraron duplicados.", "success")

    return resultado


def listar_escaneos(limit: int = 10) -> None:
    """Lista los escaneos guardados en la base de datos."""
    conn = create_connection()
    create_tables(conn)

    escaneos = obtener_escaneos(conn, limit)

    if not escaneos:
        mostrar_estado_mensaje("No hay escaneos guardados en la base de datos.", "warning")
        conn.close()
        return

    from rich import box
    from rich.table import Table

    table = Table(show_header=True, header_style="bold", box=box.ROUNDED)
    table.add_column("ID", style="highlight", justify="right")
    table.add_column("Fecha", style="info")
    table.add_column("Archivos", justify="right")
    table.add_column("Carpetas", justify="right")
    table.add_column("Modo", style="path")

    for esc in escaneos:
        table.add_row(
            str(esc["id"]),
            esc["fecha"],
            str(esc["total_archivos"]),
            str(esc["total_carpetas"]),
            esc["modo"],
        )

    console.print(f"\n[bold highlight]=== Escaneos guardados ({len(escaneos)} total) ===[/]")
    console.print(table)

    conn.close()


def obtener_escaneo_detalle(escaneo_id: int) -> dict | None:
    """Obtiene los detalles de un escaneo especifico."""
    from .db import obtener_archivos_escaneo

    conn = create_connection()
    create_tables(conn)

    escaneo = obtener_escaneo(conn, escaneo_id)
    if not escaneo:
        mostrar_estado_mensaje(f"No se encontro el escaneo #{escaneo_id}", "warning")
        conn.close()
        return None

    archivos = obtener_archivos_escaneo(conn, escaneo_id)
    duplicados = obtener_duplicados(conn, escaneo_id)
    confirmados = obtener_duplicados(conn, escaneo_id, confirmado=1)
    sospechosos = obtener_duplicados(conn, escaneo_id, confirmado=0)

    mostrar_estado_mensaje(f"Detalle del escaneo #{escaneo_id}", "info")
    console.print(f"  Fecha: {escaneo['fecha']}")
    console.print(f"  Archivos: {escaneo['total_archivos']}")
    console.print(f"  Carpetas: {escaneo['total_carpetas']}")
    console.print(f"  Modo: {escaneo['modo']}")
    console.print(f"  Duplicados confirmados: {len(confirmados)}")
    console.print(f"  Sospechosos: {len(sospechosos)}")

    conn.close()
    return {
        "escaneo": dict(escaneo),
        "archivos": archivos,
        "duplicados": duplicados,
    }


def mostrar_estadisticas() -> None:
    """Muestra las estadisticas de la base de datos."""
    conn = create_connection()
    create_tables(conn)

    stats = obtener_espacio_usado(conn)

    mostrar_estado_mensaje("=== Estadisticas de la base de datos ===", "info")
    console.print(f"  Archivos de BD: {stats['tamano_archivo']} bytes")
    console.print(f"  Escaneos totales: {stats['total_escaneos']}")
    console.print(f"  Archivos indexados: {stats['total_archivos']}")
    console.print(f"  Duplicados confirmados: {stats['total_duplicados']}")
    console.print(f"  Espacio en duplicados: {stats['espacio_duplicado_bytes']} bytes")

    conn.close()


def comparar_escaneos(id1: int, id2: int) -> dict | None:
    """Compara dos escaneos y muestra las diferencias."""
    from .db import comparar_escaneos

    conn = create_connection()
    create_tables(conn)

    diff = comparar_escaneos(conn, id1, id2)
    conn.close()

    mostrar_comparacion_escaneos(
        {"archivos": diff["nuevos"]},
        {"archivos": diff["eliminados"]},
        diff.get("movidos", []),
        diff.get("duplicados_nuevos", []),
        diff.get("nuevos", []),
    )

    return diff


def eliminar_escaneo_cmd(escaneo_id: int) -> bool:
    """Elimina un escaneo de la base de datos."""
    from .db import eliminar_escaneo

    conn = create_connection()
    create_tables(conn)

    if eliminar_escaneo(conn, escaneo_id):
        mostrar_estado_mensaje(f"Escaneo #{escaneo_id} eliminado", "success")
        conn.close()
        return True
    else:
        mostrar_estado_mensaje(f"Escaneo #{escaneo_id} no encontrado", "error")
        conn.close()
        return False


def preguntar_tipo_archivos() -> str:
    """Pregunta qué tipo de archivos analizar."""
    mostrar_estado_mensaje("¿Qué tipo de archivos quieres analizar?", "info")
    console.print("  1. Solo multimedia")
    console.print("  2. Todos los archivos")
    while True:
        respuesta = input("Selecciona la opción 1 o 2: ").strip()
        if respuesta == "1":
            return "multimedia"
        elif respuesta == "2":
            return "todos"
        else:
            mostrar_estado_mensaje("Opción no válida, intenta de nuevo con (1) o (2)", "warning")


def preguntar_modo_escaneo() -> str:
    """Pregunta modo de escaneo: rápido (nombre) o preciso (hash)."""
    mostrar_estado_mensaje("¿Qué modo de escaneo deseas?", "info")
    console.print("  1. Rápido — solo por nombre (sin hash)")
    console.print("  2. Preciso — con hash SHA256 (detecta falsos positivos)")
    while True:
        respuesta = input("Selecciona la opción 1 o 2: ").strip()
        if respuesta == "1":
            return "rapido"
        elif respuesta == "2":
            return "preciso"
        else:
            mostrar_estado_mensaje("Opción no válida, intenta de nuevo con (1) o (2)", "warning")
