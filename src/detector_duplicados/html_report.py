"""Generador de reportes HTML autocontenido con interactividad.

FASE 2.0: Ahora genera reportes con enlaces file:// para abrir
ubicaciones directamente desde el navegador.
"""

import datetime
import os
import platform
import webbrowser
from pathlib import Path


def _archivo_a_ruta_file(ruta: str) -> str:
    """Convierte una ruta local a URL file:// compatible con el SO actual."""
    sistema = platform.system()

    if sistema == "Windows":
        return f"file:///{ruta}"
    else:
        return f"file://{ruta}"


def generar_reporte_html(
    archivos_duplicados: dict,
    carpetas_duplicadas: dict,
    total_archivos: int,
    total_carpetas: int,
    nombre_reporte: str = "detector_report.html",
    abrir_navegador: bool = True,
) -> str:
    """Genera un reporte HTML autocontenido con interactividad.

    Características interactivas:
        - Búsqueda en tiempo real
        - Ordenamiento por columnas
        - Dark/Light toggle
        - Expandir/Colapsar grupos
        - Copiar rutas al portapapeles
        - Filtro por extensión
        - Exportar a CSV

    Args:
        archivos_duplicados: Diccionario con los grupos de duplicados de archivos.
        carpetas_duplicadas: Diccionario con los grupos de carpetas duplicadas.
        total_archivos: Total de archivos escaneados.
        total_carpetas: Total de carpetas escaneadas.
        nombre_reporte: Nombre del archivo HTML a generar.
        abrir_navegador: Si True, abre el HTML en el navegador automáticamente.

    Returns:
        Ruta al archivo generado.
    """

    # Preparar datos para serializar al JS
    archivos_data = {}
    total_espacio_duplicado = 0

    for grupo_id, info in archivos_duplicados.items():
        # Soportar ambos formatos: {key: {"rutas": [...], "tamanio": ...}} (rapido)
        # y {hash: [ruta1, ruta2, ...]} (preciso)
        if isinstance(info, list):
            rutas = info
            tamanio = 0
            espacio_potencial = tamanio * (len(rutas) - 1)
        else:
            rutas = info.get("rutas", [])
            tamanio = info.get("tamanio") or 0
            espacio_potencial = tamanio * (len(rutas) - 1)
        total_espacio_duplicado += espacio_potencial

        archivos_data[str(grupo_id)] = {
            "rutas": rutas,
            "tamanio": tamanio,
            "espacio_potencial": espacio_potencial,
        }

    # Preparar datos de carpetas para serializar al JS
    carpetas_data = {}
    for grupo_id, info in carpetas_duplicadas.items():
        # Soportar varios formatos:
        #   {key: {"rutas": [...], "nombre": ...}} (rapido)
        #   {key: [ruta1, ruta2, ...]} (rapido sospechosos)
        #   {key: [obj1, obj2, ...]} (preciso sospechosos — objetos de archivo)
        if isinstance(info, list):
            if info and isinstance(info[0], dict):
                # Lista de objetos de archivo — extraer solo la ruta
                rutas = [item["ruta"] for item in info if isinstance(item, dict) and "ruta" in item]
                nombre = f"carpeta_{grupo_id}"
            else:
                # Lista de strings de ruta
                rutas = info
                nombre = f"carpeta_{grupo_id}"
        elif isinstance(info, dict):
            rutas = info.get("rutas", [])
            nombre = info.get("nombre", "Desconocido")
        else:
            rutas = [info] if info else []
            nombre = f"carpeta_{grupo_id}"

        carpetas_data[str(grupo_id)] = {
            "nombre": nombre,
            "rutas": rutas,
            "copias": len(rutas),
        }

    # Tiempo de generación
    fecha_generacion = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Plantilla HTML completa
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Duplicados - Detector</title>
    <style>
        :root {{
            --bg: #1e1e1e;
            --bg-card: #2d2d30;
            --bg-header: #252526;
            --text: #d4d4d4;
            --text-muted: #808080;
            --accent: #569cd6;
            --accent-hover: #4ec9b0;
            --border: #3e3e42;
            --warning-bg: #3d2d00;
        }}

        [data-theme="light"] {{
            --bg: #f5f5f5;
            --bg-card: #ffffff;
            --bg-header: #e8e8e8;
            --text: #333333;
            --text-muted: #888888;
            --accent: #0066cc;
            --accent-hover: #0088aa;
            --border: #d0d0d0;
            --warning-bg: #fff3cd;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 20px;
            transition: background-color 0.3s, color 0.3s;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        h1 {{
            color: var(--accent);
            border-bottom: 2px solid var(--accent);
            padding-bottom: 10px;
        }}

        h2 {{
            color: var(--accent);
            margin-top: 30px;
        }}

        .toolbar {{
            display: flex;
            gap: 15px;
            margin: 20px 0;
            flex-wrap: wrap;
            align-items: center;
        }}

        .search-box {{
            flex: 1;
            min-width: 250px;
            padding: 10px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 4px;
            color: var(--text);
            font-size: 14px;
        }}

        .search-box::placeholder {{
            color: var(--text-muted);
        }}

        .filter-select {{
            padding: 10px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 4px;
            color: var(--text);
            font-size: 14px;
        }}

        .theme-toggle, .export-btn {{
            padding: 10px 20px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 4px;
            color: var(--text);
            cursor: pointer;
            font-size: 14px;
        }}

        .theme-toggle:hover, .export-btn:hover {{
            border-color: var(--accent);
        }}

        .stats {{
            display: flex;
            gap: 20px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}

        .stat-card {{
            background-color: var(--bg-card);
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid var(--accent);
            flex: 1;
            min-width: 180px;
        }}

        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: var(--accent);
        }}

        .stat-label {{
            font-size: 14px;
            color: var(--text-muted);
        }}

        .warning {{
            background-color: var(--warning-bg);
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
            color: var(--text);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: var(--bg-card);
        }}

        th {{
            background-color: var(--bg-header);
            color: var(--accent);
            padding: 12px;
            text-align: left;
            cursor: pointer;
            user-select: none;
            position: relative;
        }}

        th:hover {{
            background-color: var(--border);
        }}

        th::after {{
            content: ' ↕';
            font-size: 12px;
            opacity: 0.3;
        }}

        th[data-dir="asc"]::after {{
            content: ' ↑';
            opacity: 1;
            color: var(--accent);
        }}

        th[data-dir="desc"]::after {{
            content: ' ↓';
            opacity: 1;
            color: var(--accent);
        }}

        td {{
            padding: 10px;
            border-bottom: 1px solid var(--border);
        }}

        tr:hover {{
            background-color: var(--border);
        }}

        tr.collapsed .group-content {{
            display: none;
        }}

        .expand-btn {{
            cursor: pointer;
            user-select: none;
            color: var(--accent);
        }}

        .copy-btn {{
            padding: 4px 8px;
            background: var(--bg-header);
            border: 1px solid var(--border);
            border-radius: 3px;
            color: var(--text-muted);
            cursor: pointer;
            font-size: 12px;
        }}

        .copy-btn:hover {{
            color: var(--text);
            border-color: var(--accent);
        }}

        .copy-btn.copied {{
            color: var(--accent-hover);
        }}

        a {{
            color: var(--accent);
            text-decoration: none;
        }}

        a:hover {{
            text-decoration: underline;
            color: var(--accent-hover);
        }}

        ul {{
            margin: 5px 0;
            padding-left: 20px;
        }}

        footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid var(--border);
            color: var(--text-muted);
            text-align: center;
        }}

        .no-results {{
            text-align: center;
            padding: 20px;
            color: var(--text-muted);
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Reporte de Archivos Duplicados</h1>

        <div class="toolbar">
            <input
                type="text"
                id="search"
                class="search-box"
                placeholder="🔍 Buscar por nombre o ruta..."
            />
            <select id="ext-filter" class="filter-select">
                <option value="">📁 Todas las extensiones</option>
                {_generar_opciones_extensiones(archivos_data)}
            </select>
            <button id="theme-toggle" class="theme-toggle">
                🌙 Cambiar tema
            </button>
            <button id="export-csv" class="export-btn">
                📊 Exportar CSV
            </button>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{total_archivos}</div>
                <div class="stat-label">Archivos Escaneados</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_carpetas}</div>
                <div class="stat-label">Carpetas Escaneadas</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(archivos_duplicados)}</div>
                <div class="stat-label">Grupos de Duplicados</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_espacio_duplicado:,}</div>
                <div class="stat-label">Espacio Recuperable (bytes)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{fecha_generacion}</div>
                <div class="stat-label">Generado</div>
            </div>
        </div>

        <div class="warning">
            <strong>⚠️ Este reporte es solo informativo.</strong>
            El usuario debe decidir manualmente qué eliminar.
            Cada resultado tiene un botón "📂 Abrir ubicación" para abrir la carpeta directamente.
        </div>

        <h2>Archivos Duplicados</h2>
        <table id="files-table">
            <thead>
                <tr>
                    <th data-col="0">Grupo</th>
                    <th data-col="1">Tamaño</th>
                    <th data-col="2">Copias</th>
                    <th data-col="3">Espacio Recuperable</th>
                    <th data-col="4">Rutas</th>
                </tr>
            </thead>
            <tbody>
                {_generar_filas_archivos(archivos_data)}
            </tbody>
        </table>

        <h2>Carpetas Duplicadas</h2>
        <table id="folders-table">
            <thead>
                <tr>
                    <th data-col="0">Grupo</th>
                    <th data-col="1">Nombre</th>
                    <th data-col="2">Copias</th>
                    <th data-col="3">Rutas</th>
                </tr>
            </thead>
            <tbody>
                {_generar_filas_carpetas(carpetas_data)}
            </tbody>
        </table>

        <footer>
            Generado por Detector de Duplicados | {fecha_generacion}
        </footer>
    </div>

    <script>
        (function() {{
            // === THEME TOGGLE ===
            const themeBtn = document.getElementById('theme-toggle');
            let currentTheme = 'dark';

            themeBtn.addEventListener('click', function() {{
                if (currentTheme === 'dark') {{
                    document.documentElement.setAttribute('data-theme', 'light');
                    themeBtn.textContent = '🌞 Cambiar tema';
                    currentTheme = 'light';
                }} else {{
                    document.documentElement.removeAttribute('data-theme');
                    themeBtn.textContent = '🌙 Cambiar tema';
                    currentTheme = 'dark';
                }}
            }});

            // === SEARCH ===
            const searchInput = document.getElementById('search');
            const tables = [
                document.getElementById('files-table'),
                document.getElementById('folders-table')
            ];

            searchInput.addEventListener('input', function() {{
                const query = this.value.toLowerCase();
                let visibleCount = 0;

                tables.forEach(table => {{
                    const rows = table.querySelectorAll('tbody tr');
                    rows.forEach(row => {{
                        const text = row.textContent.toLowerCase();
                        const match = text.includes(query);
                        row.style.display = match ? '' : 'none';
                        if (match) visibleCount++;
                    }});
                }});

                // Mostrar mensaje si no hay resultados
                if (visibleCount === 0) {{
                    tables.forEach(table => {{
                        const tbody = table.querySelector('tbody');
                        const msg = document.createElement('tr');
                        msg.className = 'no-results';
                        msg.innerHTML = '<td colspan="5">No se encontraron coincidencias</td>';
                        tbody.appendChild(msg);
                    }});
                }}
            }});

            // === EXTENSION FILTER ===
            const extFilter = document.getElementById('ext-filter');
            extFilter.addEventListener('change', function() {{
                const ext = this.value;
                let visibleCount = 0;

                if (ext === '') {{
                    tables.forEach(table => {{
                        const rows = table.querySelectorAll('tbody tr');
                        rows.forEach(row => row.style.display = '');
                    }});
                    return;
                }}

                tables.forEach(table => {{
                    const rows = table.querySelectorAll('tbody tr');
                    rows.forEach(row => {{
                        const text = row.textContent.toLowerCase();
                        const hasExt = text.includes(ext);
                        row.style.display = hasExt ? '' : 'none';
                        if (hasExt) visibleCount++;
                    }});
                }});

                if (visibleCount === 0) {{
                    tables.forEach(table => {{
                        const tbody = table.querySelector('tbody');
                        const msg = document.createElement('tr');
                        msg.className = 'no-results';
                        msg.innerHTML = '<td colspan="5">No se encontraron archivos con extensión ' + ext + '</td>'; // noqa: E501
                        tbody.appendChild(msg);
                    }});
                }}
            }});

            // === EXPORT CSV ===
            document.getElementById('export-csv').addEventListener('click', function() {{
                const csvData = [];
                const headers = ['Grupo', 'Tamaño', 'Copias', 'Espacio Recuperable', 'Rutas'];
                csvData.push(headers);

                tables.forEach(table => {{
                    const rows = table.querySelectorAll('tbody tr');
                    rows.forEach(row => {{
                        const cells = Array.from(row.children);
                        const rowData = cells.map(cell => cell.textContent.trim());
                        if (rowData.length > 1) {{
                            csvData.push(rowData);
                        }}
                    }});
                }});

                const csvContent = csvData.map(row => row.join(',')).join('\\n');
                const blob = new Blob([csvContent], {{ type: 'text/csv' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'detector_duplicados.csv';
                a.click();
                URL.revokeObjectURL(url);
            }});

            // === SORTING ===
            tables.forEach(table => {{
                const headers = table.querySelectorAll('th');
                headers.forEach((header, index) => {{
                    header.addEventListener('click', function() {{
                        const dir = header.getAttribute('data-dir') || 'asc';
                        const newDir = dir === 'asc' ? 'desc' : 'asc';

                        // Reset all headers
                        headers.forEach(h => h.removeAttribute('data-dir'));
                        header.setAttribute('data-dir', newDir);

                        // Sort rows
                        const tbody = table.querySelector('tbody');
                        const rows = Array.from(tbody.querySelectorAll('tr'));

                        rows.sort((a, b) => {{
                            const aVal = a.children[index].textContent.replace(/,/g, '');
                            const bVal = b.children[index].textContent.replace(/,/g, '');

                            const aNum = parseFloat(aVal);
                            const bNum = parseFloat(bVal);

                            if (!isNaN(aNum) && !isNaN(bNum)) {{
                                return newDir === 'asc' ? aNum - bNum : bNum - bNum;
                            }}
                            return newDir === 'asc'
                                ? aVal.localeCompare(bVal)
                                : bVal.localeCompare(aVal);
                        }});

                        rows.forEach(row => tbody.appendChild(row));
                    }});
                }});
            }});

            // === COPY TO CLIPBOARD ===
            document.addEventListener('click', function(e) {{
                if (e.target.classList.contains('copy-btn')) {{
                    const path = e.target.getAttribute('data-path');
                    const btn = e.target;

                    if (navigator.clipboard && navigator.clipboard.writeText) {{
                        navigator.clipboard.writeText(path).then(() => {{
                            btn.textContent = '✓ Copiado';
                            btn.classList.add('copied');
                            setTimeout(() => {{
                                btn.textContent = '📋 Copiar';
                                btn.classList.remove('copied');
                            }}, 2000);
                        }}).catch(() => {{
                            btn.textContent = '✗ Error';
                            setTimeout(() => {{
                                btn.textContent = '📋 Copiar';
                            }}, 2000);
                        }});
                    }} else {{
                        const textarea = document.createElement('textarea');
                        textarea.value = path;
                        document.body.appendChild(textarea);
                        textarea.select();
                        document.execCommand('copy');
                        document.body.removeChild(textarea);

                        btn.textContent = '✓ Copiado';
                        btn.classList.add('copied');
                        setTimeout(() => {{
                            btn.textContent = '📋 Copiar';
                            btn.classList.remove('copied');
                        }}, 2000);
                    }}
                }}
            }});

            // === EXPAND/COLLAPSE ===
            document.addEventListener('click', function(e) {{
                if (e.target.classList.contains('expand-btn') ||
                    e.target.closest('.expand-btn')) {{
                    const row = e.target.closest('tr');
                    if (row) {{
                        row.classList.toggle('collapsed');
                        const icon = e.target.closest('.expand-btn').textContent;
                        e.target.closest('.expand-btn').textContent =
                            row.classList.contains('collapsed') ? '▶' : '▼';
                    }}
                }}
            }});
        }})();
    </script>
</body>
</html>"""

    # Escribir el archivo
    report_path = Path(nombre_reporte)
    report_path.write_text(html_content, encoding="utf-8")

    # Abrir automáticamente en el navegador si se solicita
    if abrir_navegador:
        try:
            url = f"file://{report_path.resolve()}"
            webbrowser.open(url)
        except Exception as e:
            print(f"[warning] No se pudo abrir el navegador: {e}")

    return str(report_path)


def _generar_filas_archivos(archivos_data):
    """Genera filas HTML para la tabla de archivos duplicados."""
    html = ""
    for grupo_id, info in archivos_data.items():
        rutas = info["rutas"]
        tamanio = info["tamanio"]
        espacio = info["espacio_potencial"]

        rutas_html = ""
        for ruta in rutas:
            parent_dir = os.path.dirname(ruta)
            folder_url = _archivo_a_ruta_file(parent_dir)
            rutas_html += f"""
                    <li>
                        <button class="copy-btn" data-path="{ruta}" style="margin-right: 4px; font-size: 11px;">
                            📋 Copiar
                        </button>
                        <a href="{folder_url}" title="Abrir carpeta: {parent_dir}" style="font-size: 11px;">
                            📂 Abrir ubicación
                        </a>
                    </li>"""

        html += f"""
            <tr>
                <td>{grupo_id}</td>
                <td>{tamanio:,} bytes</td>
                <td>{len(rutas)} copias</td>
                <td>{espacio:,} bytes</td>
                <td>
                    <ul style="list-style: none; padding-left: 10px;">
                        {rutas_html}
                    </ul>
                </td>
            </tr>
            """
    return html


def _generar_filas_carpetas(carpetas_data):
    """Genera filas HTML para la tabla de carpetas duplicadas."""
    html = ""
    for grupo_id, info in carpetas_data.items():
        nombre = info["nombre"]
        rutas = info["rutas"]
        copias = info["copias"]

        rutas_html = ""
        for ruta in rutas:
            parent_dir = os.path.dirname(ruta)
            folder_url = _archivo_a_ruta_file(parent_dir)
            rutas_html += f"""
                    <li>
                        <button class="copy-btn" data-path="{ruta}" style="margin-right: 4px; font-size: 11px;">
                            📋 Copiar
                        </button>
                        <a href="{folder_url}" title="Abrir carpeta: {parent_dir}" style="font-size: 11px;">
                            📂 Abrir ubicación
                        </a>
                    </li>"""

        html += f"""
            <tr>
                <td>{grupo_id}</td>
                <td>{nombre}</td>
                <td>{copias} copias</td>
                <td>
                    <ul style="list-style: none; padding-left: 10px;">
                        {rutas_html}
                    </ul>
                </td>
            </tr>
            """
    return html


def _generar_opciones_extensiones(archivos_data):
    """Genera opciones de filtro por extensión para el HTML."""
    extensiones = set()
    for info in archivos_data.values():
        for ruta in info["rutas"]:
            ext = Path(ruta).suffix
            if ext:
                extensiones.add(ext)

    opciones = ""
    for ext in sorted(extensiones):
        opciones += f'<option value="{ext}">{ext}</option>'
    return opciones


def generar_reporte_desde_db(
    escaneo_id: int,
    nombre_reporte: str = "detector_report_db.html",
    abrir_navegador: bool = True,
    db_path: str | None = None,
) -> str:
    """Genera un reporte HTML cargando datos desde la base de datos SQLite.

    FASE 2.0: Soporta apertura automática del navegador.

    Args:
        escaneo_id: ID del escaneo en la base de datos.
        nombre_reporte: Nombre del archivo HTML a generar.
        abrir_navegador: Si True, abre el HTML en el navegador automáticamente.
        db_path: Ruta opcional a la DB. Si None, usa la ruta por defecto.

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

        if db_path:
            conn = create_connection(db_path)
        else:
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

    # Generar reporte con las nuevas funcionalidades
    reporte = generar_reporte_html(
        archivos_duplicados,
        carpetas_duplicadas,
        total_archivos,
        total_carpetas,
        nombre_reporte,
        abrir_navegador=abrir_navegador,
    )

    return reporte
