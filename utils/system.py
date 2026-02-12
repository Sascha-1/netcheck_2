"""System command execution utilities.

Provides safe command execution with timeout protection.
Never uses shell=True to prevent command injection.
"""

import re
import shutil
import subprocess
from typing import Any

import config


def run_command(cmd: list[str]) -> str | None:
    """Execute system command safely.

    Security:
        - NEVER shell=True
        - Timeout: 10 seconds
        - No root privileges required

    Args:
        cmd: Command as list (e.g., ["ip", "addr", "show"])

    Returns:
        Command output (stripped) or None on error.
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=config.TIMEOUT_SECONDS,
            check=False,  # Don't raise on non-zero exit
            shell=False,  # CRITICAL: Never use shell=True
        )

        if result.returncode == 0:
            return result.stdout.strip()

        return None

    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        return None
    except (OSError, ValueError, RuntimeError) as e:
        # Catch specific subprocess-related exceptions
        del e  # Variable is intentionally unused
        return None


def command_exists(cmd: str) -> bool:
    """Check if command exists in PATH.

    Args:
        cmd: Command name (e.g., "ip", "lspci")

    Returns:
        True if command is available, False otherwise.
    """
    return shutil.which(cmd) is not None


def sanitize_for_log(value: Any) -> str:
    """Sanitize values before logging to prevent log injection.

    Removes:
        - Newlines
        - ANSI escape codes
        - Control characters

    Max length: 200 characters

    Args:
        value: Value to sanitize (any type, will be converted to string)

    Returns:
        Sanitized string safe for logging.
    """
    text = str(value)

    # Remove newlines
    text = text.replace("\n", " ").replace("\r", " ")

    # Remove ANSI escape codes
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)

    # Remove control characters
    text = "".join(c for c in text if c.isprintable() or c.isspace())

    # Truncate
    if len(text) > 200:
        text = text[:197] + "..."

    return text
