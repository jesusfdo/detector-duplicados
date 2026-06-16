"""Tests comprehensivos para Fase 4 (Policy Engine, Rollback, Dry-Run)."""

# Importar modulos del proyecto
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestPolicyEngine:
    """Tests para el motor de politicas de conservacion."""

    def test_keep_one_copy(self):
        """politica 'keep_one_copy' debe mantener solo 1 copia."""
        from detector_duplicados.policies import aplicar_politica

        grupo = {
            "id": 1,
            "rutas": ["/tmp/a.mp4", "/home/user/b.mp4", "/media/c.mp4"],
            "tamanio": 1000,
            "hash": "abc123",
            "escaneo_id": 1,
        }

        resultado = aplicar_politica(grupo, "keep_one_copy")

        assert resultado["accion"] in ("eliminar", "mover")
        assert len(resultado["mantener"]) == 1
        assert len(resultado["eliminar"]) == 2

    def test_keep_newest(self):
        """politica 'keep_newest' debe mantener el archivo mas reciente."""
        from detector_duplicados.policies import aplicar_politica

        grupo = {
            "id": 2,
            "rutas": ["/tmp/a.mp4", "/home/user/b.mp4", "/media/c.mp4"],
            "tamanio": 1000,
            "hash": "abc123",
            "escaneo_id": 1,
        }

        resultado = aplicar_politica(grupo, "keep_newest")

        assert len(resultado["mantener"]) == 1

    def test_keep_oldest(self):
        """politica 'keep_oldest' debe mantener el archivo mas antiguo."""
        from detector_duplicados.policies import aplicar_politica

        grupo = {
            "id": 3,
            "rutas": ["/tmp/a.mp4", "/home/user/b.mp4", "/media/c.mp4"],
            "tamanio": 1000,
            "hash": "abc123",
            "escaneo_id": 1,
        }

        resultado = aplicar_politica(grupo, "keep_oldest")

        assert len(resultado["mantener"]) == 1

    def test_keep_in_path(self):
        """politica 'keep_in_path' debe proteger archivos en rutas especificas."""
        from detector_duplicados.policies import aplicar_politica

        grupo = {
            "id": 4,
            "rutas": ["/tmp/a.mp4", "/home/user/b.mp4", "/media/c.mp4"],
            "tamanio": 1000,
            "hash": "abc123",
            "escaneo_id": 1,
        }

        resultado = aplicar_politica(grupo, "keep_in_path", rutas_protegidas=["/media/"])

        assert "/media/c.mp4" in resultado["mantener"]
        assert "/tmp/a.mp4" in resultado["eliminar"]

    def test_politica_invalida(self):
        """politica invalida debe lanzar PolicyError."""
        from detector_duplicados.policies import PolicyError, aplicar_politica

        grupo = {
            "id": 5,
            "rutas": ["/tmp/a.mp4"],
            "tamanio": 1000,
            "hash": "abc123",
            "escaneo_id": 1,
        }

        with pytest.raises(PolicyError):
            aplicar_politica(grupo, "politica_inexistente")

    def test_todas_mismas_rutas(self):
        """Si todas las rutas estan protegidas, no se elimina nada."""
        from detector_duplicados.policies import aplicar_politica

        grupo = {
            "id": 6,
            "rutas": ["/home/user/a.mp4", "/home/user/b.mp4"],
            "tamanio": 1000,
            "hash": "abc123",
            "escaneo_id": 1,
        }

        resultado = aplicar_politica(grupo, "keep_one_copy", rutas_protegidas=["/home/user/"])

        assert resultado["accion"] == "ninguna"
        assert len(resultado["mantener"]) == 2

    def test_perfiles_predefinidos(self):
        """Los perfiles predefinidos deben ser accesibles."""
        from detector_duplicados.policies import PERFILES

        assert "default" in PERFILES
        assert "agresivo" in PERFILES
        assert "conservador" in PERFILES

        # Verificar que cada perfil tiene la politica correcta
        assert PERFILES["default"]["politica"] == "keep_one_copy"
        assert PERFILES["agresivo"]["politica"] == "aggressive"
        assert PERFILES["conservador"]["politica"] == "conservative"


