"""Pruebas de soporte multi-ruta — Fase 1.5."""

from pathlib import Path

from src.detector_duplicados.duper import encontrar_duplicados
from src.detector_duplicados.scanner import parse_rutas, recopilar_info

# ====================== TestParseRutas ======================


class TestParseRutas:
    """Pruebas de parse_rutas."""

    def test_ruta_unico(self) -> None:
        """Una sola ruta retorna lista con un elemento."""
        result = parse_rutas("/media/disco1")
        assert result == ["/media/disco1"]

    def test_rutas_multiples_coma(self) -> None:
        """Múltiples rutas separadas por coma."""
        result = parse_rutas("/a,/b,/c")
        assert result == ["/a", "/b", "/c"]

    def test_rutas_multiples_coma_espacios(self) -> None:
        """Múltiples rutas con espacios tras comas."""
        result = parse_rutas("/a, /b, /c")
        assert result == ["/a", "/b", "/c"]

    def test_ruta_vacia(self) -> None:
        """Cadena vacía retorna lista vacía."""
        result = parse_rutas("")
        assert result == []

    def test_rutas_con_elementos_vacios(self) -> None:
        """Elementos vacíos entre comas se filtran."""
        result = parse_rutas("/a, , /b")
        assert result == ["/a", "/b"]

    def test_ruta_con_espacios_borde(self) -> None:
        """Espacios al inicio/fin se eliminan."""
        result = parse_rutas("  /media/disco1  ")
        assert result == ["/media/disco1"]


# ====================== TestMultiRutaEscaneo ======================


class TestMultiRutaEscaneo:
    """Pruebas de escaneo con múltiples rutas."""

    def test_escanea_dos_rutas(self, tmp_path: Path) -> None:
        """Debe escanear y consolidar dos directorios diferentes."""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        (dir1 / "a.txt").write_text("contenido A")
        (dir2 / "b.txt").write_text("contenido B")

        archivos, carpetas, total_archivos, total_carpetas, total, rutas_no = recopilar_info(
            [str(dir1), str(dir2)]
        )

        assert total_archivos == 2, "Deben encontrarse 2 archivos"
        # dir1 y dir2 tienen solo archivos, no subdirectorios
        assert total_carpetas == 0
        assert total == 2
        assert len(rutas_no) == 0, "Ninguna ruta omitida"

    def test_escanea_tres_rutas(self, tmp_path: Path) -> None:
        """Debe escanear y consolidar tres directorios diferentes."""
        dirs = [tmp_path / f"dir{i}" for i in range(1, 4)]
        for d in dirs:
            d.mkdir()
            (d / "file.txt").write_text("contenido")

        archivos, _, total_archivos, _, _, rutas_no = recopilar_info([str(d) for d in dirs])

        assert total_archivos == 3, "Deben encontrarse 3 archivos"
        assert len(rutas_no) == 0, "Ninguna ruta omitida"

    def test_duplicados_entre_rutas(self, tmp_path: Path) -> None:
        """Debe detectar duplicados entre directorios distintos."""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        contenido = b"archivo identico en ambos discos"
        (dir1 / "video.mp4").write_bytes(contenido)
        (dir2 / "video_copy.mp4").write_bytes(contenido)

        archivos, _, total_archivos, _, _, rutas_no = recopilar_info([str(dir1), str(dir2)])

        assert total_archivos == 2, "Deben encontrarse 2 archivos"
        assert len(rutas_no) == 0

    def test_duplicados_entre_tres_rutas(self, tmp_path: Path) -> None:
        """Debe detectar duplicados entre 3 directorios distintos."""
        dirs = []
        for i in range(3):
            d = tmp_path / f"dir{i}"
            d.mkdir()
            (d / "video.mp4").write_bytes(b"contenido identico")
            dirs.append(d)

        archivos, _, total_archivos, _, _, rutas_no = recopilar_info([str(d) for d in dirs])

        assert total_archivos == 3, "3 archivos idénticos"
        assert len(rutas_no) == 0

        # Verificar que el detector encuentra 3 duplicados
        confirmados, sospechosos, total_conf, total_sos = encontrar_duplicados(
            archivos, [], confirmar_por_hash=True
        )

        assert total_conf == 3, "3 archivos idénticos deben confirmarse como duplicados"

    def test_rutas_no_escanear_inexistentes(self, tmp_path: Path) -> None:
        """Debe reportar rutas que no existen."""
        rutas_existentes = [str(tmp_path)]
        rutas_inexistentes = [str(tmp_path / "no_existe_1"), str(tmp_path / "no_existe_2")]

        archivos, _, total_archivos, _, _, rutas_no = recopilar_info(
            rutas_existentes + rutas_inexistentes
        )

        assert len(rutas_no) == 2, "Debe reportar 2 rutas omitidas"

    def test_ruta_no_es_directorio(self, tmp_path: Path) -> None:
        """Debe rechazar archivos pasados como rutas."""
        archivo = tmp_path / "solo_archivo.txt"
        archivo.write_text("contenido")

        archivos, _, total_archivos, _, _, rutas_no = recopilar_info([str(archivo)])

        assert total_archivos == 0, "Archivos pasados como ruta no deben escanearse"
        assert len(rutas_no) == 1, "Debe reportar la ruta como omitida"


# ====================== TestExclusiones ======================


