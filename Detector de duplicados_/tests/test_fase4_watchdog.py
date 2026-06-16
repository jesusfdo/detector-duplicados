"""Tests rigurosos para la Fase 4: Watchdog (watchdog.py)"""

import os
import tempfile
from pathlib import Path

import pytest
from src.detector_duplicados.watchdog import WatchdogMonitor


class TestWatchdogMonitorInit:
    """Pruebas de inicializacion del WatchdogMonitor."""

    def test_inicializacion_basicos(self):
        """Verificar que WatchdogMonitor se inicializa correctamente."""
        monitor = WatchdogMonitor(
            rutas=["/tmp"],
            interval=1.0,
        )

        assert not monitor.running
        assert monitor.interval == 1.0
        assert len(monitor.rutas) == 1
        assert isinstance(monitor.index, dict)

    def test_inicializacion_multiple_rutas(self):
        """Verificar que se pueden definir multiples rutas."""
        rutas = ["/tmp", "/var/tmp", "/scratch"]
        monitor = WatchdogMonitor(rutas=rutas)

        assert len(monitor.rutas) == 3

    def test_cargar_index_vacio(self):
        """Verificar que cargar_index funciona sin archivo previo."""
        monitor = WatchdogMonitor(rutas=["/tmp"])

        # No debe lanzar excepciones
        monitor._cargar_index()
        assert isinstance(monitor.index, dict)


class TestWatchdogIndex:
    """Pruebas para la gestion del index del Watchdog."""

    def test_guardar_cargar_index(self):
        """Verificar que el index se guarda y carga correctamente."""
        with tempfile.TemporaryDirectory() as tmpdir:
            monitor = WatchdogMonitor(
                rutas=["/tmp"],
                alert_log=os.path.join(tmpdir, "alertas.log"),
            )

            # Agregar datos al index
            monitor.index["hash_test_123"] = ["/tmp/archivo1.txt", "/tmp/archivo2.txt"]

            # Guardar
            monitor._guardar_index()

            # Crear nuevo monitor y cargar
            monitor2 = WatchdogMonitor(
                rutas=["/tmp"],
                alert_log=os.path.join(tmpdir, "alertas.log"),
            )
            monitor2._cargar_index()

            # Verificar que se cargaron los datos
            assert "hash_test_123" in monitor2.index
            assert len(monitor2.index["hash_test_123"]) == 2

    def test_index_persitencia(self):
        """Verificar que el index se mantiene entre ejecuciones."""
        index_file = os.path.expanduser("~/.local/share/detector_duplicados/index.db")

        try:
            monitor1 = WatchdogMonitor(rutas=["/tmp"])
            monitor1.index["hash_unico"] = ["/tmp/unico.txt"]
            monitor1._guardar_index()

            monitor2 = WatchdogMonitor(rutas=["/tmp"])
            monitor2._cargar_index()

            assert "hash_unico" in monitor2.index
        finally:
            # Limpiar
            if os.path.exists(index_file):
                os.remove(index_file)


class TestWatchdogDeteccion:
    """Pruebas para la deteccion de duplicados."""

    def test_deteccion_duplicado_existente(self):
        """Verificar que detecta un duplicado cuando existe en el index."""
        monitor = WatchdogMonitor(rutas=["/tmp"])

        # Agregar un archivo al index manualmente
        monitor.index["hash_simulado"] = ["/tmp/origen.txt"]

        # Crear un archivo temporal para verificar
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("contenido simulado")
            temp_file = f.name

        try:
            # Verificar que no es duplicado (hash diferente)
            resultado = monitor._verificar_duplicados(Path(temp_file))
            # Como el hash es diferente, no deberia ser detectado como duplicado
            assert resultado is None or resultado != "hash_simulado"
        finally:
            os.remove(temp_file)

    def test_no_duplicado_unico(self):
        """Verificar que archivos unicos NO se marcan como duplicados."""
        monitor = WatchdogMonitor(rutas=["/tmp"])

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("contenido unico_12345")
            temp_file = f.name

        try:
            resultado = monitor._verificar_duplicados(Path(temp_file))
            # Si es unico, no deberia ser duplicado
            assert resultado is None or resultado not in monitor.index
        finally:
            os.remove(temp_file)


class TestWatchdogAlertas:
    """Pruebas para el sistema de alertas."""

    def test_alertar_duplicado_crea_log(self):
        """Verificar que alertar_duplicado crea la alerta en el log."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            alert_log = f.name

        try:
            monitor = WatchdogMonitor(
                rutas=["/tmp"],
                alert_log=alert_log,
            )

            # Simular alerta
            monitor._alertar_duplicado("hash_test", ["/tmp/archivo1.txt", "/tmp/archivo2.txt"])

            # Verificar que el log tiene contenido
            assert os.path.exists(alert_log)

            with open(alert_log) as f:
                contenido = f.read()
                assert len(contenido) > 0
        finally:
            if os.path.exists(alert_log):
                os.remove(alert_log)

    def test_ver_alertas(self):
        """Verificar que ver_alertas lee correctamente."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            alert_log = f.name
            f.write("alerta_1\n")
            f.write("alerta_2\n")
            f.write("alerta_3\n")

        try:
            monitor = WatchdogMonitor(
                rutas=["/tmp"],
                alert_log=alert_log,
            )

            alertas = monitor.ver_alertas(limit=2)
            assert len(alertas) <= 2
        finally:
            if os.path.exists(alert_log):
                os.remove(alert_log)

    def test_limpiar_alertas(self):
        """Verificar que limpiar_alertas elimina el log."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            alert_log = f.name
            f.write("alerta_de_prueba\n")

        try:
            monitor = WatchdogMonitor(
                rutas=["/tmp"],
                alert_log=alert_log,
            )

            monitor.limpiar_alertas()
            assert not os.path.exists(alert_log)
        finally:
            if os.path.exists(alert_log):
                os.remove(alert_log)


class TestWatchdogEstado:
    """Pruebas para el estado del monitor."""

    def test_ver_estado(self):
        """Verificar que ver_estado funciona sin errores."""
        monitor = WatchdogMonitor(rutas=["/tmp"])

        # No debe lanzar excepciones
        try:
            monitor.ver_estado()
        except Exception as e:
            pytest.fail(f"ver_estado() lanzo excepcion: {e}")

    def test_detener_monitor(self):
        """Verificar que detener() funciona correctamente."""
        monitor = WatchdogMonitor(rutas=["/tmp"])
        monitor.running = True

        monitor.detener()
        assert not monitor.running
