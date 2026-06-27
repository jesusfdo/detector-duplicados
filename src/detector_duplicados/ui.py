"""Capa de interfaz terminal con Rich.

Maneja toda la presentación al usuario: paneles, tablas, arboles,
menus interactivos y mensajes de estado.
Fase 3: Tablas interactivas, filtros, seleccion, acciones.
"""

from rich import box
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from .theme import console


def mostrar_bienvenida(usuario: str = "Usuario") -> None:
    """Muestra el panel de bienvenida con estilo Rich."""
    title = Text("Detector de Duplicados v1.0.0", style="highlight")
    subtitle = Text(f"Escáner local seguro | Autor: {usuario}", style="info")
    console.print(
        Panel(
            console.render_str("[success]Escáner de archivos duplicados[/]"),
            title=title,
            subtitle=subtitle,
            border_style="highlight",
            box=box.ROUNDED,
        )
    )


def mostrar_panel_ayuda() -> None:
    """Muestra un panel de ayuda con instrucciones para usuarios no tecnicos.

    Este panel se muestra automaticamente al iniciar la app para guiar
    al usuario sobre como usar la herramienta sin necesidad de conocer
    comandos de terminal.
    """
    help_lines = [
        ("¿Como usar esta herramienta?", "bold"),
        ("", ""),
        ("  1. Elige una de las opciones del menu principal", "info"),
        ("", ""),
        (
            "  2. Si eliges 'Escanear carpetas', escribe la ruta de la carpeta "
            "donde tienes tus archivos",
            "warning",
        ),
        ("", ""),
        ("     Ejemplo: /home/tu-nombre/Documents", "path"),
        ("", ""),
        (
            "  3. La herramienta encontrara archivos duplicados y te mostrara "
            "los resultados en tablas",
            "info",
        ),
        ("", ""),
        (
            "  4. Podras ver el detalle de cada escaneo, comparar escaneos anteriores "
            "o exportar los resultados a un archivo de texto",
            "info",
        ),
        ("", ""),
        ("  5. Tambien podras eliminar duplicados de forma segura con el cleanup", "success"),
        ("", ""),
        (
            "  6. Si no estas seguro, siempre puedes ver las estadisticas de la base de datos",
            "info",
        ),
        ("", ""),
        (
            "  7. Para salir del programa, selecciona la opcion 'Salir' en cualquier momento",
            "error",
        ),
    ]

    help_text = Text()
    for line, style in help_lines:
        if line == "":
            help_text.append("\n", style=style)
        else:
            help_text.append(line + "\n", style=style)

    console.print(
        Panel(
            help_text,
            title="[bold yellow]⚡ Ayuda - Como usar el programa[/]",
            border_style="yellow",
            box=box.ROUNDED,
            width=80,
        )
    )


def preguntar_ruta() -> str:
    """Pregunta la ruta al usuario con prompt Rich."""
    return Prompt.ask("¿Ruta(s) a analizar? (separa multiples con coma)").strip()


def mostrar_progreso(barra, task_id, total, actual=None):
    """Actualiza la barra de progreso Rich."""
    if barra:
        barra.update(task_id, completed=actual or actual, advance=1)


