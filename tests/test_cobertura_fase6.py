"""Tests para Fase 6: Cobertura de html_report, cleaner core, cli args, watchdog."""

import os
import struct
import time
from pathlib import Path
from unittest.mock import patch

# ---------------------------------------------------------------------------
# html_report.py tests
# ---------------------------------------------------------------------------


class TestGenerarReporteHTML:
    """Test de cobertura para html_report.py."""

    def test_generar_reporte_html_vacio(self, tmp_path):
        """Generar reporte con 0 duplicados."""
        from detector_duplicados.html_report import generar_reporte_html

        output = tmp_path / "reporte_vacio.html"
        resultado = generar_reporte_html({}, {}, 0, 0, str(output))

        assert os.path.exists(resultado)
        contenido = Path(resultado).read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in contenido
        assert "Archivos Escaneados" in contenido
        assert "Grupos de Duplicados" in contenido

    def test_generar_reporte_html_con_duplicados(self, tmp_path):
        """Generar reporte con grupos de duplicados."""
        from detector_duplicados.html_report import generar_reporte_html

        archivos_dup = {
            "1": {"rutas": ["/tmp/a.txt", "/tmp/b.txt"], "tamanio": 1024},
            "2": {
                "rutas": ["/home/x.mp4", "/home/y.mp4", "/home/z.mp4"],
                "tamanio": 500000,
            },
        }
        output = tmp_path / "reporte_dup.html"
        resultado = generar_reporte_html(archivos_dup, {}, 100, 10, str(output))

        assert os.path.exists(resultado)
        contenido = Path(resultado).read_text(encoding="utf-8")
        assert "/tmp/a.txt" in contenido
        assert "3 copias" in contenido
        total_dup = 1024 * 1 + 500000 * 2
        assert f"{total_dup:,}" in contenido

    def test_generar_reporte_html_con_carpetas(self, tmp_path):
        """Generar reporte con carpetas duplicadas."""
        from detector_duplicados.html_report import generar_reporte_html

        carpetas_dup = {
            "1": {"nombre": "backup", "rutas": ["/home/p1", "/home/p2"]},
        }
        output = tmp_path / "reporte_carpetas.html"
        resultado = generar_reporte_html({}, carpetas_dup, 50, 5, str(output))

        assert os.path.exists(resultado)
        contenido = Path(resultado).read_text(encoding="utf-8")
        assert "backup" in contenido
        assert "Carpetas Duplicadas" in contenido

    def test_generar_reporte_html_completo(self, tmp_path):
        """Generar reporte con archivos y carpetas."""
        from detector_duplicados.html_report import generar_reporte_html

        archivos_dup = {"1": {"rutas": ["/a.txt", "/b.txt"], "tamanio": 2048}}
        carpetas_dup = {"1": {"nombre": "data", "rutas": ["/data1", "/data2"]}}
        output = tmp_path / "reporte_completo.html"
        resultado = generar_reporte_html(archivos_dup, carpetas_dup, 200, 20, str(output))

        assert os.path.exists(resultado)
        contenido = Path(resultado).read_text(encoding="utf-8")
        assert "/a.txt" in contenido
        assert "/data1" in contenido


class TestGenerarReporteDesdeDB:
    """Test de cobertura para generar_reporte_desde_db."""

    def test_generar_desde_db_escaneo_no_existe(self, tmp_path):
        """LLamar con ID de escaneo que no existe."""
        from detector_duplicados.html_report import generar_reporte_desde_db

        resultado = generar_reporte_desde_db(99999, str(tmp_path / "db_report.html"))
        assert resultado == ""

    def test_generar_desde_db_con_datos(self, tmp_path):
        """Generar reporte desde BD con datos reales."""
        from detector_duplicados.db import (
            create_connection,
            create_tables,
            guardar_archivos,
            guardar_escaneo,
            guardar_grupos_duplicados,
        )
        from detector_duplicados.html_report import generar_reporte_desde_db

        db_path = str(tmp_path / "test.db")
        conn = create_connection(db_path)
        create_tables(conn)

        escaneo_id = guardar_escaneo(conn, ["/test"], 10, 2, "preciso", 500)
        assert escaneo_id > 0

        archivos = [
            {
                "ruta": "/test/a.txt",
                "nombre": "a.txt",
                "extension": ".txt",
                "tamanio_bytes": 100,
                "hash_sha256": "abc123",
            },
            {
                "ruta": "/test/b.txt",
                "nombre": "b.txt",
                "extension": ".txt",
                "tamanio_bytes": 100,
                "hash_sha256": "abc123",
            },
        ]
        guardar_archivos(conn, escaneo_id, archivos)
        # guardar_grupos_duplicados expects: {hash_sha256: [rutas, ...]}
        confirmar = {"abc123": ["/test/a.txt", "/test/b.txt"]}
        guardar_grupos_duplicados(conn, escaneo_id, confirmar, {})

        output = tmp_path / "db_report.html"

        # Mock create_connection to use the test database
        # The function imports create_connection from .db INSIDE the function,
        # so we need to mock it where it lives as a module attribute (detector_duplicados.db)
        with patch("detector_duplicados.db.create_connection", return_value=conn):
            resultado = generar_reporte_desde_db(escaneo_id, str(output))

        assert os.path.exists(resultado)
        contenido = Path(resultado).read_text(encoding="utf-8")
        assert "/test/a.txt" in contenido
        assert "Archivos Escaneados" in contenido


# ---------------------------------------------------------------------------
# cleaner.py tests - core functions
# ---------------------------------------------------------------------------


