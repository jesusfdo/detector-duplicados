"""Tests para el modulo db.py (Fase 2).

Cubren:
  - Creacion de tablas
  - Guardado y recuperacion de escaneos
  - Guardado de archivos y duplicados
  - Comparacion entre escaneos
  - Eliminacion de escaneos
  - Estadisticas
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import detector_duplicados.db as db_module


@pytest.fixture
def temp_db():
    """Crea una base de datos temporal para cada test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    conn = db_module.create_connection(db_path)
    db_module.create_tables(conn)
    yield conn

    conn.close()
    os.unlink(db_path)


class TestCreateTables:
    """Pruebas para la creacion de tablas."""

    def test_creacion_tablas_existen(self, temp_db):
        """Verificar que las tablas se crearon correctamente."""
        for table in ["escaneos", "archivos", "grupos_duplicados"]:
            row = temp_db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
            assert row is not None

    def test_indexes_existentes(self, temp_db):
        """Verificar que los indices se crearon."""
        for idx in ["idx_archivos_hash", "idx_archivos_ruta"]:
            row = temp_db.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
                (idx,),
            ).fetchone()
            assert row is not None


class TestGuardarEscaneo:
    """Pruebas para guardar y recuperar escaneos."""

    def test_guardar_escaneo_inserta_fila(self, temp_db):
        """Verificar que guardar_escaneo inserta una fila."""
        escaneo_id = db_module.guardar_escaneo(
            temp_db,
            rutas=["/test/ruta1"],
            total_archivos=10,
            total_carpetas=5,
            modo="preciso",
            duracion_ms=1234,
        )
        assert escaneo_id > 0

    def test_guardar_escaneo_datos_correctos(self, temp_db):
        """Verificar que los datos del escaneo se guardan correctamente."""
        escaneo_id = db_module.guardar_escaneo(
            temp_db,
            rutas=["/ruta1", "/ruta2"],
            total_archivos=20,
            total_carpetas=10,
            modo="rapido",
            duracion_ms=5678,
        )
        escaneo = db_module.obtener_escaneo(temp_db, escaneo_id)
        assert escaneo is not None
        assert escaneo["total_archivos"] == 20
        assert escaneo["total_carpetas"] == 10
        assert escaneo["modo"] == "rapido"
        assert escaneo["duracion_ms"] == 5678
        assert json.loads(escaneo["rutas"]) == ["/ruta1", "/ruta2"]

    def test_guardar_escaneo_duracion_none(self, temp_db):
        """Verificar que se puede guardar con duracion_ms=None."""
        escaneo_id = db_module.guardar_escaneo(
            temp_db,
            rutas=["/test"],
            total_archivos=5,
            total_carpetas=0,
            modo="preciso",
            duracion_ms=None,
        )
        escaneo = db_module.obtener_escaneo(temp_db, escaneo_id)
        assert escaneo is not None

    def test_obtener_escaneos_list_all(self, temp_db):
        """Verificar que obtener_escaneos retorna todos los escaneos."""
        for i in range(3):
            db_module.guardar_escaneo(
                temp_db,
                rutas=[f"/ruta{i}"],
                total_archivos=i,
                total_carpetas=0,
            )

        escaneos = db_module.obtener_escaneos(temp_db, limit=50)
        assert len(escaneos) == 3

    def test_obtener_escaneos_limit(self, temp_db):
        """Verificar que el limite funciona."""
        for i in range(10):
            db_module.guardar_escaneo(
                temp_db,
                rutas=[f"/ruta{i}"],
                total_archivos=1,
                total_carpetas=0,
            )

        escaneos = db_module.obtener_escaneos(temp_db, limit=5)
        assert len(escaneos) == 5


class TestGuardarArchivos:
    """Pruebas para guardar archivos en la base de datos."""

    def test_guardar_archivos_inserta_filas(self, temp_db):
        """Verificar que los archivos se guardan."""
        escaneo_id = db_module.guardar_escaneo(
            temp_db,
            rutas=["/test"],
            total_archivos=0,
            total_carpetas=0,
        )

        archivos = [
            {
                "ruta": "/test/archivo1.txt",
                "nombre": "archivo1",
                "extension": ".txt",
                "tamanio": 1024,
                "mtime": 1234567890,
                "hash_sha256": "abc123",
                "hash_computado": 1,
            },
            {
                "ruta": "/test/archivo2.txt",
                "nombre": "archivo2",
                "extension": ".txt",
                "tamanio": 2048,
                "mtime": 1234567890,
                "hash_sha256": "def456",
                "hash_computado": 1,
            },
        ]

        db_module.guardar_archivos(temp_db, escaneo_id, archivos)

        stored = db_module.obtener_archivos_escaneo(temp_db, escaneo_id)
        assert len(stored) == 2

    def test_guardar_archivos_duplicados_reemplazo(self, temp_db):
        """Verificar que guardar el mismo archivo dos veces no duplica."""
        escaneo_id = db_module.guardar_escaneo(
            temp_db,
            rutas=["/test"],
            total_archivos=0,
            total_carpetas=0,
        )

        archivos = [
            {
                "ruta": "/test/archivo.txt",
                "nombre": "archivo",
                "extension": ".txt",
                "tamanio": 100,
                "mtime": 1234567890,
                "hash_sha256": "hash1",
                "hash_computado": 1,
            },
        ]

        db_module.guardar_archivos(temp_db, escaneo_id, archivos)
        db_module.guardar_archivos(temp_db, escaneo_id, archivos)

        stored = db_module.obtener_archivos_escaneo(temp_db, escaneo_id)
        assert len(stored) == 1

    def test_obtener_archivos_escaneo_vacio(self, temp_db):
        """Verificar que se retorna lista vacia si no hay archivos."""
        escaneo_id = db_module.guardar_escaneo(
            temp_db,
            rutas=["/test"],
            total_archivos=0,
            total_carpetas=0,
        )

        stored = db_module.obtener_archivos_escaneo(temp_db, escaneo_id)
        assert len(stored) == 0


