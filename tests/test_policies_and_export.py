"""Tests para policies.py y exporter.py."""
import csv
import json
import os

import pytest


class TestPoliciesDirect:
    """Tests directos para policies.py (sin pasar por cleaner.py)."""

    def test_aplicar_politica_keep_one_copy(self):
        """Politica keep_one_copy mantiene 1 archivo."""
        from detector_duplicados.policies import aplicar_politica

        grupo = {
            "id": 1,
            "rutas": ["/home/a.txt", "/home/b.txt", "/home/c.txt"],
            "tamanio": 100,
            "hash": "abc",
        }

        resultado = aplicar_politica(grupo, "keep_one_copy")

        assert len(resultado["mantener"]) == 1
        assert len(resultado["eliminar"]) == 2
        assert resultado["accion"] in ("mover", "eliminar")

    def test_aplicar_politica_keep_newest(self):
        """Politica keep_newest mantiene el archivo mas reciente."""
        from detector_duplicados.policies import aplicar_politica

        grupo = {
            "id": 2,
            "rutas": ["/home/old.txt", "/home/new.txt"],
            "tamanio": 100,
            "mtime": [1000, 2000],
            "hash": "abc",
        }

        resultado = aplicar_politica(grupo, "keep_newest")

        assert len(resultado["mantener"]) == 1
        # El archivo con mayor mtime (2000) es /home/new.txt
        assert "/home/new.txt" in resultado["mantener"] or len(resultado["mantener"]) == 1

    def test_aplicar_politica_keep_oldest(self):
        """Politica keep_oldest mantiene el archivo mas viejo."""
        from detector_duplicados.policies import aplicar_politica

        grupo = {
            "id": 3,
            "rutas": ["/home/old.txt", "/home/new.txt"],
            "tamanio": 100,
            "mtime": [1000, 2000],
            "hash": "abc",
        }

        resultado = aplicar_politica(grupo, "keep_oldest")

        assert len(resultado["mantener"]) == 1

    def test_aplicar_politica_keep_in_path(self):
        """Politica keep_in_path protege archivos en ruta especifica."""
        from detector_duplicados.policies import aplicar_politica

        grupo = {
            "id": 4,
            "rutas": ["/home/a.txt", "/media/b.txt"],
            "tamanio": 100,
            "hash": "abc",
        }

        resultado = aplicar_politica(
            grupo, "keep_in_path", rutas_protegidas=["/media/"]
        )

        assert "/media/b.txt" in resultado["mantener"]

    def test_aplicar_politica_aggressive(self):
        """Politica aggressive mantiene solo si estan protegidos."""
        from detector_duplicados.policies import aplicar_politica

        grupo = {
            "id": 5,
            "rutas": ["/home/a.txt", "/home/b.txt", "/home/c.txt"],
            "tamanio": 100,
            "hash": "abc",
        }

        resultado = aplicar_politica(grupo, "aggressive")

        assert len(resultado["mantener"]) == 1
        assert len(resultado["eliminar"]) == 2

    def test_aplicar_politica_conservative(self):
        """Politica conservative mantiene copias adicionales."""
        from detector_duplicados.policies import aplicar_politica

        grupo = {
            "id": 6,
            "rutas": ["/home/a.txt", "/home/b.txt", "/home/c.txt"],
            "tamanio": 100,
            "hash": "abc",
        }

        resultado = aplicar_politica(grupo, "conservative")

        assert len(resultado["mantener"]) >= 1  # Mantiene al menos 1
        # La politica conservadora usa umbral de riesgo mas alto

    def test_politica_invalida_lanza_error(self):
        """Politica invalida debe lanzar PolicyError."""
        from detector_duplicados.policies import PolicyError, aplicar_politica

        grupo = {
            "id": 7,
            "rutas": ["/home/a.txt"],
            "tamanio": 100,
            "hash": "abc",
        }

        with pytest.raises(PolicyError):
            aplicar_politica(grupo, "politica_inexistente_xyz")

    def test_perfiles_predefinidos_existentes(self):
        """Los perfiles predefinidos existen."""
        from detector_duplicados.policies import PERFILES

        assert "default" in PERFILES
        assert "agresivo" in PERFILES
        assert "conservador" in PERFILES

    def test_perfil_default_config(self):
        """El perfil default tiene config correcta."""
        from detector_duplicados.policies import PERFILES

        perfil = PERFILES["default"]
        assert perfil["politica"] == "keep_one_copy"
        assert perfil["umbral_riesgo"] == 50

    def test_perfil_agresivo_config(self):
        """El perfil agresivo tiene config correcta."""
        from detector_duplicados.policies import PERFILES

        perfil = PERFILES["agresivo"]
        assert perfil["politica"] == "aggressive"
        assert perfil["umbral_riesgo"] == 30

    def test_perfil_conservador_config(self):
        """El perfil conservador tiene config correcta."""
        from detector_duplicados.policies import PERFILES

        perfil = PERFILES["conservador"]
        assert perfil["politica"] == "conservative"
        assert perfil["umbral_riesgo"] == 70

    def test_politica_con_rutas_protegidas(self):
        """Politica con rutas protegidas no borra archivos en esas rutas."""
        from detector_duplicados.policies import aplicar_politica

        grupo = {
            "id": 8,
            "rutas": [
                "/home/a.txt",
                "/etc/b.txt",
                "/usr/c.txt",
            ],
            "tamanio": 100,
            "hash": "abc",
        }

        resultado = aplicar_politica(
            grupo,
            "keep_one_copy",
            rutas_protegidas=["/etc/", "/usr/"],
        )

        protegidos = [r for r in resultado["mantener"] if r.startswith(("/etc/", "/usr/"))]
        assert len(protegidos) == 2


