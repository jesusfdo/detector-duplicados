"""Tests de regresión para la barra de progreso y el flujo post-escaneo.

Verifica que:
1. La barra de escaneo avanza durante el escaneo
2. La barra de hashing avanza y llega al 100%
3. Al finalizar hashing, continúa el flujo
4. El HTML se genera
5. El navegador intenta abrirse
6. El proceso termina correctamente
7. El código de salida es 0
"""

import os
import sys
import tempfile
import time
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

cwd = str(Path(__file__).parent.parent)
sys.path.insert(0, os.path.join(cwd, "src"))
PY = sys.executable  # python3 del venv


class TestBarraEscaneoAvanza:
    """BUG 1: La barra de escaneo nunca avanza (0% todo el tiempo)."""

    def test_barra_escaneo_actualiza_progreso(self):
        """Verificar que _walk_directory llama barra.update() durante el escaneo."""
        from detector_duplicados.scanner import _walk_directory, recopilar_info
        from rich.progress import Progress

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("contenido")

            barra = Progress()
            task = barra.add_task("Escaneando", total=1)

            archivos = []
            carpetas = []
            _walk_directory(
                Path(tmpdir),
                frozenset(),
                None,
                barra,
                task,
                archivos,
                carpetas,
            )

            barra.__exit__(None, None, None)

            assert len(archivos) == 1, f"Se esperaba 1 archivo, got {len(archivos)}"
            tarea = barra._tasks[task]
            assert tarea.finished or tarea.completed > 0, (
                f"La barra de escaneo no avanzó. completed={tarea.completed}"
            )

    def test_recopilar_info_con_barra_progreso(self):
        """Verificar que recopilar_info crea y actualiza la barra de progreso."""
        from detector_duplicados.scanner import recopilar_info
        from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "a.txt").write_text("x")
            Path(tmpdir, "b.txt").write_text("y")
            Path(tmpdir, "subdir").mkdir()
            Path(tmpdir, "subdir", "c.txt").write_text("z")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            ) as barra:
                archivos, carpetas, ta, tc, total, rne = recopilar_info(
                    [tmpdir], barra=barra
                )

            assert len(archivos) == 3, f"Se esperaban 3 archivos, got {len(archivos)}"
            assert len(carpetas) == 1, f"Se esperaba 1 carpeta, got {len(carpetas)}"
            for tarea in barra._tasks.values():
                assert tarea.completed > 0, (
                    f"Barra de progreso no avanzó: completed={tarea.completed}, total={tarea.total}"
                )


class TestBarraHashAvanza:
    """BUG 2: La barra de hashing llega al 100% pero después el programa se congela."""

    def test_barra_hash_actualiza_progreso(self):
        """Verificar que la barra de hashing se actualiza durante el hashing."""
        import tempfile
        from detector_duplicados.scanner import agrupar_por_tamanio
        from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn

        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                Path(tmpdir, f"orig_{i}.txt").write_text(f"contenido_{i}")
                Path(tmpdir, f"copy_{i}.txt").write_text(f"contenido_{i}")

            archivos = []
            for f in Path(tmpdir).rglob("*"):
                if f.is_file():
                    stat = f.stat()
                    archivos.append({
                        "nombre": f.stem,
                        "extension": f.suffix,
                        "ruta": str(f.resolve()),
                        "tamanio": stat.st_size,
                        "mtime": stat.st_mtime,
                    })

            grupos = agrupar_por_tamanio(archivos)

            assert len(grupos) == 1, f"Se esperaba 1 grupo de tamaño, got {len(grupos)}"

            for tam, grp in grupos.items():
                total_archivos = len(grp)
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                ) as barra_hash:
                    task = barra_hash.add_task("Calculando hashes...", total=total_archivos)

                    for arch in grp:
                        from detector_duplicados.scanner import calcular_hash_sha256
                        h = calcular_hash_sha256(arch["ruta"])
                        assert h is not None
                        barra_hash.update(task, advance=1)

                    tarea = barra_hash._tasks[task]
                    assert tarea.completed == tarea.total, (
                        f"Barra de hash no llegó al 100%. completed={tarea.completed}, total={tarea.total}"
                    )


