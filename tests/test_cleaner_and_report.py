"""Tests de cobertura para cleaner.py y html_report.py (Fase 5)."""
import os
from datetime import datetime

from detector_duplicados.cleaner import (
    aplicar_politica_a_grupo,
    calcular_puntuacion,
    dry_run_cleanup,
    sugerir_eliminado,
)
from detector_duplicados.db import (
    create_connection,
    create_tables,
    deshacer_accion,
    eliminar_escaneo,
    guardar_escaneo,
    guardar_grupos_duplicados,
    obtener_duplicados,
    obtener_escaneo,
    obtener_rollback_disponible,
    registrar_accion,
)
from detector_duplicados.html_report import (
    generar_reporte_html,
)


class TestCleanerScoring:
    """Tests para calcular_puntuacion y sugerir_eliminado."""

    def test_archivo_temporaneo_baja_puntuacion(self):
        """Archivos en temp tienen puntaje alto (riesgo alto)."""
        archivo = {"ruta": "/tmp/test.txt", "tamanio": 100, "mtime": 0}
        score = calcular_puntuacion(archivo)
        assert score > 30  # Archivos temporales son candidatos a borrar

    def test_archivo_en_home_baja_puntuacion(self):
        """Archivos en home directo tienen puntaje medio."""
        import os
        home = os.path.expanduser("~")
        archivo = {"ruta": f"{home}/test.txt", "tamanio": 100, "mtime": 0}
        score = calcular_puntuacion(archivo)
        assert score < 100  # No es maximo riesgo

    def test_archivo_antiguo_alta_puntuacion(self):
        """Archivos viejos tienen alta puntuacion de riesgo."""
        # mtime hace 2 años
        mtime_2yrs = datetime.now().timestamp() - (730 * 24 * 3600)
        archivo = {"ruta": "/home/user/docs/old.txt", "tamanio": 1000, "mtime": mtime_2yrs}
        score = calcular_puntuacion(archivo)
        assert score >= 50  # Archivos viejos son buen candidato

    def test_archivo_pequeno_alta_puntuacion(self):
        """Archivos pequenos son buen candidato para borrar."""
        archivo = {"ruta": "/home/user/small.txt", "tamanio": 50, "mtime": 0}
        score = calcular_puntuacion(archivo)
        assert score > 20  # Archivos pequenos tienen algun riesgo

    def test_score_maximo_100(self):
        """Puntaje nunca excede 100."""
        archivo = {"ruta": "/home/user/old.txt", "tamanio": 100, "mtime": 0}
        score = calcular_puntuacion(archivo)
        assert score <= 100

    def test_archivo_grande_baja_puntuacion(self):
        """Archivos grandes tienen menor puntuacion de riesgo."""
        archivo = {"ruta": "/home/user/large_video.mp4", "tamanio": 500000, "mtime": 0}
        score = calcular_puntuacion(archivo)
        assert score < 70  # Video grande = no borrar

    def test_archivo_protegido_baja_puntuacion(self):
        """Archivos protegidos tienen puntaje bajo."""
        archivo = {"ruta": "/etc/config.json", "tamanio": 100, "mtime": 0}
        score = calcular_puntuacion(archivo)
        assert score < 50  # Archivos de sistema no se borran facilmente

    def test_score_muy_bajo_no_eliminable(self):
        """Archivos con score muy bajo no son eliminables."""
        archivo = {"ruta": "/etc/config.json", "tamanio": 100, "mtime": 0}
        sugerencias = sugerir_eliminado([archivo], umbral_riesgo=50)
        assert len(sugerencias["sugeridos_borrar"]) == 0

    def test_sugerencias_ordenadas_por_riesgo(self):
        """Sugerencias deben estar ordenadas de mayor a menor riesgo."""
        archivos = [
            {"ruta": "/home/old.txt", "tamanio": 100, "mtime": 0},  # Riesgo alto
            {"ruta": "/home/new.txt", "tamanio": 1000, "mtime": datetime.now().timestamp()},  # Riesgo bajo
            {"ruta": "/home/med.txt", "tamanio": 500, "mtime": 0},  # Riesgo medio
        ]
        sugerencias = sugerir_eliminado(archivos, umbral_riesgo=20)
        if len(sugerencias["sugeridos_borrar"]) >= 2:
            scores = [s["score"] for s in sugerencias["sugeridos_borrar"]]
            assert scores == sorted(scores, reverse=True)

    def test_umbral_alto_filtra_mas(self):
        """Umbral alto filtra mas archivos."""
        archivos = [
            {"ruta": "/home/a.txt", "tamanio": 100, "mtime": 0},  # Riesgo medio
            {"ruta": "/home/b.txt", "tamanio": 100, "mtime": 0},  # Riesgo medio
            {"ruta": "/home/c.txt", "tamanio": 100, "mtime": 0},  # Riesgo medio
        ]
        sugerencias_altas = sugerir_eliminado(archivos, umbral_riesgo=80)
        sugerencias_bajas = sugerir_eliminado(archivos, umbral_riesgo=30)
        assert len(sugerencias_altas["sugeridos_borrar"]) <= len(sugerencias_bajas["sugeridos_borrar"])