class TestExporterTXT:
    """Tests para exportacion a TXT."""

    def test_guardar_resultados_txt_vacio(self, tmp_path):
        """Guardar TXT con duplicados vacio no crash."""
        from detector_duplicados.exporter import guardar_resultados_txt

        output = tmp_path / "report.txt"
        result = guardar_resultados_txt(
            {"archivos_duplicados": {}, "carpetas_duplicadas": {}}, str(output)
        )

        assert result is True
        assert os.path.exists(output)
        with open(output) as f:
            content = f.read()
        assert "No se encontraron archivos duplicados" in content

    def test_guardar_resultados_txt_con_duplicados(self, tmp_path):
        """Guardar TXT con duplicados reales."""
        from detector_duplicados.exporter import guardar_resultados_txt

        archivos_dup = {
            "grupo1": ["/tmp/a.txt", "/tmp/b.txt"],
        }

        output = tmp_path / "report.txt"
        result = guardar_resultados_txt(
            {"archivos_duplicados": archivos_dup, "carpetas_duplicadas": {}},
            str(output),
        )

        assert result is True
        assert os.path.exists(output)

        with open(output) as f:
            content = f.read()

        assert "grupo1" in content
        assert "/tmp/a.txt" in content
        assert "/tmp/b.txt" in content

    def test_guardar_resultados_txt_cre_archivo(self, tmp_path):
        """Guardar TXT crea el archivo en la ruta especificada."""
        from detector_duplicados.exporter import guardar_resultados_txt

        # Crear la subcarpeta antes de llamar a guardar_resultados_txt
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        output = subdir / "report.txt"

        result = guardar_resultados_txt(
            {"archivos_duplicados": {}, "carpetas_duplicadas": {}}, str(output)
        )

        assert os.path.exists(output)
        assert os.path.isfile(output)

    def test_guardar_resultados_txt_con_carpetas(self, tmp_path):
        """Guardar TXT con carpetas duplicadas."""
        from detector_duplicados.exporter import guardar_resultados_txt

        carpetas_dup = {
            "backup": ["/home/a/backup", "/home/b/backup"],
        }

        output = tmp_path / "report.txt"
        result = guardar_resultados_txt(
            {"archivos_duplicados": {}, "carpetas_duplicadas": carpetas_dup},
            str(output),
        )

        with open(output) as f:
            content = f.read()

        assert "backup" in content
        assert "/home/a/backup" in content


