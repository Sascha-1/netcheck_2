"""Type-safe enumerations for netcheck.

All categorical values use enum types for type safety and consistency.
"""

from enum import Enum


class InterfaceType(str, Enum):
    """Interface classification types."""

    LOOPBACK = "loopback"
    ETHERNET = "ethernet"
    WIRELESS = "wireless"
    VPN = "vpn"
    CELLULAR = "cellular"  # Built-in modem with SIM card (e.g., Quectel EM05-G)
    TETHER = "tether"      # USB phone tethering (e.g., Pixel sharing internet)
    VIRTUAL = "virtual"
    BRIDGE = "bridge"
    UNKNOWN = "unknown"


class DnsLeakStatus(str, Enum):
    """DNS leak detection status.

    OK: Using VPN DNS (best privacy - VPN provider sees queries)
    PUBLIC: Using public DNS (Cloudflare/Google/Quad9 - not leaking to ISP, but suboptimal)
    LEAK: Using ISP DNS (security issue - ISP sees all queries, defeats VPN privacy)
    WARN: Using unknown DNS (investigate further)
    NOT_APPLICABLE: Not applicable (no VPN active or no DNS configured)
    """

    OK = "OK"
    PUBLIC = "PUBLIC"
    LEAK = "LEAK"
    WARN = "WARN"
    NOT_APPLICABLE = "--"


class DataMarker(str, Enum):
    """Data status markers.

    NOT_APPLICABLE: Field doesn't apply to this interface type
    NOT_AVAILABLE: Data not available or could not be retrieved
    NONE_VALUE: Explicitly no value (e.g., no default route exists)
    DEFAULT: Using default value (e.g., metric not explicitly set)
    QUERY_FAILED: API query was attempted but failed
    """

    NOT_APPLICABLE = "--"
    NOT_AVAILABLE = "N/A"
    NONE_VALUE = "NONE"
    DEFAULT = "DEFAULT"
    QUERY_FAILED = "QUERY FAILED"