def mostrar_resultados_tabla(
    archivos_duplicados: dict,
    carpetas_duplicadas: dict,
    total_archivos: int,
    total_carpetas: int,
    rutas_no_escaneadas: list | None = None,
) -> None:
    """Muestra los resultados en tablas Rich formateadas (Fase 3)."""
    console.print("\n[bold highlight]=== Resultados del Análisis ===[/]")

    # Panel de resumen
    resumen = Text()
    resumen.append("Total archivos escaneados: ", style="info")
    resumen.append(f"{total_archivos}\n", style="success")
    resumen.append("Total carpetas: ", style="info")
    resumen.append(f"{total_carpetas}\n", style="success")
    if total_archivos > 0:
        resumen.append("Tamaño total: ", style="info")
        # Soportar ambos formatos: valores dict o list (preciso)
        total_size = 0
        for v in archivos_duplicados.values():
            if isinstance(v, list):
                # Formato preciso: lista de rutas, sin tamanio
                continue
            elif isinstance(v, dict):
                total_size += v.get("tamanio", 0)
        resumen.append(f"{total_size:,} bytes\n", style="success")
    console.print(Panel(resumen, title="Resumen", border_style="info", box=box.ROUNDED))

    # Tabla de duplicados de archivos
    if archivos_duplicados:
        console.print("\n[bold duplicate]📁 Duplicados de archivos:[/]\n")
        table = Table(show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Grupo", style="highlight")
        table.add_column("Tamaño", justify="right")
        table.add_column("Hash (SHA256)", style="hash", max_width=30)
        table.add_column("Ruta", style="path", max_width=40)

        grupo_num = 1
        for key, info in archivos_duplicados.items():
            # Soportar ambos formatos: {key: {"rutas": [...], "tamanio": ...}} (rapido)
            # y {hash: [ruta1, ruta2, ...]} (preciso)
            if isinstance(info, list):
                rutas = info
                tamanio = 0
                hash_val = key[:16] + "..."
            else:
                rutas = info.get("rutas", [])
                tamanio = info.get("tamanio", 0)
                hash_val = info.get("hash", key[:16] + "...")

            for ruta in rutas:
                table.add_row(
                    f"[highlight]{grupo_num}[/]",
                    f"[success]{tamanio:,} bytes[/]",
                    f"[hash]{hash_val}[/]",
                    f"[path]{ruta}[/]",
                )
            grupo_num += 1
        console.print(table)

    # Tabla de carpetas duplicadas
    if carpetas_duplicadas:
        console.print("\n[bold duplicate]📂 Carpetas duplicadas:[/]\n")
        table = Table(show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Grupo", style="highlight")
        table.add_column("Nombre Carpeta", style="info")
        table.add_column("Ruta", style="path", max_width=50)

        grupo_num = 1
        for nombre, rutas in carpetas_duplicadas.items():
            for ruta in rutas:
                table.add_row(
                    f"[highlight]{grupo_num}[/]",
                    f"[info]{nombre}[/]",
                    f"[path]{ruta}[/]",
                )
            grupo_num += 1
        console.print(table)

    # Mostrar rutas omitidas si existen
    if rutas_no_escaneadas:
        console.print(f"\n[warning]⚠ Rutas omitidas ({len(rutas_no_escaneadas)}):[/]")
        for r in rutas_no_escaneadas:
            console.print(f"  [warning]- {r}[/]")

    console.print("\n[success]--- Análisis terminado ---[/]\n")


def mostrar_arbol_resultados(archivos_duplicados: dict) -> None:
    """Muestra los resultados en formato de arbol Rich."""
    console.print("\n[bold highlight]=== Estructura de Duplicados ===[/]\n")

    tree = Tree("[bold highlight]Duplicados Encontrados[/]")

    for nombre, info in archivos_duplicados.items():
        group_node = tree.add(f"[duplicate]Grupo: {nombre}[/]")
        if isinstance(info, list):
            # Formato preciso: lista de rutas
            tamanio = 0
            for ruta in info:
                group_node.add(f"[path]{ruta}[/] ({tamanio} bytes)")
        else:
            # Formato rapido: dict con "rutas", "tamanio"
            tamanio = info.get("tamanio", 0)
            for ruta in info.get("rutas", []):
                group_node.add(f"[path]{ruta}[/] ({tamanio} bytes)")

    console.print(tree)


def menu_interactivo(opciones: list) -> int:
    """Muestra un menu interactivo y devuelve la seleccion del usuario.

    Maneja EOF (Ctrl+D) retornando 0 (salir).
    """
    console.print("\n[bold highlight]Seleccione una opcion:[/]")
    for i, opcion in enumerate(opciones, 1):
        console.print(f"  [info]{i}[/]. {opcion}")
    console.print("  [info]0[/]. Salir")

    while True:
        try:
            seleccion = int(input("[bold info]Opcion:[/] "))
            if 0 <= seleccion < len(opciones) + 1:
                return seleccion
            console.print("[warning]Por favor seleccione un numero valido.[/]")
        except ValueError:
            console.print("[warning]Entrada invalida. Ingrese un numero.[/]")
        except EOFError:
            # Ctrl+D / fin de entrada → salir silenciosamente
            console.print("[info]Entrada finalizada (EOF). Saliendo...[/]")
            return 0


def mostrar_estado_mensaje(mensaje: str, tipo: str = "info"):
    """Muestra un mensaje de estado con icono y color apropiado."""
    iconos = {
        "success": "[success]✓[/]",
        "error": "[error]✗[/]",
        "warning": "[warning]⚠[/]",
        "info": "[info]ℹ[/]",
    }
    icono = iconos.get(tipo, "[info]ℹ[/]")
    console.print(f"{icono} {mensaje}")


def confirmar_accion(mensaje: str) -> bool:
    """Pide confirmacion al usuario para una accion critica."""
    return Confirm.ask(f"[warning]{mensaje}[/]", default=False)


def mostrar_escaneo_en_curso(barra, task_id, total, actual):
    """Prepara y muestra la informacion de escaneo en tiempo real (Fase 3)."""
    if barra:
        barra.update(task_id, advance=1)
    if actual % 100 == 0:  # Solo actualizar consola cada 100 archivos
        console.print(f"[info]Escaneando... {actual}/{total} archivos[/]")


def mostrar_comparacion_escaneos(
    esc1_info: dict,
    esc2_info: dict,
    comunes: list,
    solo1: list,
    solo2: list,
) -> None:
    """Muestra la comparacion entre dos escaneos (Fase 3)."""
    console.print("\n[bold highlight]=== Comparacion de Escaneos ===[/]\n")

    # Resumen
    resumen = Text()
    resumen.append("Escaneo 1: ", style="info")
    resumen.append(f"{len(esc1_info.get('archivos', []))} archivos\n", style="success")
    resumen.append("Escaneo 2: ", style="info")
    resumen.append(f"{len(esc2_info.get('archivos', []))} archivos\n", style="success")
    resumen.append("Comunes: ", style="highlight")
    resumen.append(f"{len(comunes)}\n", style="warning")
    console.print(Panel(resumen, border_style="info", box=box.ROUNDED))

    # Tabla de comunes
    if comunes:
        console.print("\n[bold duplicate]🔗 Archivos comunes:[/]")
        table = Table(show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Archivo", style="info")
        table.add_column("Ruta 1", style="path", max_width=40)
        table.add_column("Ruta 2", style="path", max_width=40)
        table.add_column("Duplicado", style="duplicate")

        for archivo in comunes:
            table.add_row(
                f"[info]{archivo.get('nombre', 'N/A')}[/]",
                f"[path]{archivo.get('ruta1', 'N/A')}[/]",
                f"[path]{archivo.get('ruta2', 'N/A')}[/]",
                "[duplicate]Si[/]",
            )
        console.print(table)

    # Archivos solo en escaneo 1
    if solo1:
        console.print(f"\n[bold info]Solo en Escaneo 1 ({len(solo1)}):[/]")
        for a in solo1:
            console.print(f"  [path]{a.get('ruta', 'N/A')}[/]")

    # Archivos solo en escaneo 2
    if solo2:
        console.print(f"\n[bold info]Solo en Escaneo 2 ({len(solo2)}):[/]")
        for a in solo2:
            console.print(f"  [path]{a.get('ruta', 'N/A')}[/]")

    console.print("\n[success]--- Comparacion terminada ---[/]\n")


def mostrar_panel_metricas(
    total_archivos: int, total_duplicados: int, espacio_recuperable: int
) -> None:
    """Muestra panel de métricas (Fase 3).

    Args:
        total_archivos: Total de archivos escaneados.
        total_duplicados: Total de duplicados encontrados.
        espacio_recuperable: Espacio en bytes que se puede recuperar.
    """
    console.print("\n[bold highlight]=== Métricas ===[/]")
    console.print(f"  [info]Archivos escaneados:[/] {total_archivos:,}")
    console.print(f"  [duplicate]Duplicados:[/] {total_duplicados}")
    console.print(f"  [success]Espacio recuperable:[/] {espacio_recuperable:,} bytes")
    console.print()


def mostrar_menu_principal() -> str:
    """Muestra menu principal del programa (Fase 3).

    Returns:
        str: Opcion seleccionada por el usuario.
    """
    console.print("\n[bold highlight]=== Detector de Duplicados (Modo Interactivo) ===[/]\n")

    opciones = [
        "1. Escanear nuevas carpetas",
        "2. Ver escaneos guardados",
        "3. Ver detalle de un escaneo",
        "4. Comparar dos escaneos",
        "5. Ver estadisticas de la base de datos",
        "6. Exportar resultados",
        "7. Eliminar un escaneo",
        "8. Salir",
    ]

    for opcion in opciones:
        console.print(f"  {opcion}")

    opcion = Prompt.ask("\nSelecciona una opcion", choices=["1", "2", "3", "4", "5", "6", "7", "8"])
    return opcion
