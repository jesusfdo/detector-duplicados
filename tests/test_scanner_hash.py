"""Pruebas del módulo scanner — hashing SHA256."""

from pathlib import Path

from src.detector_duplicados.scanner import (
    agrupar_por_tamanio,
    calcular_hash_grupo,
    calcular_hash_sha256,
)


class TestAgruparPorTamanio:
    """Pruebas de agrupación por tamaño."""

    def test_agrupa_archivos_mismo_tamanio(self) -> None:
        """Archivos del mismo tamaño deben agruparse."""
        archivos = [
            {"ruta": "/a.txt", "tamanio": 1000},
            {"ruta": "/b.txt", "tamanio": 1000},
            {"ruta": "/c.txt", "tamanio": 1000},
        ]
        grupos = agrupar_por_tamanio(archivos)
        assert len(grupos) == 1
        assert 1000 in grupos
        assert len(grupos[1000]) == 3

    def test_filtra_tamanios_unicos(self) -> None:
        """Tamaños únicos deben filtrarse (no pueden ser duplicados)."""
        archivos = [
            {"ruta": "/a.txt", "tamanio": 1000},
            {"ruta": "/b.txt", "tamanio": 2000},
            {"ruta": "/c.txt", "tamanio": 3000},
        ]
        grupos = agrupar_por_tamanio(archivos)
        assert len(grupos) == 0

    def test_agrupa_mixed(self) -> None:
        """Solo agrupa grupos con >1 archivo."""
        archivos = [
            {"ruta": "/a.txt", "tamanio": 1000},
            {"ruta": "/b.txt", "tamanio": 1000},
            {"ruta": "/c.txt", "tamanio": 2000},
        ]
        grupos = agrupar_por_tamanio(archivos)
        assert len(grupos) == 1
        assert 1000 in grupos


class TestCalcularHash:
    """Pruebas de hashing SHA256."""

    def test_hash_deterministico(self, tmp_path: Path) -> None:
        """Mismo contenido → mismo hash."""
        archivo = tmp_path / "test.txt"
        archivo.write_bytes(b"contenido de prueba")

        hash1 = calcular_hash_sha256(str(archivo))
        hash2 = calcular_hash_sha256(str(archivo))
        assert hash1 == hash2

    def test_hash_diferente_para_diferente_contenido(self, tmp_path: Path) -> None:
        """Contenido diferente → hash diferente."""
        archivo_a = tmp_path / "a.txt"
        archivo_b = tmp_path / "b.txt"
        archivo_a.write_bytes(b"contenido A")
        archivo_b.write_bytes(b"contenido B")

        hash_a = calcular_hash_sha256(str(archivo_a))
        hash_b = calcular_hash_sha256(str(archivo_b))
        assert hash_a != hash_b

    def test_hash_grupo_mismos_archivos(self, tmp_path: Path) -> None:
        """Archivos idénticos → mismo hash."""
        contenido = b"contenido identico"
        archivo_a = tmp_path / "a.txt"
        archivo_b = tmp_path / "b.txt"
        archivo_a.write_bytes(contenido)
        archivo_b.write_bytes(contenido)

        archivos = [
            {"ruta": str(archivo_a)},
            {"ruta": str(archivo_b)},
        ]
        hashes = calcular_hash_grupo(archivos)
        assert hashes[str(archivo_a)] == hashes[str(archivo_b)]
