"""Tests que verifican ui.py soporta ambos formatos de datos de duplicados."""
import pytest


class TestMostrarResultadosTabla:
    """mostrar_resultados_tabla con ambos formatos."""

    def test_con_formato_rapido(self, capfd):
        """Formato rapido: {nombre: {"rutas": [...], "tamanio": ...}}."""
        from src.detector_duplicados.ui import mostrar_resultados_tabla

        datos = {
            "archivo.txt": {
                "rutas": ["/a/archivo.txt", "/b/archivo.txt"],
                "tamanio": 1024,
                "hash": "abc123",
            }
        }

        try:
            mostrar_resultados_tabla(datos, {}, 10, 5, None)
        except Exception as e:
            pytest.fail(f"Formato rapido crash: {e}")

    def test_con_formato_preciso(self, capfd):
        """Formato preciso: {hash: [ruta1, ruta2, ...]}.

        Este es el bug que se corrigio: mostrar_resultados_tabla
        esperaba info.get("rutas") pero info era una lista.
        """
        from src.detector_duplicados.ui import mostrar_resultados_tabla

        datos = {
            "abc123def456...": ["/a/archivo.txt", "/b/archivo.txt"],
            "xyz789ghi012...": ["/c/video.mp4", "/d/video.mp4", "/e/video.mp4"],
        }

        # Antes del fix: esto lanzaba AttributeError
        try:
            mostrar_resultados_tabla(datos, {}, 10, 5, None)
        except AttributeError as e:
            pytest.fail(f"Formato preciso crash (bug no corregido): {e}")

    def test_con_archivos_duplicados_vacio(self, capfd):
        """Datos vacios no crash."""
        from src.detector_duplicados.ui import mostrar_resultados_tabla

        try:
            mostrar_resultados_tabla({}, {}, 0, 0, None)
        except Exception as e:
            pytest.fail(f"Datos vacios crash: {e}")

    def test_con_rutas_no_escaneadas(self, capfd):
        """Rutas no escaneadas se muestran correctamente."""
        from src.detector_duplicados.ui import mostrar_resultados_tabla

        datos = {"grupo1": {"rutas": ["/a/f1.txt", "/b/f1.txt"], "tamanio": 100}}
        rutas_no = ["/root/secret", "/proc/kcore"]

        try:
            mostrar_resultados_tabla(datos, {}, 10, 5, rutas_no)
        except Exception as e:
            pytest.fail(f"Con rutas_no_escaneadas crash: {e}")
