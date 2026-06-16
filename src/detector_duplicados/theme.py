"""Tema y estilos para la interfaz Rich.

Define paleta de colores, estilos de consola y configuracion visual
para toda la aplicacion.
"""

from rich.console import Console
from rich.theme import Theme

# Paleta de colores para el tema
THEME_COLORS = {
    "success": "#00FF41",  # Verde terminal
    "error": "#FF3333",  # Rojo
    "warning": "#FFB347",  # Naranja
    "info": "#4FC3F7",  # Azul claro
    "highlight": "#FFD700",  # Dorado
    "duplicate": "#FF6B6B",  # Rojo suave para duplicados
    "unique": "#4ECDC4",  # Turquesa para unicos
    "path": "#B388FF",  # Morado para rutas
    "hash": "#80CBC4",  # Verde azulado para hashes
    "date": "#808080",  # Gris para fechas
    "user": "#F0E68C",  # Amarillo para usuarios
}

# Tema de Rich
APP_THEME = Theme(THEME_COLORS)

# Consola configurada con el tema
console = Console(theme=APP_THEME)


def create_console() -> Console:
    """Crea una nueva consola con el tema de la app."""
    return Console(theme=APP_THEME)
