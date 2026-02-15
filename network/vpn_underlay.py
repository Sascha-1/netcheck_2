"""VPN tunnel analysis.

Detects VPN server endpoints and identifies physical interfaces carrying VPN traffic.
"""

import ipaddress
import re

from enums import InterfaceType
from logging_config import get_logger
from models import InterfaceInfo
from network.routing_utils import get_metric_sort_key
from utils import run_command, sanitize_for_log

logger = get_logger(__name__)


def detect_vpn_underlay(interfaces: list[InterfaceInfo]) -> None:
    """Detect VPN underlay for all interfaces (in-place update).

    Algorithm:
        1. For each VPN interface:
           a. Get VPN server endpoint
           b. Find physical carrier interface
           c. Set vpn.server_ip on VPN interface
           d. Mark carrier with vpn.carries_vpn=True

    Args:
        interfaces: List of InterfaceInfo objects (modified in-place)
    """
    for interface in interfaces:
        if interface.interface_type != InterfaceType.VPN:
            continue

        # Get VPN server endpoint
        vpn_server_ip = get_vpn_server_endpoint(
            interface.name, interface.interface_type, interface.ip.ipv4
        )

        if not vpn_server_ip:
            logger.debug(
                "Could not determine VPN server for %s",
                sanitize_for_log(interface.name),
            )
            continue

        interface.vpn.server_ip = vpn_server_ip
        logger.debug(
            "[%s] VPN server: %s",
            sanitize_for_log(interface.name),
            sanitize_for_log(vpn_server_ip),
        )

        # Find physical carrier
        carrier = find_physical_interface_for_vpn(vpn_server_ip, interfaces)

        if carrier:
            logger.info(
                "[%s] Carried by %s",
                sanitize_for_log(interface.name),
                sanitize_for_log(carrier),
            )
            # Mark carrier
            for iface in interfaces:
                if iface.name == carrier:
                    iface.vpn.carries_vpn = True
                    break


def get_vpn_server_endpoint(
    _iface_name: str,
    _iface_type: InterfaceType | str,
    local_ip: str,
) -> str | None:
    """Get VPN server endpoint IP.

    Command: ss -tuna

    Priority (ProtonVPN):
        1. Connection from VPN interface IP
        2. WireGuard port 51820
        3. OpenVPN ports 1194, 443

    Filters:
        - Only ESTABLISHED connections
        - Ignore DNS (port 53)
        - Ignore private IPs
        - Ignore CGNAT

    Args:
        _iface_name: Interface name (unused, kept for API compatibility)
        _iface_type: Interface type (unused, kept for API compatibility)
        local_ip: VPN interface local IP address

    Returns:
        VPN server IP or None if not found.
    """
    if not local_ip or local_ip == "N/A":
        return None

    output = run_command(["ss", "-tuna"])
    if not output:
        return None

    candidates = []

    for line in output.split("\n"):
        if "ESTAB" not in line:
            continue

        # Parse: "ESTAB 0 0 10.8.0.2:12345 198.51.100.1:51820"
        # Extract local and remote addresses
        match = re.search(r"(\S+):(\d+)\s+(\S+):(\d+)", line)
        if not match:
            continue

        local_addr, _local_port, remote_addr, remote_port = match.groups()
        remote_port_int = int(remote_port)

        # Filter: ignore DNS
        if remote_port_int == 53:
            continue

        # Filter: ignore private/CGNAT
        if _is_private_or_cgnat(remote_addr):
            continue

        # Priority 1: Connection from VPN interface IP
        if local_addr == local_ip:
            candidates.append((0, remote_addr))  # Highest priority

        # Priority 2: WireGuard port
        elif remote_port_int == 51820:
            candidates.append((1, remote_addr))

        # Priority 3: OpenVPN ports
        elif remote_port_int in (1194, 443):
            candidates.append((2, remote_addr))

    if not candidates:
        return None

    # Sort by priority, return first
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def _is_private_or_cgnat(ip: str) -> bool:
    """Check if IP is private or CGNAT range.

    Args:
        ip: IP address string

    Returns:
        True if IP is private or CGNAT, False otherwise.
    """
    try:
        addr = ipaddress.ip_address(ip)
        # Private ranges
        if addr.is_private:
            return True
        # CGNAT: 100.64.0.0/10
        cgnat = ipaddress.ip_network("100.64.0.0/10")
        if addr in cgnat:
            return True
    except ValueError:
        pass
    return False


def find_physical_interface_for_vpn(
    _vpn_server_ip: str,
    interfaces: list[InterfaceInfo],
) -> str | None:
    """Find physical interface carrying VPN traffic.

    Algorithm:
        1. Filter: physical interfaces (ethernet/wireless/cellular/tether)
        2. Filter: must have default gateway
        3. Sort by metric (deterministic - never guess DEFAULT value)
        4. Return first (highest priority)

    Args:
        _vpn_server_ip: VPN server IP address (unused, kept for future routing lookup)
        interfaces: List of all interfaces

    Returns:
        Interface name or None if no suitable carrier found.
    """
    candidates = []

    for interface in interfaces:
        # Physical interfaces only (now includes CELLULAR)
        if interface.interface_type not in (
            InterfaceType.ETHERNET,
            InterfaceType.WIRELESS,
            InterfaceType.CELLULAR,  # NEW: Cellular modems can carry VPN
            InterfaceType.TETHER,
        ):
            continue

        # Must have default gateway
        if interface.routing.gateway in ("NONE", "N/A", "--"):
            continue

        candidates.append((interface.name, interface.routing.metric))

    if not candidates:
        return None

    # Sort using helper function
    candidates.sort(key=lambda candidate: get_metric_sort_key(candidate[1]))
    return candidates[0][0]
