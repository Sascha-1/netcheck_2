"""ANSI color codes for terminal output.

Provides complete color palette and active color configuration.
All colors optimized for dark terminal backgrounds.
"""

from enum import StrEnum


# Complete Color Palette as StrEnum
class AllColors(StrEnum):
    """Complete ANSI color palette for dark terminal backgrounds.

    Using StrEnum provides:
    - Type safety and validation
    - Iteration support: for color in AllColors
    - IDE autocomplete
    - No pylint warnings

    Use these values to customize the Color enum below.
    """

    # Bright Colors (Best for dark backgrounds)
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Regular Colors (Good visibility)
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"

    # Special
    RESET = "\033[0m"

    # Orange-ish (via 256-color mode - may vary by terminal)
    ORANGE = "\033[38;5;208m"
    LIGHT_ORANGE = "\033[38;5;214m"


# Active Colors (Used in Table Display)
# CUSTOMIZE HERE: Change these to any color from AllColors above
class Color(StrEnum):
    """Active colors used for table display.

    To change colors: Replace the value with any from AllColors above.
    Example: GREEN = AllColors.BRIGHT_BLUE  # Use blue instead of green

    Current scheme optimized for dark terminal backgrounds.
    """

    GREEN = AllColors.BRIGHT_GREEN      # VPN OK
    CYAN = AllColors.BRIGHT_CYAN        # VPN carrier
    RED = AllColors.BRIGHT_RED          # Direct internet
    YELLOW = AllColors.BRIGHT_YELLOW    # Warning
    MAGENTA = AllColors.BRIGHT_MAGENTA  # Critical
    RESET = AllColors.RESET             # Reset (don't change)
