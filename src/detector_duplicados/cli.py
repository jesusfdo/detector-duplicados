"""Entry point CLI para `detector` comando.

Se registra como script en pyproject.toml.

Subcomandos:
  detector [ruta1,ruta2]  - Escanear rutas (modo interactivo)
  detector --scan <ruta>  - Escanear ruta especifica
  detector --list         - Lista escaneos guardados
  detector --stats        - Estadisticas de la base de datos
  detector --detail <id>  - Detalle de un escaneo
  detector --compare <id1> <id2> - Comparar dos escaneos
  detector --delete <id>  - Eliminar un escaneo
  detector --export <ruta> - Exportar resultados de un escaneo
"""

import argparse
import sys

from rich import box
from rich.prompt import IntPrompt, Prompt

from detector_duplicados.config import PERFILES_PREDEFINIDOS
from detector_duplicados.main import (
    comparar_escaneos,
    eliminar_escaneo_cmd,
    listar_escaneos,
    mostrar_estadisticas,
    obtener_escaneo_detalle,
    run,
)
from detector_duplicados.theme import console


def build_parser() -> argparse.ArgumentParser:
    """Construye el parser de argumentos CLI."""
    parser = argparse.ArgumentParser(
        prog="detector",
        description="Escáner local de archivos duplicados con terminal Rich",
    )

    # Posicional: ruta(s) a escanear
    parser.add_argument(
        "rutas",
        nargs="?",
        default=None,
        help="Ruta(s) a escanear. Multiples rutas separadas por coma.",
    )

    # Opciones de accion
    parser.add_argument(
        "--scan",
        "-s",
        dest="scan",
        help="Escanear una ruta especifica (alternativa a ruta posicional).",
    )

    parser.add_argument(
        "--list",
        "-l",
        dest="list",
        action="store_true",
        help="Listar todos los escaneos guardados.",
    )

    parser.add_argument(
        "--stats",
        dest="stats",
        action="store_true",
        help="Mostrar estadisticas de la base de datos.",
    )

    parser.add_argument(
        "--detail",
        "-d",
        dest="detail",
        type=int,
        metavar="ID",
        help="Mostrar detalles de un escaneo por su ID.",
    )

    parser.add_argument(
        "--compare",
        "-c",
        dest="compare",
        nargs=2,
        type=int,
        metavar="ID",
        help="Comparar dos escaneos por sus IDs.",
    )

    parser.add_argument(
        "--delete",
        dest="delete",
        type=int,
        metavar="ID",
        help="Eliminar un escaneo por su ID.",
    )

    parser.add_argument(
        "--export",
        "-e",
        dest="export",
        metavar="ID",
        type=int,
        help="Exportar resultados de un escaneo a TXT.",
    )

    parser.add_argument(
        "--cleanup",
        dest="cleanup",
        nargs="?",
        const=1,
        default=None,
        metavar="ID",
        help="Ejecutar cleanup con política de conservación (Fase 4).",
    )

    parser.add_argument(
        "--profile",
        dest="profile",
        choices=list(PERFILES_PREDEFINIDOS.keys()),
        default="default",
        help="Perfil de configuracion para cleanup (default, agresivo, conservador).",
    )

    parser.add_argument(
        "--politica",
        dest="politica",
        choices=[
            "keep_one_copy",
            "keep_newest",
            "keep_oldest",
            "keep_in_path",
            "aggressive",
            "conservative",
        ],
        default="keep_one_copy",
        help="Politica de conservacion para cleanup.",
    )

    parser.add_argument(
        "--modo-cleanup",
        dest="modo_cleanup",
        choices=["papelera", "renombrar"],
        default="papelera",
        help="Modo de cleanup (papelera o renombrar).",
    )

    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Simular cleanup sin ejecutar acciones (Fase 4).",
    )

    parser.add_argument(
        "--rollback",
        dest="rollback",
        nargs="?",
        type=int,
        const=1,
        default=None,
        metavar="ID",
        help="Deshacer una accion de cleanup registrada (Fase 4).",
    )

    parser.add_argument(
        "--list-rollback",
        dest="list_rollback",
        action="store_true",
        help="Listar acciones que pueden ser deshechas (Fase 4).",
    )

    parser.add_argument(
        "--watch",
        dest="watch",
        nargs="+",
        metavar="RUTA",
        help="Iniciar modo Watchdog para monitorear rutas en tiempo real.",
    )

    parser.add_argument(
        "--report",
        dest="report",
        nargs=2,
        metavar=("ID", "ARCHIVO"),
        help="Generar reporte HTML autocontenido. Usa: detector --report <ID> <archivo_salida>",
    )

    parser.add_argument(
        "--modo",
        "-m",
        dest="modo",
        choices=["preciso", "rapido"],
        default="preciso",
        help="Modo de escaneo: 'preciso' (hash) o 'rapido' (solo nombre).",
    )

    parser.add_argument(
        "--extensiones",
        "-x",
        dest="extensiones",
        help="Filtro de extensiones separadas por coma (ej: '.mp4,.mkv').",
    )

    parser.add_argument(
        "--no-save",
        dest="no_save",
        action="store_true",
        help="No guardar resultados en la base de datos.",
    )

    return parser


