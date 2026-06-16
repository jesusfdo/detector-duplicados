"""Generador de reportes HTML autocontenido.

Crea un archivo HTML con graficos, tablas y estadisticas sobre los duplicados.
"""

import datetime
from pathlib import Path


def generar_reporte_html(
    archivos_duplicados: dict,
    carpetas_duplicadas: dict,
    total_archivos: int,
    total_carpetas: int,
    nombre_reporte: str = "detector_report.html",
) -> str:
    """Genera un reporte HTML autocontenido.

    Args:
        archivos_duplicados: Diccionario con los grupos de duplicados de archivos.
        carpetas_duplicadas: Diccionario con los grupos de carpetas duplicadas.
        total_archivos: Total de archivos escaneados.
        total_carpetas: Total de carpetas escaneadas.
        nombre_reporte: Nombre del archivo HTML a generar.

    Returns:
        Ruta al archivo generado.
    """

    # Generar seccion de archivos
    archivos_html = ""
    total_espacio_duplicado = 0

    for grupo_id, info in archivos_duplicados.items():
        rutas = info.get("rutas", [])
        tamanio = info.get("tamanio") or 0
        espacio_potencial = tamanio * (len(rutas) - 1)
        total_espacio_duplicado += espacio_potencial

        archivos_html += f"""
        <tr>
            <td>{grupo_id}</td>
            <td>{tamanio:,} bytes</td>
            <td>{len(rutas)} copias</td>
            <td>{espacio_potencial:,} bytes</td>
            <td>
                <ul>
                    {"".join(f"<li>{r}</li>" for r in rutas)}
                </ul>
            </td>
        </tr>
        """

    # Generar seccion de carpetas
    carpetas_html = ""
    for grupo_id, info in carpetas_duplicadas.items():
        carpetas_html += f"""
        <tr>
            <td>{grupo_id}</td>
            <td>{info.get("nombre", "Desconocido")}</td>
            <td>{len(info.get("rutas", []))} copias</td>
            <td>
                <ul>
                    {"".join(f"<li>{r}</li>" for r in info.get("rutas", []))}
                </ul>
            </td>
        </tr>
        """

    # Tiempo de generacion
    fecha_generacion = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Plantilla HTML completa
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Duplicados - Detector v1.0.0</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #1e1e1e;
            color: #d4d4d4;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: #569cd6;
            border-bottom: 2px solid #569cd6;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #4ec9b0;
            margin-top: 30px;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background-color: #2d2d30;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #569cd6;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #569cd6;
        }}
        .stat-label {{
            font-size: 14px;
            color: #cccccc;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: #2d2d30;
        }}
        th {{
            background-color: #252526;
            color: #569cd6;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #3e3e42;
        }}
        tr:hover {{
            background-color: #37373d;
        }}
        .warning {{
            background-color: #3d2d00;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
        }}
        footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #3e3e42;
            color: #808080;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Reporte de Archivos Duplicados</h1>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{total_archivos}</div>
                <div class="stat-label">Archivos Escaneados</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(archivos_duplicados)}</div>
                <div class="stat-label">Grupos de Duplicados</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_espacio_duplicado:,}</div>
                <div class="stat-label">Espacio Potencial (bytes)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{fecha_generacion}</div>
                <div class="stat-label">Generado</div>
            </div>
        </div>

        <div class="warning">
            <strong>⚠️ Este reporte es solo informativo.</strong> El usuario debe decidir manualment
            e qué eliminar. <!-- noqa E501 -->        </div>

        <h2>Archivos Duplicados</h2>
        <table>
            <thead>
                <tr>
                    <th>Grupo</th>
                    <th>Tamaño</th>
                    <th>Copias</th>
                    <th>Espacio Recuperable</th>
                    <th>Rutas</th>
                </tr>
            </thead>
            <tbody>
                {archivos_html}
            </tbody>
        </table>

        <h2>Carpetas Duplicadas</h2>
        <table>
            <thead>
                <tr>
                    <th>Grupo</th>
                    <th>Nombre</th>
                    <th>Copias</th>
                    <th>Rutas</th>
                </tr>
            </thead>
            <tbody>
                {carpetas_html}
            </tbody>
        </table>

        <footer>
            Generado por Detector de Duplicados v0.2.0 | {fecha_generacion}
        </footer>
    </div>
</body>
</html>"""

    # Escribir el archivo
    report_path = Path(nombre_reporte)
    report_path.write_text(html_content, encoding="utf-8")

    return str(report_path)


def generar_reporte_desde_db(
    escaneo_id: int,
    nombre_reporte: str = "detector_report_db.html",
) -> str:
    """Genera un reporte HTML cargando datos desde la base de datos SQLite.

    Args:
        escaneo_id: ID del escaneo en la base de datos.
        nombre_reporte: Nombre del archivo HTML a generar.

    Returns:
        Ruta al archivo generado.
    """
    try:
        from .db import (
            create_connection,
            create_tables,
            obtener_archivos_escaneo,
            obtener_duplicados,
            obtener_escaneo,
        )

        conn = create_connection()
        create_tables(conn)

        escaneo = obtener_escaneo(conn, escaneo_id)
        if not escaneo:
            return ""

        _ = obtener_archivos_escaneo(conn, escaneo_id)
        grupos_dup = obtener_duplicados(conn, escaneo_id, confirmado=1)

        total_archivos = escaneo["total_archivos"]
        total_carpetas = escaneo["total_carpetas"]

        # Reconstruir grupos de duplicados en formato html_report
        archivos_duplicados = {}
        carpetas_duplicadas = {}

        for idx, grupo in enumerate(grupos_dup, 1):
            rutas = grupo.get("rutas", "").split("; ") if grupo.get("rutas") else []
            archivos_duplicados[str(idx)] = {
                "rutas": rutas,
                "tamanio": grupo.get("tamanio_bytes", 0),
                "hash": grupo.get("hash_sha256", "N/A"),
            }

    except Exception as e:
        print(f"[error]Error cargando datos de DB: {e}[/]")
        return ""

    # Generar reporte basico con los archivos de la BD
    reporte = generar_reporte_html(
        archivos_duplicados,
        carpetas_duplicadas,
        total_archivos,
        total_carpetas,
        nombre_reporte,
    )

    return reporte