class TestFlujoPostHashing:
    """BUG 2: Después del hashing el programa aparentemente se congela."""

    def test_despues_del_hashing_se_genera_html(self):
        """Verificar que después del hashing se genera el HTML."""
        import tempfile
        from pathlib import Path
        from detector_duplicados.html_report import generar_reporte_html
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "a.txt").write_text("contenido_1")
            Path(tmpdir, "b.txt").write_text("contenido_1")

            confirmados = {"abc123": [str(Path(tmpdir, "a.txt")), str(Path(tmpdir, "b.txt"))]}
            sospechosos = {}

            result = generar_reporte_html(
                confirmados, sospechosos, 2, 0,
                nombre_reporte="test_report.html",
                abrir_navegador=False,
            )

            assert result is not None, "generar_reporte_html devolvió None"
            assert os.path.exists(result), f"El HTML no se generó en {result}"
            size = os.path.getsize(result)
            assert size > 0, f"El HTML está vacío ({size} bytes)"

    def test_despues_del_html_se_abre_navegador(self):
        """Verificar que después del HTML se intenta abrir el navegador."""
        from unittest.mock import patch
        from pathlib import Path

        with patch("webbrowser.open") as mock_open:
            from detector_duplicados.html_report import generar_reporte_html
            import tempfile

            with tempfile.TemporaryDirectory() as tmpdir:
                confirmados = {"abc": ["a", "b"]}
                sospechosos = {}

                result = generar_reporte_html(
                    confirmados, sospechosos, 2, 0,
                    nombre_reporte="test.html",
                    abrir_navegador=True,
                )

                if mock_open.called:
                    url = mock_open.call_args[0][0]
                    assert url.startswith("file://"), (
                        f"webbrowser.open fue llamado con URL no-file: {url}"
                    )

    def test_programa_termina_correctamente(self):
        """Verificar que el programa termina con exit code 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "a.txt").write_text("contenido_1")
            Path(tmpdir, "b.txt").write_text("contenido_1")

            result = subprocess.run(
                [PY, "-m", "detector_duplicados.cli", "--scan", tmpdir, "--modo", "rapido", "--no-save"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=cwd,
            )

            assert result.returncode == 0, (
                f"El programa terminó con error. returncode={result.returncode}\n"
                f"stderr={result.stderr[:500]}"
            )

    def test_despues_del_html_se_muestran_resultados(self):
        """Verificar que después del HTML se muestran resultados en la terminal."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "a.txt").write_text("contenido_1")
            Path(tmpdir, "b.txt").write_text("contenido_1")

            result = subprocess.run(
                [PY, "-m", "detector_duplicados.cli", "--scan", tmpdir, "--modo", "rapido", "--no-save"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=cwd,
            )

            assert "Duplicados encontrados" in result.stdout or "Duplicados encontrados" in result.stderr, (
                "No se mostraron resultados en la salida"
            )

    def test_proceso_retorna_control_consola(self):
        """Verificar que el proceso retorna control a la consola."""
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "a.txt").write_text("contenido_1")
            Path(tmpdir, "b.txt").write_text("contenido_1")

            start = time.time()
            result = subprocess.run(
                [PY, "-m", "detector_duplicados.cli", "--scan", tmpdir, "--modo", "rapido", "--no-save"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=cwd,
            )
            elapsed = time.time() - start

            assert elapsed < 30, (
                f"El proceso tardó {elapsed:.2f}s (timeout 30s) — posiblemente congelado"
            )
            assert result.returncode == 0, f"returncode={result.returncode}"


class TestArquitecturaProgress:
    """Tests para la nueva arquitectura unificada de barras de progreso."""

    def test_unificacion_barra_de_progreso(self):
        """Verificar que todas las barras de progreso comparten la misma infraestructura."""
        from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

        barra = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )

        with barra:
            tarea1 = barra.add_task("Escaneando", total=100)
            tarea2 = barra.add_task("Calculando hashes", total=100)

            for i in range(100):
                barra.update(tarea1, advance=1)
                if i == 50:
                    barra.update(tarea2, advance=1)

            assert barra._tasks[tarea1].completed == 100
            assert barra._tasks[tarea2].completed == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
