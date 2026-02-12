"""Configuration constants for netcheck.

All configurable values stored here for easy customization.
Single source of truth for all constants and configuration.
"""

from enum import IntEnum, StrEnum

# API Configuration
IPINFO_URL: str = "https://ipinfo.io/json"
IPINFO_IPv6_URL: str = "https://v6.ipinfo.io/json"

# Timeout and Retry
TIMEOUT_SECONDS: int = 10
RETRY_ATTEMPTS: int = 3  # IPv4 only
RETRY_BACKOFF_FACTOR: float = 1.0

# Public DNS Servers (ONLY these three providers)
# These are used to distinguish between "leaking to ISP" (bad) and
# "using public DNS" (suboptimal but not leaking to ISP).
# This helps users understand their privacy posture:
#   - ISP DNS (192.168.1.1): ISP sees all DNS queries → "LEAK" status
#   - Public DNS (1.1.1.1): Third-party sees queries, NOT your ISP → "PUBLIC" status
#   - VPN DNS (ProtonVPN): VPN provider sees queries (trusted) → "OK" status
PUBLIC_DNS_SERVERS: set[str] = {
    # Cloudflare
    "1.1.1.1",
    "1.0.0.1",
    "2606:4700:4700::1111",
    "2606:4700:4700::1001",
    # Google
    "8.8.8.8",
    "8.8.4.4",
    "2001:4860:4860::8888",
    "2001:4860:4860::8844",
    # Quad9
    "9.9.9.9",
    "149.112.112.112",
    "2620:fe::fe",
    "2620:fe::9",
}

# Required System Commands
REQUIRED_COMMANDS: list[str] = [
    "ip",
    "lspci",
    "lsusb",
    "ethtool",
    "resolvectl",
    "ss",
]

# USB Tether Drivers
USB_TETHER_DRIVERS: list[str] = [
    "cdc_ether",
    "cdc_mbim",
    "cdc_ncm",
    "ipheth",
    "rndis_host",
]

# Interface Type Patterns
INTERFACE_TYPE_PATTERNS: dict[str, str] = {
    "lo": "loopback",
    "eth": "ethernet",
    "en": "ethernet",
    "wl": "wireless",
    "wlan": "wireless",
    "vpn": "vpn",
    "tun": "vpn",
    "tap": "vpn",
    "ppp": "vpn",
    "wg": "vpn",
    "docker": "bridge",
    "br": "bridge",
    "veth": "virtual",
    "vnet": "virtual",
    "macvlan": "virtual",
    "ipvlan": "virtual",
    "vlan": "virtual",
}

# VPN Ports (ProtonVPN)
COMMON_VPN_PORTS: dict[int, str] = {
    51820: "WireGuard",
    1194: "OpenVPN (UDP)",
    443: "OpenVPN (TCP)",
    5060: "OpenVPN (UDP alternate)",
    4569: "OpenVPN (UDP alternate)",
    80: "OpenVPN (TCP alternate)",
}

# Device Name Cleanup Terms
# These terms are removed from hardware device names to make them more readable.
# Sorted by length (longest first) during cleanup to avoid partial matches.
DEVICE_NAME_CLEANUP: list[str] = [
    "co.",
    "company",
    "corp.",
    "corporation",
    "inc.",
    "ltd.",
    "limited",
    "802.11ac",
    "802.11ax",
    "802.11n",
    "controller",
    "adapter",
    "ethernet",
    "network",
    "wireless",
    "gigabit",
    "fast ethernet",
    "base-t",
    "base-tx",
    "10/100",
    "10/100/1000",
    "pci express",
    "pcie",
    "rev",
    "revision",
]

# Table Configuration
TABLE_COLUMNS: list[tuple[str, int]] = [
    ("INTERFACE", 15),
    ("TYPE", 10),
    ("DEVICE", 20),
    ("INTERNAL_IPv4", 15),
    ("INTERNAL_IPv6", 25),
    ("DNS_SERVER", 20),
    ("EXTERNAL_IPv4", 15),
    ("EXTERNAL_IPv6", 25),
    ("ISP", 15),
    ("COUNTRY", 10),
    ("GATEWAY", 15),
    ("METRIC", 10),
]

COLUMN_SEPARATOR: str = "   "  # 3 spaces


# Exit Codes (Professional: Use IntEnum)
class ExitCode(IntEnum):
    """Standard exit codes for netcheck tool.
    
    Using IntEnum provides:
    - Type safety
    - IDE autocomplete
    - Prevents magic numbers
    - Standard Python pattern for exit codes
    """

    SUCCESS = 0
    GENERAL_ERROR = 1
    MISSING_DEPENDENCIES = 2
    PERMISSION_DENIED = 3  # Unused in v1.0
    INVALID_ARGUMENTS = 4


# ANSI Color Codes (StrEnum for type safety and enum benefits)
class Color(StrEnum):
    """ANSI color codes (always enabled).
    
    Using StrEnum provides:
    - Type safety
    - IDE autocomplete
    - Can be used directly as strings
    - Standard Python pattern for string constants
    """

    GREEN = "\033[92m"
    CYAN = "\033[96m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"


# Tool Metadata
VERSION: str = "1.0.0"
TOOL_NAME: str = "netcheck"