class TestConfigProfiles:
    """Tests para los perfiles de configuracion."""

    def test_cargar_perfil_default(self):
        """Debe cargar el perfil default correctamente."""
        from detector_duplicados.config import cargar_perfil

        perfil = cargar_perfil("default")

        assert perfil["politica"] == "keep_one_copy"
        assert perfil["umbral_riesgo"] == 50

    def test_cargar_perfil_agresivo(self):
        """Debe cargar el perfil agresivo correctamente."""
        from detector_duplicados.config import cargar_perfil

        perfil = cargar_perfil("agresivo")

        assert perfil["politica"] == "aggressive"
        assert perfil["umbral_riesgo"] == 30

    def test_cargar_perfil_conservador(self):
        """Debe cargar el perfil conservador correctamente."""
        from detector_duplicados.config import cargar_perfil

        perfil = cargar_perfil("conservador")

        assert perfil["politica"] == "conservative"
        assert perfil["umbral_riesgo"] == 70

    def test_cargar_perfil_inexistente_fallback_default(self):
        """Perfil inexistente debe fallback al default."""
        import pathlib

        from detector_duplicados.config import cargar_perfil

        # Patch para que el perfil no exista como toml
        falso_proyecto = pathlib.Path("/tmp/no_existe_dir_12345")
        with patch("detector_duplicados.config.PROJECT_DIR", falso_proyecto):
            perfil = cargar_perfil("no_existe_12345")

        # Debe haber fallback al default
        assert perfil["politica"] == "keep_one_copy"


class TestRollback:
    """Tests para el sistema de rollback."""

    def test_registrar_accion(self):
        """Debe registrar acciones correctamente."""
        from detector_duplicados.db import (
            create_connection,
            create_tables,
            registrar_accion,
        )

        conn = create_connection(":memory:")
        create_tables(conn)

        registrar_accion(conn, "mover", "/tmp/orig.mp4", "/tmp/dest.mp4", 1, True)

        acciones = conn.execute("SELECT * FROM log_acciones").fetchall()
        assert len(acciones) == 1
        assert acciones[0]["tipo"] == "mover"
        assert acciones[0]["exito"] == 1

    def test_obtener_acciones_ultimas_n(self):
        """Debe retornar las ultimas N acciones."""
        from detector_duplicados.db import (
            create_connection,
            create_tables,
            obtener_rollback_disponible,
            registrar_accion,
        )

        conn = create_connection(":memory:")
        create_tables(conn)

        for i in range(10):
            registrar_accion(conn, "mover", f"/tmp/file_{i}.mp4", f"/tmp/dest_{i}.mp4", 1, True)

        ultimas = obtener_rollback_disponible(conn, 3)
        assert len(ultimas) == 3

    def test_deshacer_accion_mover(self):
        """Debe deshacer acciones de tipo mover."""
        from detector_duplicados.db import (
            create_connection,
            create_tables,
            deshacer_accion,
            registrar_accion,
        )

        conn = create_connection(":memory:")
        create_tables(conn)

        # Crear el archivo de destino en disco (necesario para que deshacer funcione)
        orig_file = "/tmp/test_deshacer_orig.mp4"
        dest_file = "/tmp/test_deshacer_dest.mp4"
        Path(dest_file).write_text("contenido temporal")

        registrar_accion(conn, "mover", orig_file, dest_file, 1, True)

        # Obtener el ID de la accion
        accion = conn.execute("SELECT id FROM log_acciones").fetchone()
        accion_id = accion["id"]

        # Verificar que existe el destino
        result = deshacer_accion(conn, accion_id)
        assert result is True  # El archivo se movio de vuelta al origen

    def test_obtener_rollback_disponible(self):
        """Debe retornar las acciones reversibles."""
        from detector_duplicados.db import (
            create_connection,
            create_tables,
            obtener_rollback_disponible,
            registrar_accion,
        )

        conn = create_connection(":memory:")
        create_tables(conn)

        registrar_accion(conn, "mover", "/tmp/a.mp4", "/tmp/b.mp4", 1, True)
        registrar_accion(conn, "eliminar", "/tmp/c.mp4", None, 1, True)
        registrar_accion(conn, "copiar", "/tmp/d.mp4", "/tmp/e.mp4", 1, False)

        disponibles = obtener_rollback_disponible(conn, 5)

        # Solo la accion "mover" con exito=1 es reversible
        # "eliminar" no esta en la lista de tipos reversibles
        # "copiar" con exito=0 tambien queda fuera
        assert len(disponibles) == 1
        assert disponibles[0]["tipo"] == "mover"

    def test_deshacer_accion_no_existe(self):
        """Deshacer una accion inexistente debe retornar False."""
        from detector_duplicados.db import (
            create_connection,
            create_tables,
            deshacer_accion,
        )

        conn = create_connection(":memory:")
        create_tables(conn)

        result = deshacer_accion(conn, 999)
        assert result is False