def main_interactivo() -> None:
    """Modo interactivo con menu principal."""
    # Mostrar ayuda al inicio para usuarios no tecnicos
    from detector_duplicados.ui import mostrar_panel_ayuda

    mostrar_panel_ayuda()

    opciones = [
        "Escanear nuevas carpetas",
        "Ver escaneos guardados",
        "Ver detalle de un escaneo",
        "Comparar dos escaneos",
        "Ver estadisticas de la base de datos",
        "Exportar resultados",
        "Eliminar un escaneo",
        "Salir",
    ]

    while True:
        # Mostrar menu con numeracion clara
        console.print("\n[bold highlight]=== Menu Principal ===[/]")
        for i, opcion in enumerate(opciones, 1):
            console.print(f"  [info]{i}[/]. {opcion}")
        console.print()

        # Pedir seleccion con validacion
        seleccion_str = Prompt.ask(
            "[bold info]Seleccione una opcion[/] (1-" + str(len(opciones)) + ")",
            choices=[str(i) for i in range(1, len(opciones) + 1)],
            console=console,
        )
        seleccion = int(seleccion_str)

        if seleccion == 1:  # Escanear
            ruta = Prompt.ask(
                "\n[info]Ingrese la ruta a escanear[/] (separar multiples con coma)",
                console=console,
            )
            if ruta:
                console.print("[info]Iniciando escaneo...[/]")
                run(rutas=[ruta])
            else:
                console.print("[warning]Ruta vacia, cancelado.[/]")

        elif seleccion == 2:  # Ver escaneos
            listar_escaneos()

        elif seleccion == 3:  # Ver detalle
            esc_id = int(
                Prompt.ask(
                    "\n[info]Ingrese el ID del escaneo[/]",
                    console=console,
                )
            )
            obtener_escaneo_detalle(esc_id)

        elif seleccion == 4:  # Comparar
            id1 = int(
                Prompt.ask("\n[info]Ingrese el ID del primer escaneo[/]", console=console)
            )
            id2 = int(
                Prompt.ask("[info]Ingrese el ID del segundo escaneo[/]", console=console)
            )
            comparar_escaneos(id1, id2)

        elif seleccion == 5:  # Estadisticas
            mostrar_estadisticas()

        elif seleccion == 6:  # Exportar
            esc_id = int(
                Prompt.ask(
                    "\n[info]Ingrese el ID del escaneo a exportar[/]", console=console
                )
            )
            detalle = obtener_escaneo_detalle(esc_id)
            if detalle:
                from detector_duplicados.exporter import exportar_resultados

                exportar_resultados(detalle, esc_id)

        elif seleccion == 7:  # Eliminar
            esc_id = int(
                Prompt.ask(
                    "\n[info]Ingrese el ID del escaneo a eliminar[/]", console=console
                )
            )
            if eliminar_escaneo_cmd(esc_id):
                console.print("[success]Escaneo eliminado exitosamente.[/]")

        elif seleccion == 8:  # Salir
            console.print("[highlight]Saliendo del detector.[/]")
            break