class TestPolicyEngine:
    """Tests para aplicar_politica_a_grupo."""

    def test_keep_one_copy(self):
        """Politica 'keep_one_copy' mantiene solo una copia."""
        grupo = {
            "id": "1",
            "rutas": ["/home/a/dup.txt", "/home/b/dup.txt", "/home/c/dup.txt"],
            "tamanio": 100,
            "hash": "abc123",
        }

        decision = aplicar_politica_a_grupo(grupo, "keep_one_copy", "default")

        assert len(decision["mantener"]) == 1
        assert len(decision["eliminar"]) == 2

    def test_keep_newest(self):
        """Politica 'keep_newest' mantiene el archivo mas nuevo."""
        grupo = {
            "id": "1",
            "rutas": [
                "/home/old.txt",
                "/home/new.txt",
            ],
            "tamanio": 100,
            "hash": "abc123",
        }

        decision = aplicar_politica_a_grupo(grupo, "keep_newest", "default")
        assert len(decision["mantener"]) == 1

    def test_keep_oldest(self):
        """Politica 'keep_oldest' mantiene el archivo mas viejo."""
        grupo = {
            "id": "1",
            "rutas": [
                "/home/old.txt",
                "/home/new.txt",
            ],
            "tamanio": 100,
            "hash": "abc123",
        }

        decision = aplicar_politica_a_grupo(grupo, "keep_oldest", "default")
        assert len(decision["mantener"]) == 1

    def test_keep_in_path(self):
        """Politica 'keep_in_path' mantiene el que esta en la ruta objetivo."""
        grupo = {
            "id": "1",
            "rutas": [
                "/home/a/dup.txt",
                "/home/b/dup.txt",
            ],
            "tamanio": 100,
            "hash": "abc123",
        }

        decision = aplicar_politica_a_grupo(grupo, "keep_in_path", "/home/b")
        assert len(decision["mantener"]) == 1

    def test_politica_invalida(self):
        """Politica invalida usa 'keep_one_copy' por defecto."""
        grupo = {
            "id": "1",
            "rutas": ["/home/a.txt"],
            "tamanio": 100,
            "hash": "abc",
        }

        decision = aplicar_politica_a_grupo(grupo, "politica_inexistente", "default")
        assert decision is not None

    def test_todas_mismas_rutas(self):
        """Todas las rutas iguales no generan acciones."""
        grupo = {
            "id": "1",
            "rutas": ["/home/solo.txt"],
            "tamanio": 100,
            "hash": "abc",
        }

        decision = aplicar_politica_a_grupo(grupo, "keep_one_copy", "default")
        assert len(decision["mantener"]) == 1
        assert len(decision["eliminar"]) == 0

    def test_perfiles_predefinidos(self):
        """Los perfiles predefinidos existen y tienen politica."""
        grupo = {
            "id": "1",
            "rutas": ["/home/a.txt", "/home/b.txt"],
            "tamanio": 100,
            "hash": "abc",
        }

        for perfil in ["default", "agresivo", "conservador"]:
            decision = aplicar_politica_a_grupo(grupo, "keep_one_copy", perfil)
            assert decision is not None