class TestGuardarGruposDuplicados:
    """Pruebas para guardar grupos de duplicados."""

    def test_guardar_confirmados(self, temp_db):
        """Verificar que los duplicados confirmados se guardan."""
        escaneo_id = db_module.guardar_escaneo(
            temp_db,
            rutas=["/test"],
            total_archivos=2,
            total_carpetas=0,
        )

        # Insertar archivos con el mismo hash
        archivos = [
            {
                "ruta": "/test/a.mp4",
                "nombre": "a",
                "extension": ".mp4",
                "tamanio": 1000,
                "hash_sha256": "abc123",
                "hash_computado": 1,
            },
            {
                "ruta": "/test/b.mp4",
                "nombre": "b",
                "extension": ".mp4",
                "tamanio": 1000,
                "hash_sha256": "abc123",
                "hash_computado": 1,
            },
        ]
        db_module.guardar_archivos(temp_db, escaneo_id, archivos)

        confirmados = {"abc123": ["/test/a.mp4", "/test/b.mp4"]}
        db_module.guardar_grupos_duplicados(temp_db, escaneo_id, confirmados, {})

        duplicados = db_module.obtener_duplicados(temp_db, escaneo_id, confirmado=1)
        assert len(duplicados) == 1
        assert duplicados[0]["confirmado"] == 1
        assert duplicados[0]["cantidad"] == 2

    def test_guardar_sospechosos(self, temp_db):
        """Verificar que los sospechosos se guardan como no confirmados."""
        escaneo_id = db_module.guardar_escaneo(
            temp_db,
            rutas=["/test"],
            total_archivos=0,
            total_carpetas=0,
        )

        sospechosos = {"carpeta_duplicada": ["/test/a", "/test/b"]}
        db_module.guardar_grupos_duplicados(temp_db, escaneo_id, {}, sospechosos)

        duplicados = db_module.obtener_duplicados(temp_db, escaneo_id, confirmado=0)
        assert len(duplicados) == 1
        assert duplicados[0]["confirmado"] == 0


