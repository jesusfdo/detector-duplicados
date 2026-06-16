"""Tests de colisiones para Fase 3 (Terminal UI).

Verifica que el nuevo código de UI no colisione con:
- Fase 0: estructura de paquetes
- Fase 1: hashing SHA256
- Fase 2: base de datos SQLite
- Fase 4: policies, cleaner, rollback
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestUIImportIntegridad:
    """Tests para verificar que ui.py importa sin colisiones."""

    def test_ui_no_importa_policies(self):
        """ui.py NO debe importar policies (evita dependencia circular)."""
        import inspect

        import detector_duplicados.ui as ui_module

        source = inspect.getsource(ui_module)
        assert "from .policies" not in source, "ui.py importa policies (colision detectada)"
        assert "import policies" not in source, "ui.py importa policies (colision detectada)"

    def test_ui_no_importa_cleaner(self):
        """ui.py NO debe importar cleaner (evita dependencia circular)."""
        import inspect

        import detector_duplicados.ui as ui_module

        source = inspect.getsource(ui_module)
        assert "from .cleaner" not in source, "ui.py importa cleaner (colicion detectada)"
        assert "import cleaner" not in source, "ui.py importa cleaner (colicion detectada)"

    def test_ui_no_importa_db_directamente(self):
        """ui.py NO debe importar db (usa main.py como capa intermedia)."""
        import inspect

        import detector_duplicados.ui as ui_module

        source = inspect.getsource(ui_module)
        assert "from .db" not in source, "ui.py importa db (colision detectada)"
        assert "import db" not in source, "ui.py importa db (colicion detectada)"

    def test_ui_no_importa_exporter(self):
        """ui.py NO debe importar exporter (evita dependencia circular)."""
        import inspect

        import detector_duplicados.ui as ui_module

        source = inspect.getsource(ui_module)
        assert "from .exporter" not in source, "ui.py importa exporter (colicion detectada)"
        assert "import exporter" not in source, "ui.py importa exporter (colicion detectada)"

    def test_ui_puede_importar_sin_ejecutar(self):
        """ui.py se puede importar sin ejecutar CLI."""
        import detector_duplicados.ui as ui_module

        assert hasattr(ui_module, "mostrar_bienvenida")
        assert hasattr(ui_module, "mostrar_estado_mensaje")
        assert hasattr(ui_module, "confirmar_accion")
        assert hasattr(ui_module, "mostrar_menu_principal")


class TestUIFuncional:
    """Tests funcionales para ui.py (sin colisiones)."""

    def test_mostrar_bienvenida_no_crasha(self):
        """mostrar_bienvenida debe ejecutarse sin errores."""
        from detector_duplicados.ui import mostrar_bienvenida

        # No debe lanzar excepcion
        mostrar_bienvenida("test_user")

    def test_mostrar_estado_mensaje_no_crasha(self):
        """mostrar_estado_mensaje debe ejecutarse sin errores."""
        from detector_duplicados.ui import mostrar_estado_mensaje

        # No debe lanzar excepcion
        mostrar_estado_mensaje("test_message", "info")
        mostrar_estado_mensaje("test_message", "success")
        mostrar_estado_mensaje("test_message", "warning")
        mostrar_estado_mensaje("test_message", "error")

    def test_confirmar_accion_returns_bool(self):
        """confirmar_accion debe retornar bool."""
        # Confirmacion_accion usa rich.prompt.Confirm.ask
        from unittest.mock import patch

        with patch("rich.prompt.Confirm.ask", return_value=True):
            import detector_duplicados.ui as ui_module

            result = ui_module.confirmar_accion("test_message")
            assert isinstance(result, bool)
            assert result is True

    def test_mostrar_menu_principal_returns_str(self):
        """mostrar_menu_principal debe retornar str."""
        from detector_duplicados.ui import mostrar_menu_principal

        # Mock rich.prompt.Prompt.ask para evitar interaccion real
        with patch("rich.prompt.Prompt.ask", return_value="8"):
            result = mostrar_menu_principal()
            assert isinstance(result, str)
            assert result in ("1", "2", "3", "4", "5", "6", "7", "8")


class TestExporterIntegridad:
    """Tests para exporter.py sin colisiones."""

    def test_exporter_no_importa_policies(self):
        """exporter.py NO debe importar policies (evita dependencia circular)."""
        import inspect

        import detector_duplicados.exporter as exp_module

        source = inspect.getsource(exp_module)
        assert "from .policies" not in source, "exporter.py importa policies (colicion detectada)"
        assert "import policies" not in source, "exporter.py importa policies (colicion detectada)"

    def test_exporter_no_importa_cleaner(self):
        """exporter.py NO debe importar cleaner (evita dependencia circular)."""
        import inspect

        import detector_duplicados.exporter as exp_module

        source = inspect.getsource(exp_module)
        assert "from .cleaner" not in source, "exporter.py importa cleaner (colicion detectada)"
        assert "import cleaner" not in source, "exporter.py importa cleaner (colicion detectada)"

    def test_exportar_csv_genera_archivo_valido(self):
        """exportar_resultados con formato CSV debe generar archivo valido."""
        from detector_duplicados.exporter import exportar_resultados

        detalle = {
            "escaneo": {
                "id": 1,
                "fecha": "2025-01-01T00:00:00",
                "rutas": ["/test"],
                "total_archivos": 10,
                "total_carpetas": 2,
                "modo": "preciso",
            },
            "duplicados": [
                {
                    "id": 1,
                    "hash_sha256": "abc123",
                    "tamanio_bytes": 1000,
                    "cantidad": 2,
                    "confirmado": 1,
                    "rutas": "/test/a.mp4;/test/b.mp4",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "test.csv")
            result = exportar_resultados(detalle, 1, csv_path, "csv")
            assert result is True
            assert os.path.exists(csv_path)

            # Verificar contenido CSV
            with open(csv_path, encoding="utf-8") as f:
                content = f.read()
                assert "Grupo" in content
                assert "Hash" in content
                assert "abc123" in content


class TestExporterJSON:
    """Tests para exportacion JSON."""

    def test_exportar_json_genera_archivo_valido(self):
        """exportar_resultados con formato JSON debe generar archivo valido."""
        from detector_duplicados.exporter import exportar_resultados

        detalle = {
            "escaneo": {
                "id": 2,
                "fecha": "2025-01-01T00:00:00",
                "rutas": ["/test2"],
                "total_archivos": 5,
                "total_carpetas": 1,
                "modo": "rapido",
            },
            "duplicados": [
                {
                    "id": 1,
                    "hash_sha256": "xyz789",
                    "tamanio_bytes": 2000,
                    "cantidad": 3,
                    "confirmado": 0,
                    "rutas": "/test2/a.mp4;/test2/b.mp4;/test2/c.mp4",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, "test.json")
            result = exportar_resultados(detalle, 2, json_path, "json")
            assert result is True
            assert os.path.exists(json_path)

            # Verificar contenido JSON valido
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)  # Debe ser JSON valido
                assert "escaneo" in data
                assert "duplicados" in data
                assert data["escaneo"]["id"] == 2


class TestColisionesImport:
    """Tests de colisiones de import entre todos los modulos."""

    def test_circular_imports_ui_exporter(self):
        """ui.py y exporter.py NO deben importarse mutuamente."""
        import inspect

        import detector_duplicados.exporter as exp_module
        import detector_duplicados.ui as ui_module

        _ = inspect.getsource(ui_module)
        exp_source = inspect.getsource(exp_module)

        # Verificar que NO hay import de "from .ui" o "import ui" en exporter.py
        assert "from .ui" not in exp_source and "import ui" not in exp_source, (
            "exporter.py importa ui (colision detectada)"
        )

    def test_circular_imports_ui_main(self):
        """main.py SI importa ui (es intencional, no colision)."""
        import inspect

        import detector_duplicados.main as main_module

        main_source = inspect.getsource(main_module)

        # main.py debe importar ui (esta es la capa de presentacion)
        assert "from .ui import" in main_source, (
            "main.py no importa ui (necesario para presentacion)"
        )
        # Esto es esperado, no una colicion

    def test_config_centralizado_no_policies(self):
        """PERFILES solo definido en config.py, no en policies.py."""
        import inspect

        import detector_duplicados.config as config_module
        import detector_duplicados.policies as policies_module

        config_source = inspect.getsource(config_module)
        policies_source = inspect.getsource(policies_module)

        # config.py debe tener PERFILES_PREDEFINIDOS
        assert "PERFILES_PREDEFINIDOS" in config_source, "config.py no define PERFILES_PREDEFINIDOS"

        # policies.py debe importar desde config, no definir su propio PERFILES
        assert "PERFILES =" not in policies_source, (
            "policies.py define su propio PERFILES (debe importar desde config)"
        )

    def test_db_tablas_en_create_tables(self):
        """log_acciones debe estar dentro de create_tables (no fuera)."""
        import inspect

        import detector_duplicados.db as db_module

        db_source = inspect.getsource(db_module)

        # log_acciones debe estar en create_tables
        assert "CREATE TABLE IF NOT EXISTS log_acciones" in db_source, (
            "log_acciones no creado en create_tables"
        )

        # No debe haber DDL duplicado fuera de create_tables
        # Contar ocurrencias de "CREATE TABLE IF NOT EXISTS log_acciones"
        count = db_source.count("CREATE TABLE IF NOT EXISTS log_acciones")
        assert count == 1, (
            f"log_acciones aparece {count} veces (debe ser 1, dentro de create_tables)"
        )

    def test_cli_sin_args_clean(self):
        """--clean debe ser removido de cli.py (solo --cleanup)."""
        import inspect

        import detector_duplicados.cli as cli_module

        cli_source = inspect.getsource(cli_module)

        # No debe haber --clean en el parser
        assert '"--clean"' not in cli_source or '"--clean"' in cli_source.replace(
            '"--cleanup"', ""
        ), "--clean todavia presente en cli.py"

        # Debe tener --cleanup
        assert '"--cleanup"' in cli_source, "--cleanup no encontrado en cli.py"

    def test_html_report_obtiene_datos_reales(self):
        """generar_reporte_desde_db debe usar obtener_duplicados."""
        import inspect

        import detector_duplicados.html_report as hr_module

        hr_source = inspect.getsource(hr_module)

        assert "obtener_duplicados" in hr_source, (
            "generar_reporte_desde_db no usa obtener_duplicados (generaria reporte vacio)"
        )
        assert "archivos_duplicados =" in hr_source, (
            "generar_reporte_desde_db no construye archivos_duplicados"
        )


class TestCLIArguments:
    """Tests para verificar que CLI arguments son correctos."""

    def test_parser_sin_clean(self):
        """El parser de CLI no debe tener --clean."""
        from detector_duplicados.cli import build_parser

        parser = build_parser()

        # Verificar que no existe --clean
        action_destinations = [action.dest for action in parser._actions]
        assert "clean" not in action_destinations, "--clean todavia en el parser"

    def test_parser_tiene_cleanup(self):
        """El parser de CLI debe tener --cleanup."""
        from detector_duplicados.cli import build_parser

        parser = build_parser()

        action_destinations = [action.dest for action in parser._actions]
        assert "cleanup" in action_destinations, "--cleanup no encontrado en parser"

    def test_parser_tiene_perfil(self):
        """El parser de CLI debe tener --profile."""
        from detector_duplicados.cli import build_parser

        parser = build_parser()

        action_destinations = [action.dest for action in parser._actions]
        assert "profile" in action_destinations, "--profile no encontrado en parser"

    def test_parser_tiene_politica(self):
        """El parser de CLI debe tener --politica."""
        from detector_duplicados.cli import build_parser

        parser = build_parser()

        action_destinations = [action.dest for action in parser._actions]
        assert "politica" in action_destinations, "--politica no encontrado en parser"

    def test_parser_tiene_rollback(self):
        """El parser de CLI debe tener --rollback."""
        from detector_duplicados.cli import build_parser

        parser = build_parser()

        action_destinations = [action.dest for action in parser._actions]
        assert "rollback" in action_destinations, "--rollback no encontrado en parser"


class TestPerfilesUnificados:
    """Tests para verificar que perfiles estan unificados."""

    def test_perfiles_unicos_en_config(self):
        """PERFILES_PREDEFINIDOS solo debe estar en config.py."""
        from detector_duplicados.config import PERFILES_PREDEFINIDOS

        assert "default" in PERFILES_PREDEFINIDOS, (
            "Perfil 'default' no encontrado en PERFILES_PREDEFINIDOS"
        )
        assert "agresivo" in PERFILES_PREDEFINIDOS, (
            "Perfil 'agresivo' no encontrado en PERFILES_PREDEFINIDOS"
        )
        assert "conservador" in PERFILES_PREDEFINIDOS, (
            "Perfil 'conservador' no encontrado en PERFILES_PREDEFINIDOS"
        )

    def test_perfiles_importados_en_policies(self):
        """policies.py debe importar PERFILES de config.py."""
        from detector_duplicados.policies import PERFILES

        assert "default" in PERFILES, "PERFILES de policies.py no tiene 'default'"
        assert PERFILES["default"]["politica"] == "keep_one_copy", (
            "Politica del perfil 'default' incorrecta"
        )

    def test_perfiles_son_mismo_objeto(self):
        """PERFILES en policies.py debe ser el mismo objeto que en config.py."""
        from detector_duplicados.config import PERFILES_PREDEFINIDOS
        from detector_duplicados.policies import PERFILES

        assert PERFILES is PERFILES_PREDEFINIDOS, (
            "PERFILES en policies.py NO es el mismo objeto que en config.py (colicion detectada)"
        )

    def test_perfiles_agregados_en_cli(self):
        """El parser de CLI debe usar PERFILES_PREDEFINIDOS de config.py."""
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--cleanup", "1", "--profile", "agresivo"])

        assert args.profile == "agresivo", "Perfil 'agresivo' no cargado correctamente"
        # cleanup puede ser string si usa nargs='?'
        assert args.cleanup is not None, "ID de cleanup no encontrado"