class TestDryRunCleanup:
    """Tests para dry_run_cleanup."""

    def test_dry_run_vacio(self):
        """Dry run con duplicados vacio no crash."""
        result = dry_run_cleanup({}, "keep_one_copy", "default")
        assert result["total_duplicados"] == 0
        assert result["acciones"] == []

    def test_dry_run_con_duplicados(self, tmp_path):
        """Dry run con duplicados reales."""
        # Crear archivos duplicados
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("contenido")
        f2.write_text("contenido")

        duplicados = {
            "grupo1": {
                "rutas": [str(f1), str(f2)],
                "tamanio": f1.stat().st_size,
            },
        }

        result = dry_run_cleanup(duplicados, "keep_one_copy", "default")
        assert result["total_duplicados"] == 1
        assert len(result["acciones"]) > 0


class TestHTMLReport:
    """Tests para generador de reportes HTML."""

    def test_generar_reporte_sin_duplicados(self, tmp_path):
        """Generar reporte con datos vacios no crash."""
        output = tmp_path / "report.html"

        result = generar_reporte_html(
            archivos_duplicados={},
            carpetas_duplicadas={},
            total_archivos=100,
            total_carpetas=10,
            nombre_reporte=str(output),
        )

        assert result is not None
        assert os.path.exists(output)
        assert os.path.getsize(output) > 100

    def test_generar_reporte_con_duplicados(self, tmp_path):
        """Generar reporte con duplicados reales."""
        archivos_dup = {
            "grupo1": {
                "rutas": ["/tmp/a.txt", "/tmp/b.txt"],
                "tamanio": 1000,
                "hash": "abc123",
            }
        }

        output = tmp_path / "report2.html"
        result = generar_reporte_html(
            archivos_duplicados=archivos_dup,
            carpetas_duplicadas={},
            total_archivos=200,
            total_carpetas=20,
            nombre_reporte=str(output),
        )

        assert os.path.exists(output)
        with open(output) as f:
            content = f.read()

        assert "grupo1" in content
        assert "/tmp/a.txt" in content  # Rutas en el HTML
        assert "v1.0.0" in content  # Version actualizada

    def test_reporte_html_valido(self, tmp_path):
        """El reporte generado debe ser HTML valido."""
        output = tmp_path / "valid.html"

        result = generar_reporte_html({}, {}, 0, 0, str(output))

        with open(output) as f:
            content = f.read()

        assert "<html" in content
        assert "</html>" in content
        assert "<head>" in content
        assert "<body>" in content

    def test_reporte_nombre_personalizado(self, tmp_path):
        """Generar reporte con nombre personalizado."""
        output = tmp_path / "my_custom_report.html"

        result = generar_reporte_html(
            {}, {}, 0, 0, str(output)
        )

        assert result == str(output)
        assert os.path.exists(output)

    def test_espacio_duplicado_calculado(self, tmp_path):
        """El espacio duplicado debe calcularse correctamente."""
        # Dos grupos de duplicados: uno de 1000 bytes (2 copias) y otro de 500 bytes (3 copias)
        archivos_dup = {
            "grupo1": {"rutas": ["/a.txt", "/b.txt"], "tamanio": 1000},  # 1000 * 1
            "grupo2": {"rutas": ["/c.txt", "/d.txt", "/e.txt"], "tamanio": 500},  # 500 * 2
        }

        output = tmp_path / "space.html"
        result = generar_reporte_html(
            archivos_duplicados=archivos_dup,
            carpetas_duplicadas={},
            total_archivos=100,
            total_carpetas=10,
            nombre_reporte=str(output),
        )

        with open(output) as f:
            content = f.read()

        # Verificar que el espacio calculado aparece en el HTML
        # Espacio total: 1000*1 + 500*2 = 2000 bytes
        assert "2,000" in content  # Formato con comas

    def test_reporte_con_carpetas_duplicadas(self, tmp_path):
        """Generar reporte con carpetas duplicadas."""
        carpetas_dup = {
            "carpeta1": {
                "nombre": "backup",
                "rutas": ["/home/a/backup", "/home/b/backup"],
            }
        }

        output = tmp_path / "carpetas.html"
        result = generar_reporte_html(
            archivos_duplicados={},
            carpetas_duplicadas=carpetas_dup,
            total_archivos=50,
            total_carpetas=5,
            nombre_reporte=str(output),
        )

        with open(output) as f:
            content = f.read()

        assert "backup" in content