class TestCompararEscaneos:
    """Pruebas para comparacion de escaneos."""

    def test_detectar_nuevos_archivos(self, temp_db):
        """Verificar que se detectan archivos nuevos."""
        esc1_id = db_module.guardar_escaneo(
            temp_db,
            rutas=["/test"],
            total_archivos=1,
            total_carpetas=0,
        )
        db_module.guardar_archivos(
            temp_db,
            esc1_id,
            [
                {
                    "ruta": "/test/a.txt",
                    "nombre": "a",
                    "extension": ".txt",
                    "tamanio": 100,
                    "hash_sha256": "hash_a",
                    "hash_computado": 1,
                },
            ],
        )

        esc2_id = db_module.guardar_escaneo(
            temp_db,
            rutas=["/test"],
            total_archivos=2,
            total_carpetas=0,
        )
        db_module.guardar_archivos(
            temp_db,
            esc2_id,
            [
                {
                    "ruta": "/test/a.txt",
                    "nombre": "a",
                    "extension": ".txt",
                    "tamanio": 100,
                    "hash_sha256": "hash_a",
                    "hash_computado": 1,
                },
                {
                    "ruta": "/test/b.txt",
                    "nombre": "b",
                    "extension": ".txt",
                    "tamanio": 200,
                    "hash_sha256": "hash_b",
                    "hash_computado": 1,
                },
            ],
        )

        diff = db_module.comparar_escaneos(temp_db, esc1_id, esc2_id)
        assert len(diff["nuevos"]) == 1
        assert diff["nuevos"][0]["ruta"] == "/test/b.txt"

    def test_detectar_eliminados(self, temp_db):
        """Verificar que se detectan archivos eliminados."""
        esc1_id = db_module.guardar_escaneo(
            temp_db,
            rutas=["/test"],
            total_archivos=2,
            total_carpetas=0,
        )
        db_module.guardar_archivos(
            temp_db,
            esc1_id,
            [
                {
                    "ruta": "/test/a.txt",
                    "nombre": "a",
                    "extension": ".txt",
                    "tamanio": 100,
                    "hash_sha256": "hash_a",
                    "hash_computado": 1,
                },
                {
                    "ruta": "/test/b.txt",
                    "nombre": "b",
                    "extension": ".txt",
                    "tamanio": 200,
                    "hash_sha256": "hash_b",
                    "hash_computado": 1,
                },
            ],
        )

        esc2_id = db_module.guardar_escaneo(
            temp_db,
            rutas=["/test"],
            total_archivos=1,
            total_carpetas=0,
        )
        db_module.guardar_archivos(
            temp_db,
            esc2_id,
            [
                {
                    "ruta": "/test/a.txt",
                    "nombre": "a",
                    "extension": ".txt",
                    "tamanio": 100,
                    "hash_sha256": "hash_a",
                    "hash_computado": 1,
                },
            ],
        )

        diff = db_module.comparar_escaneos(temp_db, esc1_id, esc2_id)
        assert len(diff["eliminados"]) == 1
        assert diff["eliminados"][0]["ruta"] == "/test/b.txt"

    def test_detectar_movidos(self, temp_db):
        """Verificar que se detectan archivos movidos."""
        esc1_id = db_module.guardar_escaneo(
            temp_db,
            rutas=["/test"],
            total_archivos=1,
            total_carpetas=0,
        )
        db_module.guardar_archivos(
            temp_db,
            esc1_id,
            [
                {
                    "ruta": "/test/antiguo/a.txt",
                    "nombre": "a",
                    "extension": ".txt",
                    "tamanio": 100,
                    "hash_sha256": "hash_a",
                    "hash_computado": 1,
                },
            ],
        )

        esc2_id = db_module.guardar_escaneo(
            temp_db,
            rutas=["/test"],
            total_archivos=1,
            total_carpetas=0,
        )
        db_module.guardar_archivos(
            temp_db,
            esc2_id,
            [
                {
                    "ruta": "/test/nuevo/a.txt",
                    "nombre": "a",
                    "extension": ".txt",
                    "tamanio": 100,
                    "hash_sha256": "hash_a",
                    "hash_computado": 1,
                },
            ],
        )

        diff = db_module.comparar_escaneos(temp_db, esc1_id, esc2_id)
        assert len(diff["movidos"]) == 1
        assert diff["movidos"][0]["ruta_antigua"] == "/test/antiguo/a.txt"
        assert diff["movidos"][0]["ruta_nueva"] == "/test/nuevo/a.txt"


class TestEliminarEscaneo:
    """Pruebas para eliminacion de escaneos."""

    def test_eliminar_escaneo_exitoso(self, temp_db):
        """Verificar que se elimina un escaneo."""
        escaneo_id = db_module.guardar_escaneo(
            temp_db,
            rutas=["/test"],
            total_archivos=1,
            total_carpetas=0,
        )

        assert db_module.eliminar_escaneo(temp_db, escaneo_id) is True

        assert db_module.obtener_escaneo(temp_db, escaneo_id) is None

    def test_eliminar_escaneo_no_existente(self, temp_db):
        """Verificar que retorna False si no existe."""
        assert db_module.eliminar_escaneo(temp_db, 999) is False

    def test_eliminar_archivos_asociados(self, temp_db):
        """Verificar que al eliminar un escaneo, se eliminan sus archivos."""
        escaneo_id = db_module.guardar_escaneo(
            temp_db,
            rutas=["/test"],
            total_archivos=0,
            total_carpetas=0,
        )

        db_module.guardar_archivos(
            temp_db,
            escaneo_id,
            [
                {
                    "ruta": "/test/a.txt",
                    "nombre": "a",
                    "extension": ".txt",
                    "tamanio": 100,
                    "hash_sha256": "hash_a",
                    "hash_computado": 1,
                },
            ],
        )

        db_module.eliminar_escaneo(temp_db, escaneo_id)

        # Intentar obtener archivos despues de eliminar
        stored = db_module.obtener_archivos_escaneo(temp_db, escaneo_id)
        assert len(stored) == 0


class TestObtenerEspacioUsado:
    """Pruebas para obtener estadisticas de la base de datos."""

    def test_obtener_estadisticas(self, temp_db):
        """Verificar que se obtienen las estadisticas correctamente."""
        db_module.guardar_escaneo(
            temp_db,
            rutas=["/test"],
            total_archivos=5,
            total_carpetas=2,
        )

        stats = db_module.obtener_espacio_usado(temp_db)
        assert stats["total_escaneos"] == 1
        assert stats["total_archivos"] == 0  # No hemos guardado archivos
        assert stats["total_duplicados"] == 0
        assert stats["espacio_duplicado_bytes"] == 0
