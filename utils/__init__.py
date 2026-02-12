"""Utilities package for netcheck.

Provides system command execution, input validation, and text formatting.
"""

from .formatters import cleanup_device_name, cleanup_isp_name, shorten_text
from .system import command_exists, run_command, sanitize_for_log
from .validators import (
    is_valid_ip,
    is_valid_ipv4,
    is_valid_ipv6,
    validate_interface_name,
)

__all__ = [
    # System
    "run_command",
    "command_exists",
    "sanitize_for_log",
    # Validators
    "validate_interface_name",
    "is_valid_ipv4",
    "is_valid_ipv6",
    "is_valid_ip",
    # Formatters
    "cleanup_device_name",
    "cleanup_isp_name",
    "shorten_text",
]
