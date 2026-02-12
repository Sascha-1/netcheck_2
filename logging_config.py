"""Logging configuration for netcheck.

Provides colored console output and optional file logging.
Uses % formatting (PEP 391) for security.
"""

import logging
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """Add ANSI colors to log levels."""

    COLORS = {
        "DEBUG": "\033[96m",  # Cyan
        "INFO": "\033[92m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "CRITICAL": "\033[95m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors.

        Args:
            record: Log record to format

        Returns:
            Formatted log message with color codes.
        """
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


def setup_logging(
    verbose: bool = False,
    log_file: Path | None = None,
    use_colors: bool = True,
) -> None:
    """Configure logging.

    Args:
        verbose: Enable DEBUG level (default: WARNING+ only)
        log_file: Optional file output path
        use_colors: Always True (colors always enabled)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if verbose else logging.WARNING)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if verbose else logging.WARNING)

    if use_colors:
        console_handler.setFormatter(ColoredFormatter("%(levelname)s: %(message)s"))
    else:
        console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Suppress third-party loggers in default mode
    if not verbose:
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get logger for module.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance for the module.
    """
    return logging.getLogger(name)