def main() -> None:
    """Entry point CLI."""
    parser = build_parser()
    args = parser.parse_args()

    # Si no hay argumentos, entrar en modo interactivo
    if not sys.argv[1:]:
        main_interactivo()
        return

    # Accion: list
    if args.list:
        listar_escaneos()
        return

    # Accion: stats
    if args.stats:
        mostrar_estadisticas()
        return

    # Accion: detail
    if args.detail is not None:
        obtener_escaneo_detalle(args.detail)
        return

    # Accion: compare
    if args.compare is not None:
        comparar_escaneos(args.compare[0], args.compare[1])
        return

    # Accion: delete
    if args.delete is not None:
        eliminar_escaneo_cmd(args.delete)
        return

    # Accion: export
    if args.export is not None:
        detalle = obtener_escaneo_detalle(args.export)
        if detalle:
            from detector_duplicados.exporter import exportar_resultados

            exportar_resultados(detalle, args.export)
        return

    # Fase 4: --cleanup con politica
    if args.cleanup is not None:
        esc_id = int(args.cleanup)
        detalle = obtener_escaneo_detalle(esc_id)
        if detalle:
            from detector_duplicados.cleaner import dry_run_cleanup, ejecutar_cleanup

            archivos_dup = detalle.get("confirmados", {})

            if args.dry_run:
                resultado = dry_run_cleanup(archivos_dup, args.politica, args.profile)
                console.print(
                    f"\n[bold highlight]=== Dry Run: Politica '{args.politica}' ===[/]\n"
                )
                console.print(f"  Total grupos: {resultado['total_duplicados']}")
                console.print(f"  Total archivos: {resultado['total_archivos']}")
                console.print(f"  Espacio total: {resultado['espacio_total']:,} bytes")
                console.print(f"  Espacio recuperable: {resultado['espacio_recuperable']:,} bytes")
                if resultado["acciones"]:
                    console.print("\n[bold]Acciones propuestas:[/]")
                    for acc in resultado["acciones"]:
                        if acc["accion"] != "ninguna":
                            console.print(
                                f"  [{acc['accion']}] Grupo #{acc['grupo_id']}: "
                                f"eliminar {len(acc['eliminar'])}/mantener {len(acc['mantener'])}"
                            )
            else:
                resultado = ejecutar_cleanup(
                    archivos_dup,
                    politica=args.politica,
                    perfil=args.profile,
                    modo=args.modo_cleanup,
                    escaneo_id=esc_id,
                    confirmar=True,
                )
                if resultado.get("error"):
                    console.print(f"[warning]Error: {resultado['error']}")
                else:
                    console.print(
                        f"[success]Cleanup completado: {resultado['exitosos']} exitosos, "
                        f"{resultado['fallos']} fallos, {resultado['espacio_recuperado']:,} bytes recuperados."  # noqa: E501
                    )
        else:
            console.print(f"[warning]No hay escaneo con ID #{esc_id} para cleanup.[/]")
        return

    # Fase 4: --rollback
    if args.rollback is not None:
        accion_id = int(args.rollback)
        from detector_duplicados.db import create_connection, deshacer_accion

        conn = create_connection()

        accion_id = args.rollback
        if deshacer_accion(conn, accion_id):
            console.print(f"[success]Accion #{accion_id} deshecha exitosamente.[/]")
        else:
            console.print(
                f"[error]No se pudo deshacer la accion #{accion_id} "
                "(posiblemente ya deshecha o tipo no reversible)."
            )
        return

    # Fase 4: --list-rollback
    if args.list_rollback:
        from detector_duplicados.db import create_connection, obtener_rollback_disponible

        conn = create_connection()

        acciones = obtener_rollback_disponible(conn, 5)
        if acciones:
            console.print("\n[bold highlight]=== Acciones reversibles (ultimas 5) ===[/]\n")
            from rich.table import Table

            table = Table(show_header=True, header_style="bold", box=box.ROUNDED)
            table.add_column("ID", justify="right", style="info")
            table.add_column("Fecha", style="date")
            table.add_column("Tipo", style="highlight")
            table.add_column("Archivo Origen", style="path")
            table.add_column("Archivo Destino", style="info")
            table.add_column("Usuario", style="user")

            for acc in acciones:
                table.add_row(
                    str(acc["id"]),
                    acc["fecha"][:19],
                    acc["tipo"],
                    acc["archivo_origen"],
                    acc.get("archivo_destino", "-") or "-",
                    acc.get("usuario", "?") or "?",
                )
            console.print(table)
            console.print("\n[info]Usa 'detector --rollback <ID>' para deshacer.[/]")
        else:
            console.print("[info]No hay acciones reversibles disponibles.[/]")
        return

    # Accion: watch (Fase 4)
    if args.watch:
        from detector_duplicados.watchdog import iniciar_watchdog

        console.print(f"[info]Iniciando Watchdog en {len(args.watch)} rutas...[/]")
        iniciar_watchdog(args.watch)
        return

    # Accion: report (Fase 4)
    if args.report:
        from detector_duplicados.html_report import generar_reporte_desde_db, generar_reporte_html

        esc_id = int(args.report[0]) if args.report[0].isdigit() else None
        output_file = args.report[1] if len(args.report) > 1 else "detector_report.html"
        if esc_id:
            detalle = obtener_escaneo_detalle(esc_id)
            if detalle:
                reporte = generar_reporte_desde_db(esc_id, output_file)
                if reporte:
                    console.print(f"[success]Reporte generado: {reporte}[/]")
                    return
        # Fallback: reporte vacio si no se paso ID valido
        reporte = generar_reporte_html({}, {}, 0, 0, output_file)
        console.print(f"[success]Reporte generado: {reporte}[/]")
        return

    # Escaneo normal
    rutas = args.scan if args.scan is not None else args.rutas
    extensiones = None
    if args.extensiones:
        extensiones = set(
            ext.strip() if ext.strip().startswith(".") else f".{ext.strip()}"
            for ext in args.extensiones.split(",")
        )

    result = run(
        rutas=[rutas] if isinstance(rutas, str) and rutas else (rutas or []),
        extensiones=extensiones,
        modo=args.modo,
        persistir=not args.no_save,
    )

    if result.get("escaneo_id"):
        console.print(f"\n[green]Escaneo guardado con ID #{result['escaneo_id']}[/]")
        console.print("Usa 'detector --list' para ver todos los escaneos guardados.")
        console.print(f"Usa 'detector --detail {result['escaneo_id']}' para ver detalles.")


if __name__ == "__main__":
    import sys

    main()
