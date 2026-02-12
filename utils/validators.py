"""Input validation utilities.

Provides validation for interface names, IP addresses, and other inputs.
Critical for security - prevents injection attacks.
"""

import ipaddress
import re


def validate_interface_name(name: str) -> bool:
    """Validate interface name (security check).

    Allowed characters: [a-zA-Z0-9._:@-]
    Note: @ added for veth pairs (eth0@if2)
    Max length: 64

    Args:
        name: Interface name to validate

    Returns:
        True if valid, False otherwise.
    """
    if not name or len(name) == 0:
        return False

    if len(name) > 64:
        return False

    # Allow: letters, digits, dot, colon, @, hyphen, underscore
    if not re.match(r"^[a-zA-Z0-9._:@-]+$", name):
        return False

    return True


def is_valid_ipv4(address: str | None) -> bool:
    """Validate IPv4 address.

    Args:
        address: IPv4 address string or None

    Returns:
        True if valid IPv4 address, False otherwise.
    """
    if not address:
        return False
    try:
        ipaddress.IPv4Address(address)
        return True
    except ValueError:
        return False


def is_valid_ipv6(address: str | None) -> bool:
    """Validate IPv6 address.

    Strips zone identifier (e.g., %eth0) before validation.
    Zone identifiers are used for link-local addresses.

    Args:
        address: IPv6 address string or None

    Returns:
        True if valid IPv6 address, False otherwise.
    """
    if not address:
        return False

    # Strip zone identifier (fe80::1%eth0 → fe80::1)
    address = address.split("%")[0]

    try:
        ipaddress.IPv6Address(address)
        return True
    except ValueError:
        return False


def is_valid_ip(address: str | None) -> bool:
    """Validate IPv4 or IPv6 address.

    Args:
        address: IP address string or None

    Returns:
        True if valid IPv4 or IPv6 address, False otherwise.
    """
    return is_valid_ipv4(address) or is_valid_ipv6(address)