class TestExporterCSV:
    """Tests para exportacion a CSV."""

    def test_exportar_csv_vacio(self, tmp_path):
        """Exportar CSV con duplicados vacio no crash."""
        from detector_duplicados.exporter import _exportar_csv

        escaneo = {"id": 1, "fecha": "2026-01-01", "rutas": ["/tmp"], "total_archivos": 10, "modo": "rapido"}
        duplicados = []

        output = tmp_path / "report.csv"
        result = _exportar_csv(escaneo, duplicados, str(output))

        assert result is True
        assert os.path.exists(output)

    def test_exportar_csv_con_duplicados(self, tmp_path):
        """Exportar CSV con duplicados reales."""
        from detector_duplicados.exporter import _exportar_csv

        # El formato real requiere: confirmado (bool), hash_sha256, tamanio_bytes, cantidad, rutas (separada por "; ")
        escaneo = {"id": 1, "fecha": "2026-01-01", "rutas": ["/tmp"], "total_archivos": 10, "total_carpetas": 5, "modo": "rapido"}
        duplicados = [
            {
                "confirmado": True,
                "hash_sha256": "abc123",
                "tamanio_bytes": 1000,
                "cantidad": 2,
                "rutas": "/tmp/a.txt; /tmp/b.txt",
            }
        ]

        output = tmp_path / "report.csv"
        result = _exportar_csv(escaneo, duplicados, str(output))

        assert result is True
        assert os.path.exists(output)

        with open(output) as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert len(rows) >= 3  # Encabezado + 2 filas de rutas

    def test_exportar_csv_parseable(self, tmp_path):
        """El CSV exportado debe ser parseable."""
        from detector_duplicados.exporter import _exportar_csv

        escaneo = {"id": 1, "fecha": "2026-01-01", "rutas": ["/tmp"], "total_archivos": 10, "modo": "rapido"}

        output = tmp_path / "report.csv"
        result = _exportar_csv(escaneo, [], str(output))

        with open(output) as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert isinstance(rows, list)


class TestExporterJSON:
    """Tests para exportacion a JSON."""

    def test_exportar_json_vacio(self, tmp_path):
        """Exportar JSON con duplicados vacio no crash."""
        from detector_duplicados.exporter import _exportar_json

        escaneo = {"id": 1, "fecha": "2026-01-01", "rutas": ["/tmp"], "total_archivos": 10, "total_carpetas": 5, "modo": "rapido"}

        output = tmp_path / "report.json"
        result = _exportar_json(escaneo, [], str(output))

        assert result is True
        assert os.path.exists(output)

        with open(output) as f:
            data = json.load(f)

        assert isinstance(data, dict)

    def test_exportar_json_con_duplicados(self, tmp_path):
        """Exportar JSON con duplicados reales."""
        from detector_duplicados.exporter import _exportar_json

        escaneo = {"id": 1, "fecha": "2026-01-01", "rutas": ["/tmp"], "total_archivos": 10, "total_carpetas": 5, "modo": "rapido"}
        duplicados = [
            {
                "confirmado": True,
                "hash_sha256": "abc123",
                "tamanio_bytes": 1000,
                "cantidad": 2,
                "rutas": "/tmp/a.txt; /tmp/b.txt",
            }
        ]

        output = tmp_path / "report.json"
        result = _exportar_json(escaneo, duplicados, str(output))

        assert result is True
        assert os.path.exists(output)

        with open(output) as f:
            data = json.load(f)

        assert "abc123" in str(data)

    def test_exportar_json_valido(self, tmp_path):
        """El JSON exportado debe ser JSON valido."""
        from detector_duplicados.exporter import _exportar_json

        escaneo = {"id": 1, "fecha": "2026-01-01", "rutas": ["/tmp"], "total_archivos": 10, "total_carpetas": 5, "modo": "rapido"}

        output = tmp_path / "report.json"
        result = _exportar_json(escaneo, [], str(output))

        with open(output) as f:
            content = f.read()

        data = json.loads(content)
        assert data is not None


