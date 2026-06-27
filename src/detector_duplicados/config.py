"""Configuración centralizada del proyecto.

Reemplaza las variables globales del script original.
"""

import getpass
import logging
import os
from pathlib import Path
from typing import Final

logger = logging.getLogger(__name__)

# Constantes — no mutables

EXTENSIONES_MULTIMEDIA: Final[frozenset[str]] = frozenset(
    {".mp4", ".mkv", ".avi", ".mpg", ".vob", ".dat", ".rmw"}
)

# Extensiones de subtítulos — se excluyen si existe un video con mismo nombre base
SUBTITLE_EXTENSIONS: Final[frozenset[str]] = frozenset({".srt", ".ass", ".vtt", ".sub", ".ssa"})

# Extensiones de video (para detectar si existe un video)
VIDEO_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".mpg", ".mpeg", ".webm", ".flv", ".m4v", ".ts"}
)

# Configuración de UI

PANEL_TITLE: Final[str] = "Bienvenido"
PANEL_TEXT: Final[str] = "### Escaner de Archivos DUPLICADOS ###"

# Configuración de escaneo — valores por defecto

DEFAULT_EXTENSION_FILTER = None  # None = todos los archivos

# Exclusiones por defecto — nombres de carpetas/archivos a omitir
DEFAULT_EXCLUSIONS: Final[frozenset[str]] = frozenset(
    {
        ".git",
        ".gitignore",
        ".svn",
        ".hg",
        "__pycache__",
        "node_modules",
        "$RECYCLE.BIN",
        "System Volume Information",
        "Recovery",
        "Windows",
        "boot",
        "pagefile.sys",
        "hiberfil.sys",
        "swapfile.sys",
    }
)

# Colores para UI (referenciados en ui.py y exporter.py)

COLOR_OK: Final[str] = "#00FF41"
COLOR_ERROR: Final[str] = "red"

# Rutas del proyecto

PROJECT_DIR: Final[Path] = Path(__file__).parent.parent.parent
LOG_DIR: Final[Path] = PROJECT_DIR / "logs"

# Perfiles de configuracion

DEFAULT_PERFIL: Final[str] = "default"

PERFILES_PREDEFINIDOS = {
    "default": {
        "politica": "keep_one_copy",
        "rutas_protegidas": [],
        "umbral_riesgo": 50,
        "accion_por_defecto": "papelera",
        "extensiones_exclusas": list(DEFAULT_EXCLUSIONS),
    },
    "agresivo": {
        "politica": "aggressive",
        "rutas_protegidas": ["/home/", "/media/", "/mnt/"],
        "umbral_riesgo": 30,
        "accion_por_defecto": "papelera",
        "extensiones_exclusas": list(DEFAULT_EXCLUSIONS),
    },
    "conservador": {
        "politica": "conservative",
        "rutas_protegidas": ["/home/", "/media/", "/mnt/", "/opt/"],
        "umbral_riesgo": 70,
        "accion_por_defecto": "papelera",
        "extensiones_exclusas": list(DEFAULT_EXCLUSIONS),
    },
}


def cargar_perfil(nombre: str = DEFAULT_PERFIL) -> dict:
    """Carga un perfil de configuracion.

    Args:
        nombre: Nombre del perfil (default, agresivo, conservador).

    Returns:
        Dict con la configuracion del perfil.
    """
    if nombre in PERFILES_PREDEFINIDOS:
        return PERFILES_PREDEFINIDOS[nombre]

    # Si no existe, intentar cargar desde archivo .toml
    perfil_path = PROJECT_DIR / "perfiles" / f"{nombre}.toml"
    if perfil_path.exists():
        try:
            import tomllib

            with open(perfil_path, "rb") as f:
                config = tomllib.load(f)
            return config
        except (tomllib.TOMLDecodeError, ImportError) as e:
            logger.warning(f"No se pudo cargar perfil {nombre} desde {perfil_path}: {e}")

    # Fallback al perfil default
    logger.warning(f"Perfil '{nombre}' no encontrado, usando 'default'")
    return PERFILES_PREDEFINIDOS[DEFAULT_PERFIL]


def get_current_user() -> str:
    """Retorna el nombre de usuario actual.

    Equivalente a getpass.getuser() pero encapsulado en función
    para que sea importable sin ejecutar.
    """
    try:
        return getpass.getuser()
    except Exception:
        return os.environ.get("USER", "usuario")