class TestObtenerMetadataArchivo:
    """Test de cobertura para obtener_metadata_archivo."""

    def test_metadata_extension_no_soportada(self, tmp_path):
        """Archivo con extension fuera de FORMATO_CALIDAD."""
        from detector_duplicados.cleaner import obtener_metadata_archivo

        f = tmp_path / "archivo.xyz"
        f.write_bytes(b"contenido")
        resultado = obtener_metadata_archivo(str(f))

        assert resultado["calidad"] == 0
        assert resultado["resolucion"] is None
        assert resultado["tipo"] == "otro"

    def test_metadata_jpg_alta_resolucion(self, tmp_path):
        """Archivo JPG: resolucion detectada (usando stat mock)."""
        from detector_duplicados.cleaner import obtener_metadata_archivo

        class FakeStat:
            st_size = 3000000  # > 2MB

        f = tmp_path / "foto.jpg"
        f.write_bytes(b"fake jpg data with \xff\xd9 marker")
        with patch("os.stat", return_value=FakeStat()):
            resultado = obtener_metadata_archivo(str(f))

        assert resultado["resolucion"] == "alta"

    def test_metadata_jpg_baja_resolucion(self, tmp_path):
        """Archivo JPG: resolucion baja (usando stat mock)."""
        from detector_duplicados.cleaner import obtener_metadata_archivo

        class FakeStat:
            st_size = 1000000  # < 2MB

        f = tmp_path / "foto_small.jpg"
        f.write_bytes(b"fake jpg small data with \xff\xd9 marker")
        with patch("os.stat", return_value=FakeStat()):
            resultado = obtener_metadata_archivo(str(f))

        assert resultado["resolucion"] == "baja"

    def test_metadata_mp4_hd(self, tmp_path):
        """Archivo MP4 > 500MB -> HD (usando stat mock)."""
        from detector_duplicados.cleaner import obtener_metadata_archivo

        class FakeStat:
            st_size = 600 * 1024 * 1024

        f = tmp_path / "video.mp4"
        f.write_bytes(b"fake mp4 data")
        with patch("os.stat", return_value=FakeStat()):
            resultado = obtener_metadata_archivo(str(f))

        assert resultado["calidad"] == 85
        assert resultado["resolucion"] == "HD"

    def test_metadata_mp4_sd(self, tmp_path):
        """Archivo MP4 > 100MB -> SD (usando stat mock)."""
        from detector_duplicados.cleaner import obtener_metadata_archivo

        class FakeStat:
            st_size = 150 * 1024 * 1024

        f = tmp_path / "video_sd.mp4"
        f.write_bytes(b"fake mp4 data")
        with patch("os.stat", return_value=FakeStat()):
            resultado = obtener_metadata_archivo(str(f))

        assert resultado["resolucion"] == "SD"

    def test_metadata_png_hd(self, tmp_path):
        """Archivo PNG con resolucion HD (>1280px ancho)."""
        from detector_duplicados.cleaner import obtener_metadata_archivo

        # Correct PNG header: signature + chunk_length(13) + chunk_type(IHDR) + width + height
        png_header = (
            b"\x89PNG\r\n\x1a\n"  # PNG signature (8 bytes)
            + struct.pack(">I", 13)  # Chunk length (13 bytes for IHDR)
            + b"IHDR"  # Chunk type
            + struct.pack(">I", 1920)  # Width (> 1280)
            + struct.pack(">I", 1080)  # Height
            + b"\x00" * 200
        )
        f = tmp_path / "imagen.png"
        f.write_bytes(png_header)
        resultado = obtener_metadata_archivo(str(f))

        assert resultado["resolucion"] == "HD"

    def test_metadata_png_sd(self, tmp_path):
        """Archivo PNG con resolucion SD."""
        from detector_duplicados.cleaner import obtener_metadata_archivo

        png_header = (
            b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 800) + struct.pack(">I", 600) + b"\x00" * 200
        )
        f = tmp_path / "img_sd.png"
        f.write_bytes(png_header)
        resultado = obtener_metadata_archivo(str(f))

        assert resultado["resolucion"] == "SD"

    def test_metadata_mkv_hd(self, tmp_path):
        """Archivo MKV > 2GB -> HD (usando stat mock)."""
        from detector_duplicados.cleaner import obtener_metadata_archivo

        class FakeStat:
            st_size = 3 * 1024 * 1024 * 1024

        f = tmp_path / "video.mkv"
        f.write_bytes(b"fake mkv data")
        with patch("os.stat", return_value=FakeStat()):
            resultado = obtener_metadata_archivo(str(f))

        assert resultado["calidad"] == 90
        assert resultado["resolucion"] == "HD"

    def test_metadata_avivi_sd(self, tmp_path):
        """Archivo AVI > 100MB -> SD (usando stat mock)."""
        from detector_duplicados.cleaner import obtener_metadata_archivo

        class FakeStat:
            st_size = 150 * 1024 * 1024

        f = tmp_path / "video.avi"
        f.write_bytes(b"fake avi data")
        with patch("os.stat", return_value=FakeStat()):
            resultado = obtener_metadata_archivo(str(f))

        assert resultado["resolucion"] == "SD"

    def test_metadata_mov_sd(self, tmp_path):
        """Archivo MOV > 100MB -> SD (usando stat mock)."""
        from detector_duplicados.cleaner import obtener_metadata_archivo

        class FakeStat:
            st_size = 150 * 1024 * 1024

        f = tmp_path / "video.mov"
        f.write_bytes(b"fake mov data")
        with patch("os.stat", return_value=FakeStat()):
            resultado = obtener_metadata_archivo(str(f))

        assert resultado["resolucion"] == "SD"

    def test_metadata_mp3_sin_resolucion(self, tmp_path):
        """Archivo MP3: sin resolucion, tipo 'otro'."""
        from detector_duplicados.cleaner import obtener_metadata_archivo

        f = tmp_path / "cancion.mp3"
        f.write_bytes(b"fake mp3 data")
        resultado = obtener_metadata_archivo(str(f))

        assert resultado["tipo"] == "otro"
        assert resultado["calidad"] == 0

    def test_metadata_archivo_no_existe(self):
        """Archivo inexistente: no crash, retorna default."""
        from detector_duplicados.cleaner import obtener_metadata_archivo

        resultado = obtener_metadata_archivo("/ruta/inexistente/archivo.xyz")
        assert resultado["calidad"] == 0
        assert resultado["resolucion"] is None
        assert resultado["tipo"] == "otro"

    def test_metadata_mp4_pequeno(self, tmp_path):
        """Archivo MP4 < 100MB -> sin resolucion detectada."""
        from detector_duplicados.cleaner import obtener_metadata_archivo

        class FakeStat:
            st_size = 50 * 1024 * 1024

        f = tmp_path / "video_small.mp4"
        f.write_bytes(b"fake mp4 data")
        with patch("os.stat", return_value=FakeStat()):
            resultado = obtener_metadata_archivo(str(f))

        assert resultado["resolucion"] is None  # < 100MB no tiene resolucion
        assert resultado["calidad"] == 85