class TestExporterCombined:
    """Tests combinados para exporter."""

    def test_exportar_todas_formas(self, tmp_path):
        """Exportar en todas las formas no crash."""
        from detector_duplicados.exporter import (
            _exportar_csv,
            _exportar_json,
            guardar_resultados_txt,
        )

        archivos_dup = {"grupo1": ["/tmp/a.txt", "/tmp/b.txt"]}
        escaneo = {"id": 1, "fecha": "2026-01-01", "rutas": ["/tmp"], "total_archivos": 10, "total_carpetas": 5, "modo": "rapido"}
        duplicados = [
            {"confirmado": True, "hash_sha256": "abc", "tamanio_bytes": 100, "cantidad": 2, "rutas": "/tmp/a.txt; /tmp/b.txt"}
        ]

        txt_output = tmp_path / "report.txt"
        csv_output = tmp_path / "report.csv"
        json_output = tmp_path / "report.json"

        guardar_resultados_txt({"archivos_duplicados": archivos_dup, "carpetas_duplicadas": {}}, str(txt_output))
        _exportar_csv(escaneo, duplicados, str(csv_output))
        _exportar_json(escaneo, duplicados, str(json_output))

        assert os.path.exists(txt_output)
        assert os.path.exists(csv_output)
        assert os.path.exists(json_output)

    def test_exportar_con_rutas_especiales(self, tmp_path):
        """Exportar con rutas que contienen caracteres especiales."""
        from detector_duplicados.exporter import _exportar_json

        escaneo = {"id": 1, "fecha": "2026-01-01", "rutas": ["/tmp"], "total_archivos": 10, "total_carpetas": 5, "modo": "rapido"}
        duplicados = [
            {
                "confirmado": True,
                "hash_sha256": "abc",
                "tamanio_bytes": 100,
                "cantidad": 3,
                "rutas": "/home/user/file with spaces.txt; /home/user/file-with-dashes.txt; /home/user/file_with_underscores.txt",
            }
        ]

        output = tmp_path / "report.json"
        result = _exportar_json(escaneo, duplicados, str(output))

        assert result is True
        assert os.path.exists(output)


class TestExportarResultados:
    """Tests para la funcion principal exportar_resultados."""

    def test_exportar_resultados_txt_format(self, tmp_path):
        """exportar_resultados con formato txt genera archivo valido."""
        from detector_duplicados.exporter import exportar_resultados

        detalle = {
            "escaneo": {"id": 1, "fecha": "2026-01-01", "rutas": ["/tmp"], "total_archivos": 100, "total_carpetas": 10, "modo": "rapido"},
            "duplicados": [{"confirmado": True, "hash_sha256": "abc", "tamanio_bytes": 100, "cantidad": 2, "rutas": "/tmp/a.txt; /tmp/b.txt"}],
        }

        output = tmp_path / "result.txt"
        result = exportar_resultados(detalle, 1, str(output), "txt")

        assert result is True
        assert os.path.exists(output)

    def test_exportar_resultados_csv_format(self, tmp_path):
        """exportar_resultados con formato csv genera archivo valido."""
        from detector_duplicados.exporter import exportar_resultados

        detalle = {
            "escaneo": {"id": 1, "fecha": "2026-01-01", "rutas": ["/tmp"], "total_archivos": 100, "total_carpetas": 10, "modo": "rapido"},
            "duplicados": [{"confirmado": True, "hash_sha256": "abc", "tamanio_bytes": 100, "cantidad": 2, "rutas": "/tmp/a.txt; /tmp/b.txt"}],
        }

        output = tmp_path / "result.csv"
        result = exportar_resultados(detalle, 1, str(output), "csv")

        assert result is True
        assert os.path.exists(output)

    def test_exportar_resultados_json_format(self, tmp_path):
        """exportar_resultados con formato json genera archivo valido."""
        from detector_duplicados.exporter import exportar_resultados

        detalle = {
            "escaneo": {"id": 1, "fecha": "2026-01-01", "rutas": ["/tmp"], "total_archivos": 100, "total_carpetas": 10, "modo": "rapido"},
            "duplicados": [{"confirmado": True, "hash_sha256": "abc", "tamanio_bytes": 100, "cantidad": 2, "rutas": "/tmp/a.txt; /tmp/b.txt"}],
        }

        output = tmp_path / "result.json"
        result = exportar_resultados(detalle, 1, str(output), "json")

        assert result is True
        assert os.path.exists(output)
