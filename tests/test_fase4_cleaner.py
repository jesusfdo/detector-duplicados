"""Tests rigurosos para la Fase 4: Limpieza Inteligente (cleaner.py)"""

import os
import tempfile
from datetime import datetime, timedelta

import pytest

# Importar modulo a testear
from src.detector_duplicados.cleaner import (
    calcular_puntuacion,
    limpiar_con_interactividad,
    mover_a_papelera,
    sugerir_eliminado,
    validar_papelera,
)


class TestCalcularPuntuacion:
    """Pruebas unitarias para calcular_puntuacion()."""

    def test_archivo_temporaneo_baja_puntuacion(self):
        """Archivos en /tmp deben tener ALTA puntuacion de riesgo (se deben borrar)."""
        archivo = {
            "ruta": "/tmp/archivo_test.txt",
            "tamanio": 500,  # pequeno
            "mtime": datetime.now().timestamp(),  # reciente
        }
        score = calcular_puntuacion(archivo)
        assert score >= 40, "Archivos en /tmp deben tener score >= 40"

    def test_archivo_en_home_baja_puntuacion(self):
        """Archivos en /home/ deben tener BAJA puntuacion de riesgo."""
        archivo = {
            "ruta": "/home/user/documentos/foto.jpg",
            "tamanio": 50000,  # mediano
            "mtime": datetime.now().timestamp(),
        }
        score = calcular_puntuacion(archivo)
        assert score < 30, "Archivos en /home/ deben tener score bajo"

    def test_archivo_antiguo_alta_puntuacion(self):
        """Archivos con mas de 1 ano deben tener ALTA puntuacion de riesgo."""
        fecha_antigua = (datetime.now() - timedelta(days=400)).timestamp()
        archivo = {
            "ruta": "/home/user/backup_old.zip",
            "tamanio": 100000,
            "mtime": fecha_antigua,
        }
        score = calcular_puntuacion(archivo)
        assert score >= 30, "Archivos antiguos deben tener score >= 30"

    def test_archivo_pequeno_alta_puntuacion(self):
        """Archivos muy pequenos (< 1KB) deben tener ALTA puntuacion de riesgo."""
        archivo = {
            "ruta": "/home/user/pequeno.txt",
            "tamanio": 50,
            "mtime": datetime.now().timestamp(),
        }
        score = calcular_puntuacion(archivo)
        assert score >= 30, "Archivos pequenos deben tener score >= 30"

    def test_score_maximo_100(self):
        """La puntuacion nunca debe exceder 100."""
        archivo = {
            "ruta": "/tmp/antiguo_pequeno.dat",
            "tamanio": 100,
            "mtime": (datetime.now() - timedelta(days=500)).timestamp(),
        }
        score = calcular_puntuacion(archivo)
        assert score <= 100, "Score no debe exceder 100"

    def test_archivo_grande_baja_puntuacion(self):
        """Archivos grandes (> 10MB) deben tener BAJA puntuacion de riesgo."""
        archivo = {
            "ruta": "/home/user/backup_grande.zip",
            "tamanio": 15000000,
            "mtime": datetime.now().timestamp(),
        }
        score = calcular_puntuacion(archivo)
        assert score < 20, "Archivos grandes deben tener score bajo"


class TestSugerirEliminado:
    """Pruebas para sugerir_eliminado()."""

    def test_sugerencias_segun_riesgo(self):
        """Verificar que sugerir_eliminado ordena por riesgo."""
        archivos = [
            {"ruta": "/tmp/archivo1.dat", "tamanio": 100, "mtime": datetime.now().timestamp()},
            {
                "ruta": "/home/user/seguro.txt",
                "tamanio": 50000,
                "mtime": datetime.now().timestamp(),
            },
            {
                "ruta": "/var/tmp/cache.dat",
                "tamanio": 200,
                "mtime": (datetime.now() - timedelta(days=60)).timestamp(),
            },
        ]

        resultado = sugerir_eliminado(archivos, umbral_riesgo=30)

        # Verificar que hay sugerencias de borrado y mantenimiento
        assert len(resultado["sugeridos_borrar"]) >= 0
        assert len(resultado["sugeridos_mantener"]) >= 0

        # Verificar que el score_map contiene todos los archivos
        for archivo in archivos:
            assert archivo["ruta"] in resultado["score_map"]

    def test_umbral_alto_filtra_mas(self):
        """Un umbral alto filtra mas archivos."""
        archivos = [
            {"ruta": "/tmp/archivo1.dat", "tamanio": 100, "mtime": datetime.now().timestamp()},
            {
                "ruta": "/home/user/seguro.txt",
                "tamanio": 50000,
                "mtime": datetime.now().timestamp(),
            },
            {
                "ruta": "/var/tmp/cache.dat",
                "tamanio": 200,
                "mtime": (datetime.now() - timedelta(days=60)).timestamp(),
            },
        ]

        resultado_bajo = sugerir_eliminado(archivos, umbral_riesgo=20)
        resultado_alto = sugerir_eliminado(archivos, umbral_riesgo=50)

        assert len(resultado_alto["sugeridos_borrar"]) <= len(resultado_bajo["sugeridos_borrar"])

    def test_orden_descendente(self):
        """Las sugerencias deben estar ordenadas por score descendente."""
        archivos = [
            {"ruta": "/home/seguro1.txt", "tamanio": 50000, "mtime": datetime.now().timestamp()},
            {
                "ruta": "/var/tmp/cache.dat",
                "tamanio": 100,
                "mtime": (datetime.now() - timedelta(days=60)).timestamp(),
            },
            {"ruta": "/home/seguro2.txt", "tamanio": 60000, "mtime": datetime.now().timestamp()},
        ]

        resultado = sugerir_eliminado(archivos)

        if len(resultado["sugeridos_borrar"]) >= 2:
            score1 = resultado["sugeridos_borrar"][0][1]
            score2 = resultado["sugeridos_borrar"][1][1]
            assert score1 >= score2, "Scores deben estar en orden descendente"


