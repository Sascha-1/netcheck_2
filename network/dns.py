"""DNS configuration and leak detection.

Provides deterministic DNS leak detection based on configuration (not timing).
"""

import re

import config
from enums import DnsLeakStatus, InterfaceType
from logging_config import get_logger
from models import InterfaceInfo
from utils import run_command, sanitize_for_log

logger = get_logger(__name__)


def get_interface_dns(iface_name: str) -> tuple[list[str], str | None]:
    """Get DNS configuration for interface.

    Command: resolvectl status <interface>

    Args:
        iface_name: Interface name

    Returns:
        Tuple of (all_dns_servers, current_dns_server)
    """
    output = run_command(["resolvectl", "status", iface_name])
    if not output:
        return ([], None)

    lines = output.split("\n")
    all_dns = _parse_dns_section(lines)
    current_dns = _extract_current_dns(lines)

    return (all_dns, current_dns)


def _parse_dns_section(lines: list[str]) -> list[str]:
    """Parse DNS Servers section from resolvectl output.

    Args:
        lines: Output lines from resolvectl status

    Returns:
        List of DNS server IP addresses.
    """
    dns_servers = []
    in_dns_section = False

    for line in lines:
        if "DNS Servers:" in line:
            in_dns_section = True
            # May have IP on same line
            parts = line.split(":", 1)
            if len(parts) > 1:
                ips = _extract_ips_from_text(parts[1])
                dns_servers.extend(ips)
        elif in_dns_section:
            # Indented continuation or new section
            if line.startswith(" "):
                ips = _extract_ips_from_text(line)
                dns_servers.extend(ips)
            else:
                # New section started
                break

    return dns_servers


def _extract_current_dns(lines: list[str]) -> str | None:
    """Extract Current DNS Server line.

    Args:
        lines: Output lines from resolvectl status

    Returns:
        Current DNS server IP or None.
    """
    for line in lines:
        if "Current DNS Server:" in line:
            parts = line.split(":", 1)
            if len(parts) > 1:
                ips = _extract_ips_from_text(parts[1])
                if ips:
                    return ips[0]
    return None


def _extract_ips_from_text(text: str) -> list[str]:
    """Extract IPv4/IPv6 addresses from text.

    Args:
        text: Text to search for IP addresses

    Returns:
        List of IP addresses found.
    """
    # IPv4 pattern
    ipv4_pattern = r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"
    # IPv6 pattern (simplified)
    ipv6_pattern = r"\b(?:[0-9a-f]{0,4}:){2,7}[0-9a-f]{0,4}\b"

    ips = []
    ips.extend(re.findall(ipv4_pattern, text))
    ips.extend(re.findall(ipv6_pattern, text, re.IGNORECASE))

    return ips


def check_dns_leaks_all_interfaces(interfaces: list[InterfaceInfo]) -> None:
    """Check DNS leaks for all interfaces (in-place update).

    Algorithm:
        1. Categorize DNS servers (VPN vs ISP)
        2. For each interface: detect_dns_leak()
        3. Update dns_leak_status in-place

    Args:
        interfaces: List of InterfaceInfo objects to check (modified in-place)
    """
    # Categorize DNS servers
    vpn_dns, isp_dns = collect_dns_servers_by_category(interfaces)

    # Check each interface
    for interface in interfaces:
        is_vpn = interface.interface_type == InterfaceType.VPN

        status = detect_dns_leak(
            interface.name,
            interface.internal_ipv4,
            interface.dns_servers,
            is_vpn,
            vpn_dns,
            isp_dns,
        )

        interface.dns_leak_status = DnsLeakStatus(status)


def collect_dns_servers_by_category(
    interfaces: list[InterfaceInfo],
) -> tuple[list[str], list[str]]:
    """Categorize DNS servers as VPN or ISP.

    Args:
        interfaces: List of InterfaceInfo objects

    Returns:
        Tuple of (vpn_dns, isp_dns) - deduplicated lists
    """
    vpn_dns_set = set()
    isp_dns_set = set()

    for interface in interfaces:
        if interface.interface_type == InterfaceType.VPN:
            vpn_dns_set.update(interface.dns_servers)
        elif interface.interface_type in (
            InterfaceType.ETHERNET,
            InterfaceType.WIRELESS,
            InterfaceType.TETHER,
        ):
            isp_dns_set.update(interface.dns_servers)

    return (list(vpn_dns_set), list(isp_dns_set))


def detect_dns_leak(
    interface_name: str,
    interface_ip: str,
    configured_dns: list[str],
    is_vpn: bool,
    vpn_dns: list[str],
    isp_dns: list[str],
) -> str:
    """Detect DNS leak using deterministic method.

    Algorithm:
        1. If no VPN active: return "--"
        2. If no configured DNS: return "--"
        3. If DNS overlaps ISP: return "LEAK"
        4. If DNS overlaps VPN: return "OK"
        5. If DNS overlaps PUBLIC: return "PUBLIC"
        6. Else: return "WARN"

    Status Meanings:
        OK: Using VPN DNS (best privacy - VPN provider sees queries)
        PUBLIC: Using public DNS (Cloudflare/Google/Quad9 - not leaking to ISP, but suboptimal)
        LEAK: Using ISP DNS (security issue - ISP sees all queries, defeats VPN privacy)
        WARN: Using unknown DNS (investigate further)
        --: Not applicable (no VPN active or no DNS configured)

    Args:
        interface_name: Interface name
        interface_ip: Interface IP address (unused, kept for API compatibility)
        configured_dns: List of configured DNS servers
        is_vpn: True if this is a VPN interface
        vpn_dns: List of all VPN DNS servers in system
        isp_dns: List of all ISP DNS servers in system

    Returns:
        DnsLeakStatus as string
    """
    # Step 1: Check if VPN active
    if len(vpn_dns) == 0:
        return DnsLeakStatus.NOT_APPLICABLE.value

    # Step 2: Check if DNS configured
    if len(configured_dns) == 0:
        return DnsLeakStatus.NOT_APPLICABLE.value

    # Step 3: ISP DNS leak check
    isp_overlap = set(configured_dns) & set(isp_dns)
    if isp_overlap:
        logger.warning(
            "DNS leak on %s: using ISP DNS %s",
            sanitize_for_log(interface_name),
            list(isp_overlap),
        )
        return DnsLeakStatus.LEAK.value

    # Step 4: VPN DNS check
    vpn_overlap = set(configured_dns) & set(vpn_dns)
    if vpn_overlap:
        logger.debug(
            "%s using VPN DNS: %s",
            sanitize_for_log(interface_name),
            list(vpn_overlap),
        )
        return DnsLeakStatus.OK.value

    # Step 5: Public DNS check
    public_overlap = set(configured_dns) & config.PUBLIC_DNS_SERVERS
    if public_overlap:
        logger.info(
            "%s using public DNS: %s (suboptimal but not leak to ISP)",
            sanitize_for_log(interface_name),
            list(public_overlap),
        )
        return DnsLeakStatus.PUBLIC.value

    # Step 6: Unknown DNS
    logger.warning(
        "%s using unknown DNS: %s",
        sanitize_for_log(interface_name),
        sanitize_for_log(configured_dns),
    )
    return DnsLeakStatus.WARN.value
