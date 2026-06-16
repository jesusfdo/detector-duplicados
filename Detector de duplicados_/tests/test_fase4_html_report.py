"""Tests rigurosos para la Fase 4: Reportes HTML (html_report.py)"""

import os
import tempfile

from src.detector_duplicados.html_report import generar_reporte_html


class TestGenerarReporteHTML:
    """Pruebas para generar_reporte_html()."""

    def test_generar_reporte_sin_duplicados(self):
        """Verificar que genera reporte incluso sin duplicados."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            nombre_reporte = f.name

        try:
            reporte = generar_reporte_html(
                archivos_duplicados={},
                carpetas_duplicadas={},
                total_archivos=100,
                total_carpetas=50,
                nombre_reporte=nombre_reporte,
            )

            # Verificar que el archivo fue creado
            assert os.path.exists(reporte)

            # Verificar que tiene contenido valido
            with open(reporte) as f:
                contenido = f.read()
                assert len(contenido) > 100  # Al menos 100 bytes
        finally:
            if os.path.exists(nombre_reporte):
                os.remove(nombre_reporte)

    def test_generar_reporte_con_duplicados(self):
        """Verificar que el reporte incluye duplicados."""
        archivos_duplicados = {
            "grupo_1": {
                "rutas": ["/tmp/archivo1.txt", "/home/user/archivo1_copy.txt"],
                "tamanio": 1024,
            },
            "grupo_2": {
                "rutas": ["/var/data/file.dat", "/tmp/file_backup.dat"],
                "tamanio": 2048,
            },
        }

        carpetas_duplicadas = {
            "carpeta_1": {
                "nombre": "documentos",
                "rutas": ["/home/user/documentos", "/backup/documentos"],
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            nombre_reporte = f.name

        try:
            reporte = generar_reporte_html(
                archivos_duplicados=archivos_duplicados,
                carpetas_duplicadas=carpetas_duplicadas,
                total_archivos=1000,
                total_carpetas=200,
                nombre_reporte=nombre_reporte,
            )

            # Verificar que el archivo existe
            assert os.path.exists(reporte)

            # Verificar contenido
            with open(reporte) as f:
                contenido = f.read()

                # Debe incluir las rutas de duplicados
                assert "/tmp/archivo1.txt" in contenido
                assert "/home/user/archivo1_copy.txt" in contenido
                assert "/var/data/file.dat" in contenido
                assert "/tmp/file_backup.dat" in contenido

                # Debe incluir informacion de carpetas
                assert "documentos" in contenido

                # Debe incluir estadisticas
                assert "1,000" in contenido or "1000" in contenido
        finally:
            if os.path.exists(nombre_reporte):
                os.remove(nombre_reporte)

    def test_reporte_html_valido(self):
        """Verificar que el reporte es HTML valido."""
        reporte = generar_reporte_html(
            archivos_duplicados={},
            carpetas_duplicadas={},
            total_archivos=0,
            total_carpetas=0,
            nombre_reporte="/tmp/test_report_valid.html",
        )

        try:
            with open(reporte) as f:
                contenido = f.read()

                # Estructura basica HTML
                assert contenido.startswith("<!DOCTYPE html>")
                assert "<html" in contenido
                assert "</html>" in contenido

                # Debe tener estilos
                assert "<style>" in contenido

                # Debe tener metadatos
                assert "<meta charset" in contenido or "charset=" in contenido
        finally:
            if os.path.exists(reporte):
                os.remove(reporte)

    def test_reporte_nombre_personalizado(self):
        """Verificar que se puede especificar nombre de archivo."""
        nombre_reporte = "/tmp/reporte_personalizado_12345.html"

        reporte = generar_reporte_html(
            archivos_duplicados={},
            carpetas_duplicadas={},
            total_archivos=0,
            total_carpetas=0,
            nombre_reporte=nombre_reporte,
        )

        try:
            assert reporte == nombre_reporte
            assert os.path.exists(nombre_reporte)
        finally:
            if os.path.exists(nombre_reporte):
                os.remove(nombre_reporte)

    def test_espacio_duplicado_calculado(self):
        """Verificar que el espacio duplicado se calcula correctamente."""
        archivos_duplicados = {
            "grupo_1": {
                "rutas": ["/a.txt", "/b.txt", "/c.txt"],  # 3 copias -> 2 espacio duplicado
                "tamanio": 1000,
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            nombre_reporte = f.name

        try:
            reporte = generar_reporte_html(
                archivos_duplicados=archivos_duplicados,
                carpetas_duplicadas={},
                total_archivos=100,
                total_carpetas=50,
                nombre_reporte=nombre_reporte,
            )

            with open(reporte) as f:
                contenido = f.read()
                # Espacio duplicado: 1000 * (3-1) = 2000
                assert "2,000" in contenido or "2000" in contenido
        finally:
            if os.path.exists(nombre_reporte):
                os.remove(nombre_reporte)
