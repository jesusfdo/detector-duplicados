"""Detector de duplicados — escáner local de archivos con terminal Rich.

Una herramienta ligera para localizar, indexar y gestionar archivos
duplicados en discos locales y recursos compartidos.

Principio: terminal ligera, sin servicios externos.
"""

__version__ = "1.0.0"

# Fase 2: base de datos (exportar solo las funciones principales)
from .db import (
    comparar_escaneos,
    create_connection,
    create_tables,
    eliminar_escaneo,
    guardar_archivos,
    guardar_escaneo,
    guardar_grupos_duplicados,
    obtener_archivos_escaneo,
    obtener_duplicados,
    obtener_escaneo,
    obtener_escaneos,
    obtener_espacio_usado,
)

__all__ = [
    "__version__",
    "create_connection",
    "create_tables",
    "guardar_escaneo",
    "guardar_archivos",
    "guardar_grupos_duplicados",
    "obtener_escaneos",
    "obtener_escaneo",
    "obtener_archivos_escaneo",
    "obtener_duplicados",
    "comparar_escaneos",
    "eliminar_escaneo",
    "obtener_espacio_usado",
]
