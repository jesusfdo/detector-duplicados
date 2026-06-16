"""Pruebas del módulo duper — detección dual (nombre + hash)."""

from src.detector_duplicados.duper import encontrar_duplicados


class TestEncontrarDuplicados:
    """Pruebas de encontrar_duplicados con datos controlados."""

    def test_detecta_duplicados_archivos_nombre(self) -> None:
        """Detecta archivos con mismo nombre en modo nombre (sin hash)."""
        archivos = [
            {"nombre": "video", "extension": ".mp4", "ruta": "/a/video.mp4"},
            {"nombre": "video", "extension": ".mp4", "ruta": "/b/video.mp4"},
        ]
        carpetas = []

        confirmados, sospechosos, total_conf, total_sos = encontrar_duplicados(
            archivos, carpetas, confirmar_por_hash=False
        )

        assert len(confirmados) == 0, "Sin hash no hay confirmados"
        assert total_sos == 1, "Debe detectar 1 sospechoso por nombre"
        assert "video" in sospechosos
        assert len(sospechosos["video"]) == 2

    def test_no_falsa_alarm_con_nombre_distinto(self) -> None:
        """Nombres distintos no deben marcarse como sospechosos."""
        archivos = [
            {"nombre": "video1", "extension": ".mp4", "ruta": "/a/video1.mp4"},
            {"nombre": "video2", "extension": ".mp4", "ruta": "/b/video2.mp4"},
        ]
        carpetas = []

        confirmados, sospechosos, total_conf, total_sos = encontrar_duplicados(
            archivos, carpetas, confirmar_por_hash=False
        )

        assert len(confirmados) == 0
        assert total_sos == 0, "Nombres distintos no generan sospechosos"

    def test_detecta_duplicados_carpetas(self) -> None:
        """Debe detectar carpetas con mismo nombre."""
        archivos = []
        carpetas = [
            {"nombre": "backup", "ruta": "/a/backup"},
            {"nombre": "backup", "ruta": "/b/backup"},
        ]

        confirmados, sospechosos, total_conf, total_sos = encontrar_duplicados(
            archivos, carpetas, confirmar_por_hash=False
        )

        assert len(confirmados) == 0
        assert total_sos == 1, "Debe detectar 1 carpeta sospechosa"
        assert "backup" in sospechosos
        assert len(sospechosos["backup"]) == 2

    def test_case_insensitive(self) -> None:
        """Duplicados deben detectarse sin importar mayúsculas/minúsculas."""
        archivos = [
            {"nombre": "Video", "extension": ".mp4", "ruta": "/a/Video.mp4"},
            {"nombre": "video", "extension": ".mp4", "ruta": "/b/video.mp4"},
        ]
        carpetas = []

        confirmados, sospechosos, _, total_sos = encontrar_duplicados(
            archivos, carpetas, confirmar_por_hash=False
        )

        assert len(confirmados) == 0
        assert total_sos == 1, "Video y video deben detectarse como sospechosos"
        assert "video" in sospechosos  # key está en lowercase


class TestDuplicadosPorHash:
    """Pruebas de detección confirmada por hash SHA256."""

    def test_hash_confirma_archivos_identicos(self, tmp_path):
        """Archivos idénticos con nombres diferentes → confirmados."""
        contenido = b"contenido identico para ambos archivos"
        archivo_a = tmp_path / "a" / "archivo1.mp4"
        archivo_b = tmp_path / "b" / "archivo2.mp4"
        archivo_a.parent.mkdir(parents=True, exist_ok=True)
        archivo_b.parent.mkdir(parents=True, exist_ok=True)
        archivo_a.write_bytes(contenido)
        archivo_b.write_bytes(contenido)

        tam = len(contenido)
        archivos = [
            {
                "nombre": "archivo1",
                "extension": ".mp4",
                "ruta": str(archivo_a),
                "tamanio": tam,
                "mtime": 0,
            },
            {
                "nombre": "archivo2",
                "extension": ".mp4",
                "ruta": str(archivo_b),
                "tamanio": tam,
                "mtime": 0,
            },
        ]
        carpetas = []

        confirmados, sospechosos, total_conf, total_sos = encontrar_duplicados(
            archivos, carpetas, confirmar_por_hash=True
        )

        assert total_conf == 2, "Deben confirmarse 2 archivos con mismo hash"
        assert len(confirmados) >= 1, "Debe haber al menos 1 grupo confirmado"

    def test_hash_diferente_para_archivos_diferentes(self, tmp_path):
        """Archivos con mismo nombre/tamaño pero contenido diferente → no confirmados."""
        archivo_a = tmp_path / "video.mp4"
        archivo_b = tmp_path / "video_copy.mp4"
        archivo_a.write_bytes(b"contenido A diferente")
        archivo_b.write_bytes(b"contenido B diferente")

        tam_a = len(b"contenido A diferente")
        tam_b = len(b"contenido B diferente")
        archivos = [
            {
                "nombre": "video",
                "extension": ".mp4",
                "ruta": str(archivo_a),
                "tamanio": tam_a,
                "mtime": 0,
            },
            {
                "nombre": "video_copy",
                "extension": ".mp4",
                "ruta": str(archivo_b),
                "tamanio": tam_b,
                "mtime": 0,
            },
        ]
        carpetas = []

        confirmados, sospechosos, total_conf, total_sos = encontrar_duplicados(
            archivos, carpetas, confirmar_por_hash=True
        )

        assert total_conf == 0, "Diferente contenido → sin confirmados por hash"

    def test_sin_falsos_positivos_hash(self, tmp_path):
        """Hash confirma solo lo que realmente es duplicado."""
        # Grupo 1: archivos idénticos (confirmados)
        contenido_igual = b"exactamente igual"
        a1 = tmp_path / "a1.txt"
        a2 = tmp_path / "b1.txt"
        a1.write_bytes(contenido_igual)
        a2.write_bytes(contenido_igual)

        # Grupo 2: mismo nombre pero diferente contenido (sospechosos solo)
        a3 = tmp_path / "a3.txt"
        a4 = tmp_path / "a4.txt"
        a3.write_bytes(b"diferente contenido 1")
        a4.write_bytes(b"diferente contenido 2")

        archivos = [
            {"nombre": "a", "extension": ".txt", "ruta": str(a1), "tamanio": 18, "mtime": 0},
            {"nombre": "b", "extension": ".txt", "ruta": str(a2), "tamanio": 18, "mtime": 0},
            {"nombre": "a", "extension": ".txt", "ruta": str(a3), "tamanio": 21, "mtime": 0},
            {"nombre": "a", "extension": ".txt", "ruta": str(a4), "tamanio": 21, "mtime": 0},
        ]
        carpetas = []

        confirmados, sospechosos, total_conf, total_sos = encontrar_duplicados(
            archivos, carpetas, confirmar_por_hash=True
        )

        # Grupo 1 (a,b): mismo tamaño, mismo hash → confirmado
        assert total_conf == 2, f"Grupo confirmado debe tener 2, tiene {total_conf}"

        # Grupo 2 (a3,a4): mismo nombre pero tamaños diferentes de a1/a2
        # → no confirmado por hash
        # pero ambos comparten nombre "a" → sospechosos
        assert total_sos >= 1, "Al menos un sospechoso por nombre compartido"