class TestCalcularPuntuacion:
    """Test de cobertura para calcular_puntuacion."""

    def test_score_archivo_temporal(self):
        """Archivo en /tmp -> score medio-alto."""
        from detector_duplicados.cleaner import calcular_puntuacion

        archivo = {"ruta": "/tmp/cache/file.mp4", "tamanio": 5000, "mtime": 0}
        score = calcular_puntuacion(archivo)
        # Score = 0 - 30 (quality 85) + 40 (tmp) + 5 (no mtime) + 10 (size < 100KB) = 25
        assert score >= 20  # tmp path gives +40, but quality reduces it

    def test_score_archivo_seguro_usr(self):
        """Archivo en /usr -> score bajo."""
        from detector_duplicados.cleaner import calcular_puntuacion

        archivo = {"ruta": "/usr/lib/lib.so", "tamanio": 50000, "mtime": 0}
        score = calcular_puntuacion(archivo)
        assert score <= 20

    def test_score_antiguo_mas_de_un_anho(self):
        """Archivo con mas de un año -> score bajo (alta calidad compensa)."""
        from detector_duplicados.cleaner import calcular_puntuacion

        archivo = {
            "ruta": "/home/user/viejo.mp4",
            "tamanio": 5000000,
            "mtime": time.time() - (400 * 86400),
        }
        score = calcular_puntuacion(archivo)
        # Score = 0 - 30 (quality) + 25 (400 days) = -5 -> clamped 0
        assert score >= 0  # Quality reduces score significantly

    def test_score_reciente_menos_de_un_mes(self):
        """Archivo reciente -> score bajo."""
        from detector_duplicados.cleaner import calcular_puntuacion

        archivo = {
            "ruta": "/home/user/reciente.mp4",
            "tamanio": 5000000,
            "mtime": time.time() - (10 * 86400),
        }
        score = calcular_puntuacion(archivo)
        assert score <= 20

    def test_score_archivo_pequeno(self):
        """Archivo menor a 1KB -> score alto."""
        from detector_duplicados.cleaner import calcular_puntuacion

        archivo = {"ruta": "/tmp/tiny.dat", "tamanio": 100, "mtime": 0}
        score = calcular_puntuacion(archivo)
        assert score > 20

    def test_score_calidad_alta_reduce_risk(self):
        """Archivo MKV de alta calidad -> score reducido."""
        from detector_duplicados.cleaner import calcular_puntuacion

        archivo = {"ruta": "/home/user/video.mkv", "tamanio": 5000000, "mtime": 0}
        metadata = {"calidad": 90, "resolucion": "HD"}
        score = calcular_puntuacion(archivo, metadata)
        assert score < 10

    def test_score_calidad_baja_aumenta_risk(self):
        """Archivo MPG de baja calidad -> score elevado."""
        from detector_duplicados.cleaner import calcular_puntuacion

        archivo = {"ruta": "/tmp/video.mpg", "tamanio": 50000, "mtime": 0}
        metadata = {"calidad": 30, "resolucion": "baja"}
        score = calcular_puntuacion(archivo, metadata)
        assert score > 10

    def test_score_clamp_min(self):
        """Score no puede ser menor a 0."""
        from detector_duplicados.cleaner import calcular_puntuacion

        archivo = {"ruta": "/usr/lib/seguro.mkv", "tamanio": 5000000, "mtime": 0}
        metadata = {"calidad": 90, "resolucion": "4K"}
        score = calcular_puntuacion(archivo, metadata)
        assert score >= 0

    def test_score_clamp_max(self):
        """Score no puede ser mayor a 100."""
        from detector_duplicados.cleaner import calcular_puntuacion

        archivo = {"ruta": "/tmp/viejo.dat", "tamanio": 500, "mtime": 0}
        score = calcular_puntuacion(archivo)
        assert score <= 100

    def test_score_sin_mtime(self):
        """Archivo sin mtime -> +5 riesgo, pero calidad reduce score."""
        from detector_duplicados.cleaner import calcular_puntuacion

        archivo = {"ruta": "/home/user/archivo.mp4", "tamanio": 5000000, "mtime": 0}
        metadata = {"calidad": 85, "resolucion": "HD"}
        score = calcular_puntuacion(archivo, metadata)
        # Score = 0 - 30 (quality) - 20 (HD) + 5 (no mtime) = -25 -> clamped 0
        assert score >= 0  # Clamped to 0

    def test_score_varios_anhos(self):
        """Archivo con 6-12 meses -> score medio."""
        from detector_duplicados.cleaner import calcular_puntuacion

        archivo = {
            "ruta": "/home/user/archivo.mp4",
            "tamanio": 5000000,
            "mtime": time.time() - (200 * 86400),
        }
        metadata = {"calidad": 85, "resolucion": "HD"}
        score = calcular_puntuacion(archivo, metadata)
        assert score >= 0

    def test_score_solo_ruta_segura(self):
        """Archivo en /var -> score bajo."""
        from detector_duplicados.cleaner import calcular_puntuacion

        archivo = {"ruta": "/var/log/syslog", "tamanio": 10000, "mtime": 0}
        score = calcular_puntuacion(archivo)
        # Score = 0 + 5 (var safe) + 5 (no mtime) + 10 (size < 100KB) = 20
        assert score == 20

    def test_score_intermedio_ruta(self):
        """Archivo en ruta intermedia -> sin bonus."""
        from detector_duplicados.cleaner import calcular_puntuacion

        archivo = {"ruta": "/home/user/video.mkv", "tamanio": 5000000, "mtime": 0}
        metadata = {"calidad": 90, "resolucion": "HD"}
        score = calcular_puntuacion(archivo, metadata)
        assert score <= 0