class TestDryRunCleanup:
    """Tests para dry-run de limpieza."""

    @pytest.fixture
    def conn(self):
        """Conexion a memoria para tests."""
        from detector_duplicados.db import create_connection, create_tables

        conn = create_connection(":memory:")
        create_tables(conn)
        return conn

    def test_dry_run_vacio(self):
        """Dry-run sin duplicados debe retornar cero acciones."""
        from detector_duplicados.cleaner import dry_run_cleanup

        resultado = dry_run_cleanup({}, "keep_one_copy", "default")

        assert resultado["total_duplicados"] == 0
        assert resultado["acciones"] == []
        assert resultado["error"] is None

    def test_dry_run_con_duplicados(self):
        """Dry-run con duplicados debe calcular acciones."""
        from detector_duplicados.cleaner import dry_run_cleanup

        archivos_dup = {
            "group1": {
                "rutas": ["/tmp/a.mp4", "/home/user/b.mp4"],
                "tamanio": 1000,
                "hash": "abc123",
                "escaneo_id": 1,
            }
        }

        resultado = dry_run_cleanup(archivos_dup, "keep_one_copy", "default")

        assert resultado["total_duplicados"] == 1
        assert resultado["total_archivos"] == 2
        assert resultado["acciones"] != []
        assert resultado["error"] is None

    def test_dry_run_politica_invalida(self):
        """Dry-run con politica invalida debe retornar error."""
        from detector_duplicados.cleaner import dry_run_cleanup

        archivos_dup = {
            "group1": {
                "rutas": ["/tmp/a.mp4", "/home/user/b.mp4"],
                "tamanio": 1000,
                "hash": "abc123",
                "escaneo_id": 1,
            }
        }

        resultado = dry_run_cleanup(archivos_dup, "politica_invalida_xyz")

        assert resultado["error"] is not None


class TestCLIArguments:
    """Tests para los nuevos argumentos CLI."""

    def test_parser_cleanup(self):
        """El parser debe aceptar --cleanup."""
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--cleanup", "5"])

        assert args.cleanup == "5"  # nargs="?" returns string

    def test_parser_cleanup_default(self):
        """--cleanup sin ID debe tener valor por defecto."""
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--cleanup"])

        assert args.cleanup == 1

    def test_parser_profile(self):
        """El parser debe aceptar --profile."""
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--cleanup", "--profile", "agresivo"])

        assert args.profile == "agresivo"

    def test_parser_rollback(self):
        """El parser debe aceptar --rollback."""
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--rollback", "42"])

        assert args.rollback == 42

    def test_parser_list_rollback(self):
        """El parser debe aceptar --list-rollback."""
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--list-rollback"])

        assert args.list_rollback is True

    def test_parser_dry_run(self):
        """El parser debe aceptar --dry-run."""
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--cleanup", "--dry-run"])

        assert args.dry_run is True

    def test_parser_politica(self):
        """El parser debe aceptar --politica."""
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--cleanup", "--politica", "keep_newest"])

        assert args.politica == "keep_newest"

    def test_parser_modo_cleanup(self):
        """El parser debe aceptar --modo-cleanup."""
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--cleanup", "--modo-cleanup", "renombrar"])

        assert args.modo_cleanup == "renombrar"


class TestConfigLoader:
    """Tests para carga de configuracion desde archivos."""

    def test_cargar_perfil_desde_toml(self):
        """Debe cargar perfiles desde archivos .toml."""
        from detector_duplicados.config import PROJECT_DIR, cargar_perfil

        # Crear archivo toml temporal
        perfiles_dir = PROJECT_DIR / "perfiles"
        perfiles_dir.mkdir(exist_ok=True)

        toml_content = """politica = "aggressive"
umbral_riesgo = 40
rutas_protegidas = ["/custom/"]
"""
        toml_file = perfiles_dir / "custom.toml"
        toml_file.write_text(toml_content)

        perfil = cargar_perfil("custom")
        assert perfil["politica"] == "aggressive"
        assert perfil["umbral_riesgo"] == 40

        # Limpiar
        toml_file.unlink()