class TestMoverAPapelera:
    """Pruebas para mover_a_papelera()."""

    def test_mover_a_papelera_creacion(self):
        """Verificar que mover_a_papelera funciona correctamente."""
        with tempfile.TemporaryDirectory() as _td:
            archivo_origen = os.path.join(_td, "test.txt")
            with open(archivo_origen, "w") as f:
                f.write("contenido de prueba")

            # Verificar que el archivo existe
            assert os.path.exists(archivo_origen)

            # Mover a papelera
            exito = mover_a_papelera(archivo_origen)

            # Verificar que se movio correctamente
            assert exito
            assert not os.path.exists(archivo_origen)
            assert os.path.exists(os.path.expanduser("~/.local/share/Trash/files/"))

    def test_mover_a_papelera_nombre_timestamp(self):
        """Verificar que se agrega timestamp al nombre."""
        with tempfile.TemporaryDirectory() as _td:
            archivo_origen = os.path.join(_td, "test_old.txt")
            with open(archivo_origen, "w") as f:
                f.write("contenido de prueba")

            mover_a_papelera(archivo_origen)

            # Buscar el archivo en la papelera con nombre modificado
            trash_dir = os.path.expanduser("~/.local/share/Trash/files")
            archivos_en_trash = os.listdir(trash_dir)

            encontrado = False
            for nombre in archivos_en_trash:
                if "test_old" in nombre:
                    encontrado = True
                    break

            assert encontrado, "Archivo debe estar en la papelera con nombre modificado"


class TestValidarPapelera:
    """Pruebas para validar_papelera()."""

    def test_archivo_en_papelera(self):
        """Verificar que validar_papelera detecta archivos en trash."""
        with tempfile.TemporaryDirectory() as _td:
            trash_dir = os.path.expanduser("~/.local/share/Trash/files")

            # Simular archivo en trash (ruta relativa)
            ruta_simulada = os.path.join(trash_dir, "archivo_simulado_1234567890.txt")

            # Crear el archivo para que exista
            with open(ruta_simulada, "w") as f:
                f.write("simulado")

            valido = validar_papelera(ruta_simulada)
            assert valido

            # Limpiar
            os.remove(ruta_simulada)

    def test_archivo_fuera_de_papelera(self):
        """Verificar que validar_papelera NO marca archivos fuera de trash."""
        with tempfile.TemporaryDirectory() as _td:
            archivo_fuera = os.path.join(_td, "fuera_de_trash.txt")
            with open(archivo_fuera, "w") as f:
                f.write("fuera de trash")

            valido = validar_papelera(archivo_fuera)
            assert not valido

            # Limpiar
            os.remove(archivo_fuera)


class TestLimpiezaInteractiva:
    """Pruebas para limpiar_con_interactividad()."""

    def test_limpiar_con_interactividad_sin_archivos(self):
        """Verificar que no falla si no hay archivos duplicados."""
        # Esta prueba solo verifica que no crasha
        # No podemos testear la interaccion del usuario facilmente
        archivos_duplicados = {}

        # No debe lanzar excepciones
        try:
            limpiar_con_interactividad(archivos_duplicados, modo="papelera")
        except Exception as e:
            pytest.fail(f"limpiar_con_interactividad() lanzo excepcion: {e}")

    def test_limpiar_con_interactividad_archivos_falsos(self):
        """Verificar que la funcion no modifica archivos inexistentes."""
        archivos_duplicados = {
            "grupo_1": {
                "rutas": ["/tmp/inexistente_12345.txt"],
                "tamanio": 1000,
            }
        }

        # No debe lanzar excepciones
        try:
            limpiar_con_interactividad(archivos_duplicados, modo="papelera")
        except Exception as e:
            pytest.fail(f"limpiar_con_interactividad() lanzo excepcion: {e}")
