"""Módulo Watchdog: Monitoreo en tiempo real de carpetas.

Este módulo detecta cambios en carpetas (archivos nuevos/modificados)
y verifica si se estan creando duplicados en tiempo real.
NO actua automaticamente; solo alerta y guarda un log.
"""

import logging
import os
import time
from pathlib import Path

from .scanner import calcular_hash_sha256
from .theme import console

logger = logging.getLogger(__name__)

# Configuracion por defecto del watchdog
DEFAULT_POLLING_INTERVAL = 2.0  # Segundos entre verificaciones
DEFAULT_MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB (maximo por archivo)


class WatchdogMonitor:
    """Monitor de carpetas que detecta duplicados en tiempo real.

    Attributes:
        rutas: Listas de rutas a monitorear.
        interval: Intervalo en segundos entre verificaciones.
        index: Base de datos en memoria de archivos conocidos.
        alert_log: Archivo de log para alertas.
    """

    def __init__(
        self,
        rutas: list[str],
        interval: float = DEFAULT_POLLING_INTERVAL,
        alert_log: str = "~/.local/share/detector_duplicados/watchdog.log",
        max_file_size: int = DEFAULT_MAX_FILE_SIZE,
    ):
        self.rutas = [Path(r) for r in rutas]
        self.interval = interval
        self.alert_log = os.path.expanduser(alert_log)
        self.max_file_size = max_file_size

        # Index de archivos conocidos: {hash: [ruta_str]}
        self.index: dict[str, list[str]] = {}

        # Estado de ejecucion
        self.running = False

        # Crear directorio de log si no existe
        os.makedirs(os.path.dirname(self.alert_log), exist_ok=True)

        console.print("[highlight]Monitor iniciado[/]")
        console.print(f"  Rutas: {[str(r) for r in self.rutas]}")
        console.print(f"  Intervalo: {self.interval}s")

    def _cargar_index(self) -> None:
        """Carga el index desde el archivo de persistencia si existe."""
        import json  # Importar aqui para evitar errores de lint

        index_file = os.path.expanduser("~/.local/share/detector_duplicados/index.db")
        if os.path.exists(index_file):
            try:
                with open(index_file) as f:
                    data = json.load(f)
                    self.index = {k: v for k, v in data.items() if isinstance(v, list)}
                console.print("[info]Index cargado desde archivo.[/]")
            except (OSError, json.JSONDecodeError) as e:
                console.print(f"[warning]Error cargando index: {e}[/]")
                self.index = {}
        else:
            console.print("[info]Creando nuevo index.[/]")
            self.index = {}

    def _guardar_index(self) -> None:
        """Guarda el index en el archivo de persistencia."""
        import json

        index_file = os.path.expanduser("~/.local/share/detector_duplicados/index.db")
        try:
            with open(index_file, "w") as f:
                json.dump(self.index, f, indent=2)
        except OSError as e:
            console.print(f"[error]Error guardando index: {e}[/]")

    def _verificar_duplicados(self, ruta: Path) -> str | None:
        """Verifica si un archivo es duplicado de algun otro en el index.

        Args:
            ruta: Ruta del archivo a verificar.

        Returns:
            Hash del archivo si es duplicado, None si es unico.
        """
        try:
            stat = ruta.stat()

            # Verificar tamaño
            if stat.st_size > self.max_file_size:
                return None

            # Calcular hash
            file_hash = calcular_hash_sha256(str(ruta))
            if file_hash is None:
                return None

            # Verificar si ya existe en el index
            if file_hash in self.index:
                for existing_path in self.index[file_hash]:
                    if existing_path != str(ruta.resolve()):
                        # Es un duplicado
                        console.print("\n[duplicate]DUPLICADO DETECTADO:[/]", style="bold")
                        console.print(f"  Original: [path]{existing_path}[/]")
                        console.print(f"  Nuevo: [path]{ruta}[/]")
                        console.print(f"  Tamaño: [info]{stat.st_size:,} bytes[/]")
                        return file_hash

            # Agregar al index
            if file_hash not in self.index:
                self.index[file_hash] = []
            self.index[file_hash].append(str(ruta.resolve()))

            return None

        except (OSError, PermissionError) as e:
            console.print(f"[warning]Error verificando {ruta}: {e}[/]")
            return None

    def _alertar_duplicado(self, file_hash: str, rutas_duplicadas: list[str]) -> None:
        """Guarda la alerta en el archivo de log."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        alerta = f"[{timestamp}] DUPLICADO: {rutas_duplicadas[0]} | {rutas_duplicadas[1]}"

        try:
            with open(self.alert_log, "a") as f:
                f.write(alerta + "\n")
        except OSError as e:
            console.print(f"[error]Error guardando alerta: {e}[/]")

    def iniciar(self) -> None:
        """Inicia el monitoreo de las rutas configuradas."""
        console.print("[success]Monitor iniciado en las rutas configuradas.[/]")
        console.print("[warning]Presione Ctrl+C para detener.[/]")

        self._cargar_index()
        self.running = True

        try:
            while self.running:
                for ruta in self.rutas:
                    if not ruta.exists():
                        continue

                    # Escanear archivos nuevos/modificados
                    for archivo in ruta.rglob("*"):
                        if archivo.is_file():
                            # Verificar si es duplicado
                            file_hash = self._verificar_duplicados(archivo)
                            if file_hash is not None:
                                self._alertar_duplicado(file_hash, self.index[file_hash])

                # Esperar antes de la siguiente verificacion
                time.sleep(self.interval)

        except KeyboardInterrupt:
            console.print("[info]Monitor deteniéndose...[/]")
        finally:
            self.running = False
            self._guardar_index()
            console.print("[success]Monitor detenido. Index guardado.[/]")

    def detener(self) -> None:
        """Detiene el monitoreo."""
        self.running = False
        console.print("[warning]Monitor detenido manualmente.[/]")

    def ver_alertas(self, limit: int = 10) -> list[str]:
        """Lee las ultimas alertas del log."""
        if not os.path.exists(self.alert_log):
            return []

        with open(self.alert_log) as f:
            lines = f.readlines()
            return lines[-limit:]

    def limpiar_alertas(self) -> None:
        """Limpia el archivo de alertas."""
        if os.path.exists(self.alert_log):
            os.remove(self.alert_log)
            console.print("[success]Alertas limpiadas.[/]")
        else:
            console.print("[info]No hay alertas para limpiar.[/]")

    def ver_estado(self) -> None:
        """Muestra el estado actual del monitor."""

        console.print("\n[bold highlight]=== Estado del Monitor ===[/]\n")
        console.print(f"  Ejecutando: {'Si' if self.running else 'No'}")
        console.print(f"  Archivos indexados: {sum(len(v) for v in self.index.values())}")
        console.print(f"  Grupos unicos: {len(self.index)}")
        console.print(
            f"  Alertas acumuladas: {sum(len(v) - 1 for v in self.index.values() if len(v) > 1)}"
        )


def iniciar_watchdog(rutas: list[str], interval: float = 5.0) -> None:
    """Funcion de conveniencia para iniciar el monitor."""
    console.print("[bold highlight]=== Iniciando Monitor de Duplicados ===[/]\n")

    monitor = WatchdogMonitor(
        rutas=rutas,
        interval=interval,
    )
    monitor.iniciar()
