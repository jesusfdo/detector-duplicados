"""Pruebas mínimas del módulo scanner."""

from pathlib import Path

from src.detector_duplicados.scanner import recopilar_info


class TestRecopilarInfo:
    """Pruebas de recopilar_info sin interacción de terminal."""

    def test_escanea_archivos(self, tmp_path: Path) -> None:
        """Debe encontrar archivos en directorio."""
        tmp_path.mkdir(exist_ok=True)
        (tmp_path / "a.txt").write_text("contenido a")
        (tmp_path / "b.txt").write_text("contenido b")
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "c.txt").write_text("contenido c")

        archivos, carpetas, total_archivos, total_carpetas, total, rutas_no = recopilar_info(
            [str(tmp_path)], None
        )

        assert total_archivos == 3, "Deben encontrarse los 3 archivos"
        assert total_carpetas == 1, "Debe encontrarse la carpeta 'sub'"
        assert total == 4, "Total = archivos + carpetas"
        assert len(rutas_no) == 0, "Ninguna ruta omitida"

    def test_filtro_extension(self, tmp_path: Path) -> None:
        """Debe filtrar archivos por extensión."""
        (tmp_path / "a.mp4").write_text("video")
        (tmp_path / "b.txt").write_text("texto")
        (tmp_path / "c.mkv").write_text("video2")

        extensiones = {".mp4", ".mkv"}
        archivos, _, total_archivos, _, _, _ = recopilar_info([str(tmp_path)], extensiones)

        assert total_archivos == 2, "Solo deben encontrarse archivos .mp4 y .mkv"
        exts = {a["extension"] for a in archivos}
        assert exts == {".mp4", ".mkv"}

    def test_archivos_vacios(self, tmp_path: Path) -> None:
        """Debe retornar 0 archivos en directorio vacío."""
        archivos, carpetas, total_archivos, total_carpetas, total, rutas_no = recopilar_info(
            [str(tmp_path)], None
        )

        assert total_archivos == 0
        assert total_carpetas == 0
        assert total == 0
        assert len(rutas_no) == 0
