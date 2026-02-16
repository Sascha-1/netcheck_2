"""Tests for colors.py.

Tests ANSI color code definitions and enum structure.
"""

import pytest

from colors import Color, AllColors


class TestColorEnum:
    """Tests for Color enum."""

    def test_color_is_strenum(self) -> None:
        """Test Color inherits from StrEnum."""
        from enum import StrEnum
        assert issubclass(Color, StrEnum)

    def test_all_required_colors_defined(self) -> None:
        """Test all colors used in display are defined."""
        assert hasattr(Color, 'GREEN')
        assert hasattr(Color, 'CYAN')
        assert hasattr(Color, 'RED')
        assert hasattr(Color, 'YELLOW')
        assert hasattr(Color, 'MAGENTA')
        assert hasattr(Color, 'RESET')

    def test_color_values_are_ansi_codes(self) -> None:
        """Test color values are ANSI escape sequences."""
        assert Color.GREEN.startswith("\033[")
        assert Color.CYAN.startswith("\033[")
        assert Color.RED.startswith("\033[")
        assert Color.YELLOW.startswith("\033[")
        assert Color.MAGENTA.startswith("\033[")
        assert Color.RESET.value == "\033[0m"

    def test_color_values_are_strings(self) -> None:
        """Test all color values are strings."""
        assert isinstance(Color.GREEN, str)
        assert isinstance(Color.CYAN, str)
        assert isinstance(Color.RED, str)
        assert isinstance(Color.YELLOW, str)
        assert isinstance(Color.MAGENTA, str)
        assert isinstance(Color.RESET, str)

    def test_can_concatenate_with_text(self) -> None:
        """Test colors can be concatenated with text."""
        result = Color.GREEN + "test" + Color.RESET
        assert result == "\033[92mtest\033[0m"

    def test_can_use_in_fstring(self) -> None:
        """Test colors work in f-strings."""
        result = f"{Color.RED}error{Color.RESET}"
        assert "\033[" in result
        assert "error" in result
        assert result.endswith("\033[0m")


class TestAllColorsEnum:
    """Tests for AllColors complete palette."""

    def test_allcolors_is_strenum(self) -> None:
        """Test AllColors inherits from StrEnum."""
        from enum import StrEnum
        assert issubclass(AllColors, StrEnum)

    def test_bright_colors_defined(self) -> None:
        """Test bright colors are available."""
        assert hasattr(AllColors, 'BRIGHT_RED')
        assert hasattr(AllColors, 'BRIGHT_GREEN')
        assert hasattr(AllColors, 'BRIGHT_YELLOW')
        assert hasattr(AllColors, 'BRIGHT_BLUE')
        assert hasattr(AllColors, 'BRIGHT_MAGENTA')
        assert hasattr(AllColors, 'BRIGHT_CYAN')

    def test_regular_colors_defined(self) -> None:
        """Test regular colors are available."""
        assert hasattr(AllColors, 'RED')
        assert hasattr(AllColors, 'GREEN')
        assert hasattr(AllColors, 'YELLOW')
        assert hasattr(AllColors, 'BLUE')
        assert hasattr(AllColors, 'MAGENTA')
        assert hasattr(AllColors, 'CYAN')

    def test_styles_defined(self) -> None:
        """Test style codes are available."""
        assert hasattr(AllColors, 'BOLD')
        assert hasattr(AllColors, 'DIM')
        assert hasattr(AllColors, 'UNDERLINE')

    def test_reset_defined(self) -> None:
        """Test RESET is defined."""
        assert hasattr(AllColors, 'RESET')
        assert AllColors.RESET.value == "\033[0m"

    def test_can_iterate_colors(self) -> None:
        """Test can iterate over AllColors enum."""
        colors = list(AllColors)
        assert len(colors) > 0
        assert all(isinstance(c, str) for c in colors)

    def test_color_uses_allcolors(self) -> None:
        """Test active Color enum uses AllColors values."""
        # Color.GREEN should be one of the AllColors values
        assert Color.GREEN.value in [c.value for c in AllColors]


class TestColorUsage:
    """Tests for practical color usage."""

    def test_empty_string_concatenation(self) -> None:
        """Test concatenating with empty string."""
        result = Color.GREEN + "" + Color.RESET
        assert result == "\033[92m\033[0m"

    def test_multiline_text(self) -> None:
        """Test colors work with multiline text."""
        text = "line1\nline2"
        result = Color.RED + text + Color.RESET
        assert result.startswith("\033[")
        assert "line1\nline2" in result
        assert result.endswith("\033[0m")

    def test_nested_colors(self) -> None:
        """Test nested color usage."""
        # Outer color
        outer = Color.RED + "outer" + Color.RESET
        # Inner color (note: ANSI doesn't really nest, last wins)
        inner = Color.GREEN + "inner" + Color.RESET
        combined = outer + " " + inner
        
        assert "\033[91m" in combined  # RED
        assert "\033[92m" in combined  # GREEN
        assert "outer" in combined
        assert "inner" in combined

    @pytest.mark.parametrize("color", [
        Color.GREEN,
        Color.CYAN,
        Color.RED,
        Color.YELLOW,
        Color.MAGENTA,
    ])
    def test_all_active_colors_work(self, color) -> None:
        """Test all active colors can be used."""
        result = color + "test" + Color.RESET
        assert result.startswith("\033[")
        assert "test" in result
        assert result.endswith("\033[0m")

    def test_color_with_special_characters(self) -> None:
        """Test colors work with special characters."""
        special = "test!@#$%^&*()"
        result = Color.YELLOW + special + Color.RESET
        assert special in result
        assert result.startswith("\033[")

    def test_color_with_unicode(self) -> None:
        """Test colors work with unicode."""
        unicode_text = "café ñ 中文 🔥"
        result = Color.MAGENTA + unicode_text + Color.RESET
        assert unicode_text in result
        assert result.startswith("\033[")

    def test_reset_clears_color(self) -> None:
        """Test RESET code is correct."""
        assert Color.RESET.value == "\033[0m"

    def test_color_values_unique(self) -> None:
        """Test each active color has a unique ANSI code."""
        colors = [
            Color.GREEN,
            Color.CYAN,
            Color.RED,
            Color.YELLOW,
            Color.MAGENTA,
        ]
        # RESET is special, exclude it
        assert len(colors) == len(set(colors))