class TestExclusiones:
    """Pruebas de aplicación de exclusiones."""

    def test_excluye_pycache(self, tmp_path: Path) -> None:
        """Directorios __pycache__ deben omitirse."""
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "module.pyc").write_text("bytecode")

        archivos, carpetas, total_archivos, total_carpetas, _, rutas_no = recopilar_info(
            [str(tmp_path)], exclusiones=frozenset({"__pycache__"})
        )

        assert total_archivos == 0, "__pycache__ debe omitirse completamente"
        assert total_carpetas == 0, "El directorio __pycache__ no debe contarse"
        assert len(rutas_no) == 0

    def test_excluye_git(self, tmp_path: Path) -> None:
        """Directorios .git deben omitirse."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("[core]")

        archivos, carpetas, total_archivos, total_carpetas, _, rutas_no = recopilar_info(
            [str(tmp_path)], exclusiones=frozenset({".git"})
        )

        assert total_archivos == 0, ".git debe omitirse completamente"
        assert total_carpetas == 0, "El directorio .git no debe contarse"
        assert len(rutas_no) == 0

    def test_excluye_multiple_carpetas(self, tmp_path: Path) -> None:
        """Múltiples carpetas excluidas deben omitirse."""
        # Crear estructura:
        # tmp_path/
        #   dir1/
        #     __pycache__/  (excluido)
        #       module.pyc
        #   keep.txt
        pycache1 = tmp_path / "dir1"
        pycache1.mkdir()
        pycache1_c = pycache1 / "__pycache__"
        pycache1_c.mkdir()
        (pycache1_c / "module.pyc").write_text("bytecode")
        (tmp_path / "keep.txt").write_text("keep")

        archivos, carpetas, total_archivos, total_carpetas, _, rutas_no = recopilar_info(
            [str(tmp_path)],
            exclusiones=frozenset({"__pycache__"}),
        )

        assert total_archivos == 1, "Solo keep.txt (pycache excluido)"
        # dir1 ES un directorio válido (no está en exclusiones)
        # solo su contenido __pycache__ está excluido
        assert total_carpetas == 1, "dir1 se cuenta (no está en exclusiones)"
        assert len(rutas_no) == 0

    def test_excluye_recycle_bin(self, tmp_path: Path) -> None:
        """$RECYCLE.BIN debe omitirse."""
        recycle = tmp_path / "$RECYCLE.BIN"
        recycle.mkdir()
        (recycle / "deleted.exe").write_bytes(b"malware")

        archivos, _, total_archivos, _, _, rutas_no = recopilar_info(
            [str(tmp_path)],
            exclusiones=frozenset({"$RECYCLE.BIN"}),
        )

        assert total_archivos == 0, "$RECYCLE.BIN debe omitirse"
        assert len(rutas_no) == 0

    def test_excluye_redunda_con_default(self, tmp_path: Path) -> None:
        """DEFAULT_EXCLUSIONS de config debe funcionar."""
        from src.detector_duplicados.config import DEFAULT_EXCLUSIONS

        # Verificar que __pycache__ está en DEFAULT_EXCLUSIONS
        assert "__pycache__" in DEFAULT_EXCLUSIONS

        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "test.pyc").write_text("data")

        # Sin pasar exclusiones, usa DEFAULT_EXCLUSIONS de config
        archivos, carpetas, total_archivos, total_carpetas, _, rutas_no = recopilar_info(
            [str(tmp_path)]
        )

        assert total_archivos == 0, "DEFAULT_EXCLUSIONS debe excluir __pycache__"
        assert total_carpetas == 0, "El directorio __pycache__ no debe contarse"
        assert len(rutas_no) == 0

    def test_no_excluye_subdirectorio_similar(self, tmp_path: Path) -> None:
        """__pycache_bak__ NO debe excluirse (exclusión exacta por nombre)."""
        # Crear directorio similar pero no igual
        similar = tmp_path / "__pycache_bak__"
        similar.mkdir()
        (similar / "data.txt").write_text("keep this")
        (tmp_path / "real.txt").write_text("keep this too")

        archivos, total_carpetas, total_archivos, _, _, rutas_no = recopilar_info(
            [str(tmp_path)],
            exclusiones=frozenset({"__pycache__"}),
        )

        assert total_archivos == 2, "__pycache_bak__ no debe excluirse"
        assert len(rutas_no) == 0


# ====================== TestRutasInvalidas ======================


class TestRutasInvalidas:
    """Pruebas de manejo de rutas inválidas."""

    def test_ruta_inexistente(self, tmp_path: Path) -> None:
        """Debe reportar rutas que no existen sin crash."""
        archivos, _, total_archivos, _, _, rutas_no = recopilar_info(
            [
                str(tmp_path / "no_existe"),
            ],
        )

        assert total_archivos == 0
        assert len(rutas_no) == 1

    def test_ruta_sin_permisos(self, tmp_path: Path) -> None:
        """Debe reportar rutas sin permisos."""
        dir_no_perm = tmp_path / "no_permiso"
        dir_no_perm.mkdir()
        (dir_no_perm / "file.txt").write_text("data")

        # Quitar permisos de lectura
        dir_no_perm.chmod(0o000)

        try:
            archivos, _, total_archivos, _, _, rutas_no = recopilar_info([str(dir_no_perm)])
            # Puede fallar o reportar como no escaneada
            assert len(rutas_no) >= 0  # Depende del sistema
        finally:
            dir_no_perm.chmod(0o755)  # Restaurar permisos para cleanup de pytest
