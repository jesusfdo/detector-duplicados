"""Test integracion: menu_interactivo maneja EOF sin crash."""
from unittest.mock import patch

from detector_duplicados.ui import menu_interactivo


class TestMenuInteractivoEOF:
    """5. FIX MODO INTERACTIVO - EOF handling."""

    def test_menu_eof_returns_0(self):
        """Ctrl+D (EOF) debe retornar 0 (salir), no crash."""
        opciones = ["A", "B", "C"]
        # Simula Ctrl+D (EOFError) en la primera llamada
        with patch("builtins.input", side_effect=EOFError):
            result = menu_interactivo(opciones)
        assert result == 0

    def test_menu_valid_input(self):
        """Input valido debe retornar el valor correcto."""
        opciones = ["A", "B", "C"]
        with patch("builtins.input", return_value="2"):
            result = menu_interactivo(opciones)
        assert result == 2

    def test_menu_invalid_then_valid(self):
        """Entrada invalida luego valida debe funcionar."""
        opciones = ["A", "B", "C"]
        with patch("builtins.input", side_effect=["abc", "1"]):
            result = menu_interactivo(opciones)
        assert result == 1

    def test_menu_eof_after_invalid(self):
        """EOF despues de entrada invalida debe retornar 0."""
        opciones = ["A", "B", "C"]
        with patch("builtins.input", side_effect=["abc", EOFError]):
            result = menu_interactivo(opciones)
        assert result == 0