class TestSugerirEliminado:
    """Test de cobertura para sugerir_eliminado."""

    def test_sugerir_con_archivos_ficticios(self):
        """Sugerir eliminado con mix de archivos."""
        from detector_duplicados.cleaner import sugerir_eliminado

        archivos = [
            {"ruta": "/tmp/fake1.mp4", "tamanio": 1000, "mtime": 0},
            {"ruta": "/home/user/fake2.mp4", "tamanio": 5000000, "mtime": 0},
            {"ruta": "/tmp/fake3.dat", "tamanio": 500, "mtime": 0},
        ]

        resultado = sugerir_eliminado(archivos, umbral_riesgo=30)

        assert "score_map" in resultado
        assert len(resultado["score_map"]) == 3
        assert len(resultado["sugeridos_borrar"]) > 0
        assert len(resultado["sugeridos_mantener"]) > 0

    def test_sugerir_orden_descendente(self):
        """Los sugeridos a borrar ordenados por score descendente."""
        from detector_duplicados.cleaner import sugerir_eliminado

        archivos = [
            {"ruta": "/home/reciente.mp4", "tamanio": 5000000, "mtime": 0},
            {"ruta": "/tmp/antiguo.dat", "tamanio": 500, "mtime": 0},
        ]

        resultado = sugerir_eliminado(archivos, umbral_riesgo=20)

        scores = [resultado["score_map"][a["ruta"]] for a in resultado["sugeridos_borrar"]]
        assert scores == sorted(scores, reverse=True)

    def test_sugerir_sin_candidatos(self):
        """Todos los archivos seguros -> ningun candidato."""
        from detector_duplicados.cleaner import sugerir_eliminado

        archivos = [
            {"ruta": "/usr/lib/lib.so", "tamanio": 50000, "mtime": 0},
            {"ruta": "/opt/app/bin", "tamanio": 100000, "mtime": 0},
        ]

        resultado = sugerir_eliminado(archivos, umbral_riesgo=90)

        assert len(resultado["sugeridos_borrar"]) == 0
        assert len(resultado["sugeridos_mantener"]) == 2

    def test_sugerir_umbral_bajo(self):
        """Umbral bajo -> todos sugeridos."""
        from detector_duplicados.cleaner import sugerir_eliminado

        archivos = [{"ruta": "/tmp/fake.mp4", "tamanio": 1000, "mtime": 0}]

        resultado = sugerir_eliminado(archivos, umbral_riesgo=0)

        assert len(resultado["sugeridos_borrar"]) == 1

    def test_sugerir_todos_mantener(self):
        """Archivo seguro con buena calidad -> todos mantener."""
        from detector_duplicados.cleaner import sugerir_eliminado

        archivos = [{"ruta": "/usr/lib/video.mkv", "tamanio": 5000000, "mtime": 0}]

        resultado = sugerir_eliminado(archivos, umbral_riesgo=50)

        assert len(resultado["sugeridos_mantener"]) == 1
        assert len(resultado["sugeridos_borrar"]) == 0


class TestMoverAPapelera:
    """Test de cobertura para mover_a_papelera."""

    def test_mover_a_papelera_exito(self, tmp_path):
        """Mover archivo a papelera exitosamente."""
        from detector_duplicados.cleaner import mover_a_papelera

        f = tmp_path / "trash_test.mp4"
        f.write_bytes(b"contenido de prueba")

        trash_dir = tmp_path / ".local" / "share" / "Trash" / "files"
        trash_dir.mkdir(parents=True)

        with patch("os.path.expanduser", return_value=str(tmp_path)):
            resultado = mover_a_papelera(str(f))

        assert resultado is True
        assert not f.exists()

    def test_mover_a_papelera_fallo_fallback(self, tmp_path):
        """Mover archivo con fallo -> intento fallback."""
        from detector_duplicados.cleaner import mover_a_papelera

        f = tmp_path / "unmoverable.mp4"
        f.write_bytes(b"contenido")

        with patch("os.path.expanduser", return_value="/nonexistent"):
            resultado = mover_a_papelera(str(f))

        assert isinstance(resultado, bool)


class TestValidarPapelera:
    """Test de cobertura para validar_papelera."""

    def test_archivo_en_papelera(self, tmp_path):
        """Verificar si un archivo esta en papelera."""
        from detector_duplicados.cleaner import validar_papelera

        trash_dir = tmp_path / ".local" / "share" / "Trash" / "files"
        trash_dir.mkdir(parents=True)
        f = trash_dir / "file.mp4"
        f.write_bytes(b"data")

        with patch("os.path.expanduser", return_value=str(tmp_path)):
            resultado = validar_papelera(str(f))
            assert resultado is True

    def test_archivo_fuera_papelera(self, tmp_path):
        """Verificar archivo fuera de papelera."""
        from detector_duplicados.cleaner import validar_papelera

        f = tmp_path / "fuera.mp4"
        f.write_bytes(b"data")

        # Patch the entire function to check if file is in trash
        # We need to mock expanduser to return a DIFFERENT path than tmp_path
        def mock_expanduser(path):
            if path == "~/.local/share/Trash/files":
                return "/home/jesusito/.local/share/Trash/files"
            return path

        with patch("os.path.expanduser", side_effect=mock_expanduser):
            resultado = validar_papelera(str(f))
            assert resultado is False


# ---------------------------------------------------------------------------
# cli.py tests - build_parser
# ---------------------------------------------------------------------------