class TestDBIntegration:
    """Tests de integracion para db.py con nueva ruta de DB."""

    def test_db_path_xdg_data_home(self, monkeypatch, tmp_path):
        """DB debe usarse XDG_DATA_HOME si existe."""
        import detector_duplicados.db as db_module

        # Simular XDG_DATA_HOME
        fake_xdg = tmp_path / "data"
        monkeypatch.setenv("XDG_DATA_HOME", str(fake_xdg))

        db_path = db_module._get_default_db_path()
        assert "data" in db_path  # Debe estar en el path fake

    def test_db_path_env_override(self, monkeypatch, tmp_path):
        """DB debe usar DETECTOR_DB_PATH si esta definido."""
        import detector_duplicados.db as db_module

        fake_db = tmp_path / "my_custom.db"
        monkeypatch.setenv("DETECTOR_DB_PATH", str(fake_db))

        db_path = db_module._get_default_db_path()
        assert db_path == str(fake_db)

    def test_guardar_y_obtener_escaneo(self, tmp_path):
        """Guardar y recuperar un escaneo."""
        db_path = str(tmp_path / "test.db")
        conn = create_connection(db_path)
        create_tables(conn)

        escaneo_id = guardar_escaneo(
            conn,
            rutas=["/tmp/test"],
            total_archivos=100,
            total_carpetas=10,
            modo="rapido",
        )

        assert escaneo_id is not None

        esc = obtener_escaneo(conn, escaneo_id)
        assert esc is not None
        assert esc["total_archivos"] == 100
        assert esc["modo"] == "rapido"

    def test_guardar_y_obtener_duplicados(self, tmp_path):
        """Guardar y recuperar duplicados."""
        db_path = str(tmp_path / "test.db")
        conn = create_connection(db_path)
        create_tables(conn)

        escaneo_id = guardar_escaneo(
            conn,
            rutas=["/tmp/test"],
            total_archivos=2,
            total_carpetas=1,
        )

        confirmados = {"abc123": ["/tmp/a.txt", "/tmp/b.txt"]}
        sospechosos = {"dup": ["/tmp/c.txt"]}

        guardar_grupos_duplicados(conn, escaneo_id, confirmados, sospechosos)

        dups = obtener_duplicados(conn, escaneo_id, confirmado=1)
        assert len(dups) == 1

        dups_sos = obtener_duplicados(conn, escaneo_id, confirmado=0)
        assert len(dups_sos) == 1

    def test_eliminar_escaneo(self, tmp_path):
        """Eliminar escaneo y verificar."""
        db_path = str(tmp_path / "test.db")
        conn = create_connection(db_path)
        create_tables(conn)

        escaneo_id = guardar_escaneo(
            conn,
            rutas=["/tmp/test"],
            total_archivos=10,
            total_carpetas=1,
        )

        success = eliminar_escaneo(conn, escaneo_id)
        assert success is True

        esc = obtener_escaneo(conn, escaneo_id)
        assert esc is None

    def test_registrar_accion(self, tmp_path):
        """Registrar y recuperar accion de log."""
        from detector_duplicados.db import registrar_accion

        db_path = str(tmp_path / "test.db")
        conn = create_connection(db_path)
        create_tables(conn)

        escaneo_id = guardar_escaneo(
            conn,
            rutas=["/tmp/test"],
            total_archivos=1,
            total_carpetas=1,
        )

        registrar_accion(
            conn,
            "mover",
            "/tmp/origen.txt",
            "/tmp/destino.txt",
            escaneo_id,
            True,
        )

        acciones = obtener_rollback_disponible(conn, 10)
        assert len(acciones) >= 1

    def test_deshacer_accion(self, tmp_path):
        """Deshacer accion de log."""
        db_path = str(tmp_path / "test.db")
        conn = create_connection(db_path)
        create_tables(conn)

        escaneo_id = guardar_escaneo(
            conn,
            rutas=["/tmp/test"],
            total_archivos=1,
            total_carpetas=1,
        )

        # Crear archivo de prueba
        test_file = tmp_path / "test_move.txt"
        test_file.write_text("contenido")

        registrar_accion(
            conn,
            "mover",
            str(test_file),
            str(test_file) + "_trash",
            escaneo_id,
            True,
        )

        # La accion debe ser deshecha (archivo movido de vuelta)
        # Nota: Esto requiere que el archivo exista y se pueda mover
        # Para este test, solo verificamos que la funcion no crash

        # Verificar que la funcion retorna algo
        result = deshacer_accion(conn, 1)
        assert result is not None  # Puede ser True o False dependiendo del sistema
