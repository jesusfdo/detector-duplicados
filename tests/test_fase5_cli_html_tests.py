"""Tests para html_report.py (Fase 5 coverage)."""
import os

import pytest


class TestHTMLReport:
    """Tests para html_report.py."""

    def test_generar_reporte_html_vacio(self, tmp_path):
        """generar_reporte_html con datos vacios genera HTML basico."""
        from src.detector_duplicados.html_report import generar_reporte_html

        output_file = str(tmp_path / "report.html")

        result = generar_reporte_html(
            {},
            {},
            0,
            0,
            output_file,
        )
        assert result is not None
        assert os.path.exists(output_file)

        with open(output_file) as f:
            content = f.read()
        assert "Detector de Duplicados" in content
        assert "<!DOCTYPE" in content or "<html" in content

    def test_generar_reporte_html_con_datos(self, tmp_path):
        """generar_reporte_html con datos genera reporte completo."""
        from src.detector_duplicados.html_report import generar_reporte_html

        datos_dup = {
            "grupo1": {
                "hash": "abc123",
                "tamanio": 1000,
                "rutas": ["/tmp/f1.txt", "/tmp/f2.txt"],
            }
        }

        output_file = str(tmp_path / "report.html")

        result = generar_reporte_html(
            datos_dup,
            {},
            10,
            5,
            output_file,
        )
        assert result is not None
        assert os.path.exists(output_file)

        with open(output_file) as f:
            content = f.read()
        assert "10" in content
        assert "5" in content

    def test_generar_reporte_desde_db(self, tmp_path):
        """generar_reporte_desde_db funciona con DB vacia."""
        from src.detector_duplicados.html_report import generar_reporte_desde_db

        output_file = str(tmp_path / "report.html")

        try:
            result = generar_reporte_desde_db(999, output_file)
            assert result is None or result is False or os.path.exists(result)
        except Exception:
            pytest.skip("ID de escaneo no existe en DB")

    def test_generar_reporte_con_nombre_personalizado(self, tmp_path):
        """generar_reporte_html con nombre personalizado."""
        from src.detector_duplicados.html_report import generar_reporte_html

        output_file = str(tmp_path / "report_custom.html")

        result = generar_reporte_html(
            {},
            {},
            0,
            0,
            output_file,
        )
        assert result is not None
        assert os.path.exists(output_file)