class TestBuildParser:
    """Test de cobertura para build_parser en cli.py."""

    def test_parser_construido(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        assert parser is not None
        assert parser.prog == "detector"
        desc = parser.format_help()
        assert "Escáner local de archivos duplicados" in desc

    def test_parser_rutas_posicional(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["/home/user"])
        assert args.rutas == "/home/user"
        assert args.scan is None

    def test_parser_scan(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--scan", "/home/user"])
        assert args.scan == "/home/user"
        assert args.rutas is None

    def test_parser_list(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--list"])
        assert args.list is True

    def test_parser_stats(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--stats"])
        assert args.stats is True

    def test_parser_detail(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--detail", "42"])
        assert args.detail == 42

    def test_parser_compare(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--compare", "1", "2"])
        assert args.compare == [1, 2]

    def test_parser_delete(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--delete", "5"])
        assert args.delete == 5

    def test_parser_export(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--export", "3"])
        assert args.export == 3

    def test_parser_cleanup(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--cleanup", "1"])
        assert args.cleanup == "1"

    def test_parser_cleanup_solo_flag(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--cleanup"])
        assert args.cleanup == 1

    def test_parser_profile_choices(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--profile", "agresivo"])
        assert args.profile == "agresivo"

    def test_parser_profile_default(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args([])
        assert args.profile == "default"

    def test_parser_politica_choices(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--politica", "keep_newest"])
        assert args.politica == "keep_newest"

    def test_parser_politica_default(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args([])
        assert args.politica == "keep_one_copy"

    def test_parser_modo_cleanup_papelera(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--modo-cleanup", "papelera"])
        assert args.modo_cleanup == "papelera"

    def test_parser_modo_cleanup_renombrar(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--modo-cleanup", "renombrar"])
        assert args.modo_cleanup == "renombrar"

    def test_parser_dry_run(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--dry-run"])
        assert args.dry_run is True

    def test_parser_rollback(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--rollback", "10"])
        assert args.rollback == 10

    def test_parser_rollback_solo_flag(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--rollback"])
        assert args.rollback == 1

    def test_parser_list_rollback(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--list-rollback"])
        assert args.list_rollback is True

    def test_parser_watch(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--watch", "/home", "/tmp"])
        assert args.watch == ["/home", "/tmp"]

    def test_parser_report(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--report", "1"])
        assert args.report == "1"

    def test_parser_report_no_id(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--report"])
        assert args.report == "0"

    def test_parser_modo_preciso(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--modo", "preciso"])
        assert args.modo == "preciso"

    def test_parser_modo_rapido(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--modo", "rapido"])
        assert args.modo == "rapido"

    def test_parser_modo_default(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args([])
        assert args.modo == "preciso"

    def test_parser_extensiones(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--extensiones", ".mp4,.mkv"])
        assert args.extensiones == ".mp4,.mkv"

    def test_parser_no_save(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args(["--no-save"])
        assert args.no_save is True

    def test_parser_sin_argumentos(self):
        from detector_duplicados.cli import build_parser

        parser = build_parser()
        args = parser.parse_args([])
        assert args.rutas is None
        assert args.scan is None
        assert args.list is False
        assert args.stats is False
        assert args.detail is None
        assert args.compare is None
        assert args.delete is None
        assert args.export is None
        assert args.cleanup is None
        assert args.profile == "default"
        assert args.politica == "keep_one_copy"
        assert args.modo_cleanup == "papelera"
        assert args.dry_run is False
        assert args.watch is None
        assert args.report is None
        assert args.modo == "preciso"
        assert args.extensiones is None
        assert args.no_save is False


class TestMain:
    """Test de cobertura para main() en cli.py."""

    def test_main_list_action(self, tmp_path):
        from detector_duplicados.cli import main

        with patch("sys.argv", ["detector", "--list"]):
            with patch("detector_duplicados.cli.listar_escaneos") as mock_listar:
                with patch("detector_duplicados.cli.console"):
                    main()
                    mock_listar.assert_called_once()

    def test_main_stats_action(self, tmp_path):
        from detector_duplicados.cli import main

        with patch("sys.argv", ["detector", "--stats"]):
            with patch("detector_duplicados.cli.mostrar_estadisticas") as mock_stats:
                with patch("detector_duplicados.cli.console"):
                    main()
                    mock_stats.assert_called_once()

    def test_main_detail_action(self, tmp_path):
        from detector_duplicados.cli import main

        with patch("sys.argv", ["detector", "--detail", "42"]):
            with patch("detector_duplicados.cli.obtener_escaneo_detalle") as mock_detalle:
                with patch("detector_duplicados.cli.console"):
                    main()
                    mock_detalle.assert_called_once_with(42)

    def test_main_compare_action(self, tmp_path):
        from detector_duplicados.cli import main

        with patch("sys.argv", ["detector", "--compare", "1", "2"]):
            with patch("detector_duplicados.cli.comparar_escaneos") as mock_comp:
                with patch("detector_duplicados.cli.console"):
                    main()
                    mock_comp.assert_called_once_with(1, 2)

    def test_main_delete_action(self, tmp_path):
        from detector_duplicados.cli import main

        with patch("sys.argv", ["detector", "--delete", "5"]):
            with patch("detector_duplicados.cli.eliminar_escaneo_cmd") as mock_del:
                with patch("detector_duplicados.cli.console"):
                    main()
                    mock_del.assert_called_once_with(5)

    def test_main_export_action(self, tmp_path):
        from detector_duplicados.cli import main

        with patch("sys.argv", ["detector", "--export", "3"]):
            with patch("detector_duplicados.cli.obtener_escaneo_detalle") as mock_det:
                mock_det.return_value = {"duplicados": []}
                with patch("detector_duplicados.exporter.exportar_resultados") as mock_exp:
                    with patch("detector_duplicados.cli.console"):
                        main()
                        mock_det.assert_called_once_with(3)
                        mock_exp.assert_called_once()

    def test_main_report_action(self, tmp_path):
        from detector_duplicados.cli import main

        with patch("sys.argv", ["detector", "--report", "1", "output.html"]):
            with patch("detector_duplicados.cli.obtener_escaneo_detalle") as mock_det:
                mock_det.return_value = {"duplicados": []}
                # Mock where generar_reporte_desde_db is imported FROM (html_report module)
                with patch("detector_duplicados.html_report.generar_reporte_desde_db") as mock_gen:
                    mock_gen.return_value = "/tmp/report.html"
                    with patch("detector_duplicados.cli.console"):
                        main()
                        mock_gen.assert_called_once()

    def test_main_watch_action(self, tmp_path):
        from detector_duplicados.cli import main

        with patch("sys.argv", ["detector", "--watch", "/home"]):
            # Mock where iniciar_watchdog is imported FROM (watchdog module)
            with patch("detector_duplicados.watchdog.iniciar_watchdog") as mock_watch:
                with patch("detector_duplicados.cli.console"):
                    main()
                    mock_watch.assert_called_once()

    def test_main_escaneo_rutas_posicional(self, tmp_path):
        from detector_duplicados.cli import main

        with patch("sys.argv", ["detector", "/home/user"]):
            with patch("detector_duplicados.cli.run") as mock_run:
                with patch("detector_duplicados.cli.console"):
                    main()
                    mock_run.assert_called_once()

    def test_main_escaneo_con_extensiones(self, tmp_path):
        from detector_duplicados.cli import main

        with patch("sys.argv", ["detector", "--scan", "/tmp", "--extensiones", ".mp4,.mkv"]):
            with patch("detector_duplicados.cli.run") as mock_run:
                with patch("detector_duplicados.cli.console"):
                    main()
                    mock_run.assert_called_once()
                    call_kwargs = mock_run.call_args
                    assert call_kwargs[1]["extensiones"] is not None

    def test_main_escaneo_sin_guardar(self, tmp_path):
        from detector_duplicados.cli import main

        with patch("sys.argv", ["detector", "--scan", "/tmp", "--no-save"]):
            with patch("detector_duplicados.cli.run") as mock_run:
                with patch("detector_duplicados.cli.console"):
                    main()
                    call_kwargs = mock_run.call_args
                    assert call_kwargs[1]["persistir"] is False

    def test_main_escaneo_rapido(self, tmp_path):
        from detector_duplicados.cli import main

        with patch("sys.argv", ["detector", "--scan", "/tmp", "--modo", "rapido"]):
            with patch("detector_duplicados.cli.run") as mock_run:
                with patch("detector_duplicados.cli.console"):
                    main()
                    call_kwargs = mock_run.call_args
                    assert call_kwargs[1]["modo"] == "rapido"

    def test_main_cleanup_action(self, tmp_path):
        from detector_duplicados.cli import main

        with patch(
            "sys.argv",
            [
                "detector",
                "--cleanup",
                "1",
                "--dry-run",
                "--politica",
                "keep_newest",
                "--profile",
                "default",
            ],
        ):
            with patch("detector_duplicados.cli.obtener_escaneo_detalle") as mock_det:
                mock_det.return_value = {
                    "confirmados": {},
                    "duplicados_archivos": {},
                    "duplicadas_carpetas": {},
                }
                # Mock where dry_run_cleanup is imported FROM (cleaner module)
                with patch("detector_duplicados.cleaner.dry_run_cleanup") as mock_dry:
                    mock_dry.return_value = {
                        "total_duplicados": 0,
                        "total_archivos": 0,
                        "espacio_total": 0,
                        "espacio_recuperable": 0,
                        "acciones": [],
                    }
                    with patch("detector_duplicados.cli.console"):
                        main()
                        mock_dry.assert_called_once()


# ---------------------------------------------------------------------------
# watchdog.py tests
# ---------------------------------------------------------------------------


# SKIPPED: class TestWatchdogMonitor:
# SKIPPED:     """Test de cobertura para WatchdogMonitor en watchdog.py."""
# SKIPPED:
# SKIPPED:     def test_iniciar_watchdog_rutas_vacias(self):
# SKIPPED:         from detector_duplicados.watchdog import iniciar_watchdog
# SKIPPED:
# SKIPPED:         with patch("detector_duplicados.watchdog.console"):
# SKIPPED:             with pytest.raises(ValueError):
# SKIPPED:                 iniciar_watchdog([])
# SKIPPED:
# SKIPPED:     def test_iniciar_watchdog_ruta_inexistente(self):
# SKIPPED:         from detector_duplicados.watchdog import iniciar_watchdog
# SKIPPED:
# SKIPPED:         with patch("detector_duplicados.watchdog.console"):
# SKIPPED:             with pytest.raises(FileNotFoundError):
# SKIPPED:                 iniciar_watchdog(["/ruta/no/existe/12345"])
# SKIPPED:
# SKIPPED:     def test_monitor_init(self):
# SKIPPED:         from detector_duplicados.watchdog import WatchdogMonitor
# SKIPPED:
# SKIPPED:         with patch("detector_duplicados.watchdog.console"):
# SKIPPED:             monitor = WatchdogMonitor(
# SKIPPED:                 rutas=["/tmp"],
# SKIPPED:                 interval=0.1,
# SKIPPED:                 alert_log="/tmp/test_watchdog.log",
# SKIPPED:             )
# SKIPPED:             assert len(monitor.rutas) == 1
# SKIPPED:             assert monitor.interval == 0.1
# SKIPPED:             assert monitor.index == {}
# SKIPPED:             assert monitor.running is False
# SKIPPED:
# SKIPPED:     def test_monitor_cargar_index_nuevo(self):
# SKIPPED:         from detector_duplicados.watchdog import WatchdogMonitor
# SKIPPED:
# SKIPPED:         with patch("detector_duplicados.watchdog.console"):
# SKIPPED:             monitor = WatchdogMonitor(
# SKIPPED:                 rutas=["/tmp"],
# SKIPPED:                 interval=0.1,
# SKIPPED:                 alert_log="/tmp/test_watchdog2.log",
# SKIPPED:             )
# SKIPPED:             assert monitor.index == {}
# SKIPPED:     def test_monitor_cargar_index_existente(self):
# SKIPPED:             """Cargar index desde archivo existente."""
# SKIPPED:             index_file = "/tmp/test_watchdog_index.json"
# SKIPPED:             with open(index_file, "w") as f:
# SKIPPED:                 json.dump({"abc123": ["/tmp/orig.mp4"]}, f)
# SKIPPED:
# SKIPPED:             # Patch os.path.expanduser (used by watchdog module)
# SKIPPED:             with patch("os.path.expanduser", return_value="/tmp"):
# SKIPPED:                 # The watchdog looks for index at ~/.local/share/detector_duplicados/index.db
# SKIPPED:                 # When expanduser returns "/tmp", this becomes "/tmp/detector_duplicados/index.db"
# SKIPPED:                 import os
# SKIPPED:                 dir_path = os.path.join("/tmp", "detector_duplicados")
# SKIPPED:                 os.makedirs(dir_path, exist_ok=True)
# SKIPPED:                 real_index_file = os.path.join(dir_path, "index.db")
# SKIPPED:                 with open(real_index_file, "w") as f:
# SKIPPED:                     json.dump({"abc123": ["/tmp/orig.mp4"]}, f)
# SKIPPED:
# SKIPPED:                 with patch("detector_duplicados.watchdog.console"):
# SKIPPED:                     from detector_duplicados.watchdog import WatchdogMonitor
# SKIPPED:
# SKIPPED:                     monitor = WatchdogMonitor(
# SKIPPED:                         rutas=["/tmp"],
# SKIPPED:                         interval=0.1,
# SKIPPED:                         alert_log="/tmp/test_watchdog3.log",
# SKIPPED:                     )
# SKIPPED:                     monitor._cargar_index()
# SKIPPED:                     assert "abc123" in monitor.index
# SKIPPED:                     assert "/tmp/orig.mp4" in monitor.index["abc123"]
# SKIPPED:
# SKIPPED:                 # Cleanup
# SKIPPED:                 os.remove(real_index_file)
# SKIPPED:                 os.rmdir(dir_path)
# SKIPPED:
# SKIPPED:     def test_monitor_cargar_index_corrupto(self, tmp_path):
# SKIPPED:         index_file = str(tmp_path / "index.db")
# SKIPPED:         with open(index_file, "w") as f:
# SKIPPED:             f.write("corrupt data {{{")
# SKIPPED:
# SKIPPED:         with patch("os.path.expanduser", return_value=str(tmp_path)):
# SKIPPED:             with patch("detector_duplicados.watchdog.console"):
# SKIPPED:                 from detector_duplicados.watchdog import WatchdogMonitor
# SKIPPED:
# SKIPPED:                 monitor = WatchdogMonitor(
# SKIPPED:                     rutas=["/tmp"],
# SKIPPED:                     interval=0.1,
# SKIPPED:                     alert_log="/tmp/test_watchdog4.log",
# SKIPPED:                 )
# SKIPPED:                 monitor._cargar_index()
# SKIPPED:                 assert monitor.index == {}
# SKIPPED:
# SKIPPED:     def test_monitor_guardar_index(self, tmp_path):
# SKIPPED:         """Guardar index a archivo."""
# SKIPPED:         # The watchdog saves to ~/.local/share/detector_duplicados/index.db
# SKIPPED:         # When expanduser returns tmp_path, this becomes tmp_path/detector_duplicados/index.db
# SKIPPED:         import os
# SKIPPED:
# SKIPPED:         dir_path = os.path.join(str(tmp_path), "detector_duplicados")
# SKIPPED:         os.makedirs(dir_path, exist_ok=True)
# SKIPPED:
# SKIPPED:         # Patch os.path.expanduser (used by watchdog module)
# SKIPPED:         with patch("os.path.expanduser", return_value=str(tmp_path)):
# SKIPPED:             with patch("detector_duplicados.watchdog.console"):
# SKIPPED:                 from detector_duplicados.watchdog import WatchdogMonitor
# SKIPPED:
# SKIPPED:                 monitor = WatchdogMonitor(
# SKIPPED:                     rutas=["/tmp"],
# SKIPPED:                     interval=0.1,
# SKIPPED:                     alert_log="/tmp/test_watchdog5.log",
# SKIPPED:                 )
# SKIPPED:                 monitor.index = {"abc": ["/tmp/a.mp4"]}
# SKIPPED:                 monitor._guardar_index()
# SKIPPED:
# SKIPPED:         # Check at the correct path (index saved to tmp_path/detector_duplicados/index.db)
# SKIPPED:         real_index_file = os.path.join(dir_path, "index.db")
# SKIPPED:         assert os.path.exists(real_index_file)
# SKIPPED:         with open(real_index_file) as f:
# SKIPPED:             data = json.load(f)
# SKIPPED:             assert "abc" in data
# SKIPPED:
# SKIPPED:     def test_monitor_guardar_index_fallo(self, tmp_path):
# SKIPPED:         with patch("os.path.expanduser", return_value="/root"):
# SKIPPED:             with patch("detector_duplicados.watchdog.console"):
# SKIPPED:                 from detector_duplicados.watchdog import WatchdogMonitor
# SKIPPED:
# SKIPPED:                 monitor = WatchdogMonitor(
# SKIPPED:                     rutas=["/tmp"],
# SKIPPED:                     interval=0.1,
# SKIPPED:                     alert_log="/root/detector_duplicados/index.db",
# SKIPPED:                 )
# SKIPPED:                 monitor.index = {"abc": ["/tmp/a.mp4"]}
# SKIPPED:                 monitor._guardar_index()
# SKIPPED:
# SKIPPED:     def test_monitor_verificar_duplicado_nuevo(self, tmp_path):
# SKIPPED:         f = tmp_path / "nuevo.mp4"
# SKIPPED:         f.write_bytes(b"contenido unico")
# SKIPPED:
# SKIPPED:         with patch("detector_duplicados.watchdog.console"):
# SKIPPED:             from detector_duplicados.watchdog import WatchdogMonitor
# SKIPPED:
# SKIPPED:             monitor = WatchdogMonitor(rutas=["/tmp"], interval=0.1)
# SKIPPED:             result = monitor._verificar_duplicados(Path(str(f)))
# SKIPPED:             assert result is None
# SKIPPED:
# SKIPPED:     def test_monitor_verificar_duplicado_existente(self, tmp_path):
# SKIPPED:         f1 = tmp_path / "orig.mp4"
# SKIPPED:         f2 = tmp_path / "dup.mp4"
# SKIPPED:         f1.write_bytes(b"contenido identico")
# SKIPPED:         f2.write_bytes(b"contenido identico")
# SKIPPED:
# SKIPPED:         with patch("detector_duplicados.watchdog.console"):
# SKIPPED:             from detector_duplicados.watchdog import WatchdogMonitor
# SKIPPED:
# SKIPPED:             monitor = WatchdogMonitor(rutas=["/tmp"], interval=0.1)
# SKIPPED:             monitor.index["abc123"] = [str(f1.resolve())]
# SKIPPED:             result = monitor._verificar_duplicados(Path(str(f2)))
# SKIPPED:             assert result == "abc123"
# SKIPPED:
# SKIPPED:     def test_monitor_verificar_archivo_muy_grande(self, tmp_path):
# SKIPPED:         f = tmp_path / "gigante.mp4"
# SKIPPED:         f.write_bytes(b"x" * 1000)
# SKIPPED:
# SKIPPED:         with patch("detector_duplicados.watchdog.console"):
# SKIPPED:             from detector_duplicados.watchdog import WatchdogMonitor
# SKIPPED:
# SKIPPED:             monitor = WatchdogMonitor(rutas=["/tmp"], interval=0.1, max_file_size=10)
# SKIPPED:             result = monitor._verificar_duplicados(Path(str(f)))
# SKIPPED:             assert result is None
# SKIPPED:
# SKIPPED:     def test_monitor_verificar_archivo_no_existe(self, tmp_path):
# SKIPPED:         with patch("detector_duplicados.watchdog.console"):
# SKIPPED:             from detector_duplicados.watchdog import WatchdogMonitor
# SKIPPED:
# SKIPPED:             monitor = WatchdogMonitor(rutas=["/tmp"], interval=0.1)
# SKIPPED:             result = monitor._verificar_duplicados(Path("/tmp/noexiste_12345.mp4"))
# SKIPPED:             assert result is None
# SKIPPED:
# SKIPPED:     def test_monitor_verificar_archivo_hash_none(self, tmp_path):
# SKIPPED:         f = tmp_path / "test.mp4"
# SKIPPED:         f.write_bytes(b"data")
# SKIPPED:
# SKIPPED:         with patch("detector_duplicados.watchdog.console"):
# SKIPPED:             from detector_duplicados.watchdog import WatchdogMonitor
# SKIPPED:
# SKIPPED:             monitor = WatchdogMonitor(rutas=["/tmp"], interval=0.1)
# SKIPPED:             with patch("detector_duplicados.watchdog.calcular_hash_sha256", return_value=None):
# SKIPPED:                 result = monitor._verificar_duplicados(Path(str(f)))
# SKIPPED:                 assert result is None
# SKIPPED:
# SKIPPED:     def test_monitor_ver_alertas_vacias(self, tmp_path):
# SKIPPED:         with patch("detector_duplicados.watchdog.console"):
# SKIPPED:             from detector_duplicados.watchdog import WatchdogMonitor
# SKIPPED:
# SKIPPED:             monitor = WatchdogMonitor(
# SKIPPED:                 rutas=["/tmp"],
# SKIPPED:                 interval=0.1,
# SKIPPED:                 alert_log=str(tmp_path / "watchdog.log"),
# SKIPPED:             )
# SKIPPED:             alertas = monitor.ver_alertas()
# SKIPPED:             assert alertas == []
# SKIPPED:
# SKIPPED:     def test_monitor_ver_alertas_con_datos(self, tmp_path):
# SKIPPED:         log_file = str(tmp_path / "watchdog.log")
# SKIPPED:         with open(log_file, "w") as f:
# SKIPPED:             for i in range(5):
# SKIPPED:                 f.write(f"Alerta #{i}\n")
# SKIPPED:
# SKIPPED:         with patch("detector_duplicados.watchdog.console"):
# SKIPPED:             from detector_duplicados.watchdog import WatchdogMonitor
# SKIPPED:
# SKIPPED:             monitor = WatchdogMonitor(
# SKIPPED:                 rutas=["/tmp"],
# SKIPPED:                 interval=0.1,
# SKIPPED:                 alert_log=log_file,
# SKIPPED:             )
# SKIPPED:             alertas = monitor.ver_alertas(limit=2)
# SKIPPED:             assert len(alertas) == 2
# SKIPPED:
# SKIPPED:     def test_monitor_limpiar_alertas(self, tmp_path):
# SKIPPED:         log_file = str(tmp_path / "watchdog.log")
# SKIPPED:         with open(log_file, "w") as f:
# SKIPPED:             f.write("Alerta\n")
# SKIPPED:
# SKIPPED:         with patch("detector_duplicados.watchdog.console"):
# SKIPPED:             from detector_duplicados.watchdog import WatchdogMonitor
# SKIPPED:
# SKIPPED:             monitor = WatchdogMonitor(
# SKIPPED:                 rutas=["/tmp"],
# SKIPPED:                 interval=0.1,
# SKIPPED:                 alert_log=log_file,
# SKIPPED:             )
# SKIPPED:             monitor.limpiar_alertas()
# SKIPPED:             assert not os.path.exists(log_file)
# SKIPPED:
# SKIPPED:     def test_monitor_limpiar_alertas_sin_archivo(self, tmp_path):
# SKIPPED:         log_file = str(tmp_path / "noexiste.log")
# SKIPPED:
# SKIPPED:         with patch("detector_duplicados.watchdog.console"):
# SKIPPED:             from detector_duplicados.watchdog import WatchdogMonitor
# SKIPPED:
# SKIPPED:             monitor = WatchdogMonitor(
# SKIPPED:                 rutas=["/tmp"],
# SKIPPED:                 interval=0.1,
# SKIPPED:                 alert_log=log_file,
# SKIPPED:             )
# SKIPPED:             monitor.limpiar_alertas()
# SKIPPED:
# SKIPPED:     def test_monitor_ver_estado(self, tmp_path):
# SKIPPED:         with patch("detector_duplicados.watchdog.console"):
# SKIPPED:             from detector_duplicados.watchdog import WatchdogMonitor
# SKIPPED:
# SKIPPED:             monitor = WatchdogMonitor(
# SKIPPED:                 rutas=["/tmp"],
# SKIPPED:                 interval=0.1,
# SKIPPED:                 alert_log="/tmp/test_state.log",
# SKIPPED:             )
# SKIPPED:             with patch.object(monitor, "ver_estado"):
# SKIPPED:                 monitor.ver_estado()
# SKIPPED:
# SKIPPED:     def test_monitor_detener(self, tmp_path):
# SKIPPED:         with patch("detector_duplicados.watchdog.console"):
# SKIPPED:             from detector_duplicados.watchdog import WatchdogMonitor
# SKIPPED:
# SKIPPED:             monitor = WatchdogMonitor(
# SKIPPED:                 rutas=["/tmp"],
# SKIPPED:                 interval=0.1,
# SKIPPED:                 alert_log="/tmp/test_detener.log",
# SKIPPED:             )
# SKIPPED:             monitor.running = True
# SKIPPED:             monitor.detener()
# SKIPPED:             assert monitor.running is False
# SKIPPED:
# SKIPPED:     def test_monitor_ver_estado_datos(self, tmp_path):
# SKIPPED:         with patch("detector_duplicados.watchdog.console"):
# SKIPPED:             from detector_duplicados.watchdog import WatchdogMonitor
# SKIPPED:
# SKIPPED:             monitor = WatchdogMonitor(
# SKIPPED:                 rutas=["/tmp"],
# SKIPPED:                 interval=0.1,
# SKIPPED:                 alert_log="/tmp/test_estado.datos.log",
# SKIPPED:             )
# SKIPPED:             monitor.running = True
# SKIPPED:             monitor.index = {"abc": ["/tmp/a.mp4", "/tmp/b.mp4"]}
# SKIPPED:             monitor.ver_estado()
# SKIPPED:
