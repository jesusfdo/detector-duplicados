"""Tests unitarios para html_report.py.

FASE 3: Validación de la nueva funcionalidad de exportación HTML.
"""

import os
import unittest
from unittest.mock import patch, MagicMock


class TestGenerarReporteHTML(unittest.TestCase):
    """Pruebas para la función generar_reporte_html."""

    def setUp(self):
        """Preparar datos de prueba."""
        self.archivos_dup = {
            "1": {
                "rutas": ["/home/user/docs/rapport.pdf", "/home/user/backup/rapport.pdf"],
                "tamanio": 1048576,
            },
            "2": {
                "rutas": ["/home/user/photos/vacation1.jpg", "/home/user/photos/vacation2.jpg"],
                "tamanio": 2097152,
            },
        }
        self.carpetas_dup = {
            "1": {
                "nombre": "proyecto_backup",
                "rutas": ["/home/user/proyecto_backup", "/home/user/backup/proyecto_backup"],
            }
        }

    def test_genera_archivo_html(self):
        """Verificar que se genera un archivo HTML."""
        from detector_duplicados.html_report import generar_reporte_html

        result = generar_reporte_html(
            self.archivos_dup,
            self.carpetas_dup,
            total_archivos=150,
            total_carpetas=45,
            nombre_reporte="/tmp/test_html_report.html",
            abrir_navegador=False
        )

        self.assertTrue(os.path.exists(result))
        self.assertTrue(result.endswith("test_html_report.html"))

    def test_contenido_basico(self):
        """Verificar que el HTML tenga la estructura básica."""
        from detector_duplicados.html_report import generar_reporte_html

        result = generar_reporte_html(
            self.archivos_dup,
            self.carpetas_dup,
            total_archivos=150,
            total_carpetas=45,
            nombre_reporte="/tmp/test_html_report.html",
            abrir_navegador=False
        )

        with open(result, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("<html", content)
        self.assertIn("<body", content)
        self.assertIn("</html>", content)

    def test_buscador_interactivo(self):
        """Verificar que el HTML tenga el buscador."""
        from detector_duplicados.html_report import generar_reporte_html

        result = generar_reporte_html(
            self.archivos_dup,
            self.carpetas_dup,
            total_archivos=150,
            total_carpetas=45,
            nombre_reporte="/tmp/test_html_report.html",
            abrir_navegador=False
        )

        with open(result, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('id="search"', content)
        self.assertIn("Buscar por nombre o ruta", content)

    def test_toggle_tema(self):
        """Verificar que el HTML tenga el botón de cambio de tema."""
        from detector_duplicados.html_report import generar_reporte_html

        result = generar_reporte_html(
            self.archivos_dup,
            self.carpetas_dup,
            total_archivos=150,
            total_carpetas=45,
            nombre_reporte="/tmp/test_html_report.html",
            abrir_navegador=False
        )

        with open(result, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('id="theme-toggle"', content)
        self.assertIn("Cambiar tema", content)
        self.assertIn("data-theme", content)

    def test_exportar_csv(self):
        """Verificar que el HTML tenga el botón de exportar CSV."""
        from detector_duplicados.html_report import generar_reporte_html

        result = generar_reporte_html(
            self.archivos_dup,
            self.carpetas_dup,
            total_archivos=150,
            total_carpetas=45,
            nombre_reporte="/tmp/test_html_report.html",
            abrir_navegador=False
        )

        with open(result, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn('id="export-csv"', content)
        self.assertIn("Exportar CSV", content)

    def test_opciones_extension_dinamicas(self):
        """Verificar que el HTML tenga opciones de filtro de extensión."""
        from detector_duplicados.html_report import generar_reporte_html

        result = generar_reporte_html(
            self.archivos_dup,
            self.carpetas_dup,
            total_archivos=150,
            total_carpetas=45,
            nombre_reporte="/tmp/test_html_report.html",
            abrir_navegador=False
        )

        with open(result, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("id=\"ext-filter\"", content)
        self.assertIn("Todas las extensiones", content)
        self.assertIn(".pdf", content)
        self.assertIn(".jpg", content)

    def test_ordenamiento_columnas(self):
        """Verificar que el HTML tenga funcionalidad de ordenamiento."""
        from detector_duplicados.html_report import generar_reporte_html

        result = generar_reporte_html(
            self.archivos_dup,
            self.carpetas_dup,
            total_archivos=150,
            total_carpetas=45,
            nombre_reporte="/tmp/test_html_report.html",
            abrir_navegador=False
        )

        with open(result, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("data-col", content)
        self.assertIn("th", content)


class TestGenerarReporteDesdeDB(unittest.TestCase):
    """Pruebas para la función generar_reporte_desde_db."""

    def test_genera_reporte_desde_db(self):
        """Verificar que la función genera un reporte desde la base de datos."""
        import sys
        from unittest.mock import MagicMock, patch

        # Crear mock del módulo db
        mock_db = MagicMock()
        mock_db.create_connection.return_value = MagicMock()
        mock_db.obtener_escaneo.return_value = {"total_archivos": 100, "total_carpetas": 30}
        mock_db.obtener_archivos_escaneo.return_value = []
        mock_db.obtener_duplicados.return_value = [
            {"rutas": "/home/user/archivo1.txt; /home/user/archivo1_copy.txt", "tamanio_bytes": 1024, "hash_sha256": "abc123"}
        ]

        # Inyectar mock en sys.modules antes de importar html_report
        sys.modules["detector_duplicados.db"] = mock_db

        from detector_duplicados.html_report import generar_reporte_desde_db

        result = generar_reporte_desde_db(
            escaneo_id=1,
            nombre_reporte="/tmp/test_html_report_db.html",
            abrir_navegador=False
        )

        self.assertTrue(result)
        self.assertIn("/tmp/test_html_report_db.html", result)
        
        # Restaurar módulo original
        del sys.modules["detector_duplicados.db"]


if __name__ == "__main__":
    unittest.main()
