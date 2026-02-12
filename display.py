"""Table output formatting and display.

Formats network interface data as a color-coded table.
"""

import config
from enums import DnsLeakStatus, InterfaceType
from models import InterfaceInfo
from utils import cleanup_device_name, cleanup_isp_name, shorten_text


def format_output(interfaces: list[InterfaceInfo]) -> None:
    """Format and print table to stdout.

    Process:
        1. Print header
        2. Print column headers
        3. For each interface:
           - Clean device/ISP names
           - Apply color coding
           - Print row
        4. Print footer with legend

    Args:
        interfaces: List of InterfaceInfo objects to display
    """
    # Print header
    print("=" * 228)
    print("Network Interface Analysis")
    print("=" * 228)

    # Print column headers
    headers = []
    for name, width in config.TABLE_COLUMNS:
        headers.append(name.ljust(width))
    print(config.COLUMN_SEPARATOR.join(headers))
    print("=" * 228)

    # Print each interface
    for interface in interfaces:
        # Clean names
        device = cleanup_device_name(interface.device)
        isp = cleanup_isp_name(interface.egress_isp)

        # Get color
        color = _get_row_color(interface)

        # Format row
        row_data = [
            interface.name,
            interface.interface_type.value,
            device,
            interface.internal_ipv4,
            interface.internal_ipv6,
            interface.current_dns or "--",
            interface.external_ipv4,
            interface.external_ipv6,
            isp,
            interface.egress_country,
            interface.default_gateway,
            interface.metric,
        ]

        # Truncate and pad
        row_parts = []
        for (name, width), data in zip(config.TABLE_COLUMNS, row_data):
            truncated = shorten_text(str(data), width)
            row_parts.append(truncated.ljust(width))

        # Print with color
        row = config.COLUMN_SEPARATOR.join(row_parts)
        if color:
            print(f"{color}{row}{config.Colors.RESET}")
        else:
            print(row)

    # Print footer
    print("=" * 228)
    print("\nColor Legend:")
    print(
        f"{config.Colors.GREEN}GREEN{config.Colors.RESET}  - VPN tunnel (encrypted, DNS OK)"
    )
    print(f"{config.Colors.CYAN}CYAN{config.Colors.RESET}   - Physical interface carrying VPN")
    print(f"{config.Colors.RED}RED{config.Colors.RESET}    - Direct internet (unencrypted)")
    print(
        f"{config.Colors.YELLOW}YELLOW{config.Colors.RESET} - DNS leak, public DNS, or warning"
    )
    print("\nDNS Status Meanings:")
    print("  OK     - Using VPN DNS (best privacy - VPN provider sees queries)")
    print(
        "  PUBLIC - Using public DNS (Cloudflare/Google/Quad9 - not leaking to ISP, but suboptimal)"
    )
    print("  LEAK   - Using ISP DNS (security issue - ISP sees all queries, defeats VPN privacy)")
    print("  WARN   - Using unknown DNS (investigate further)")
    print("  --     - Not applicable (no VPN active or no DNS configured)\n")


def _get_row_color(interface: InterfaceInfo) -> str:
    """Determine row color based on priority rules.

    Priority (first match wins):
        1. DNS leak (LEAK) → YELLOW
        2. DNS warning → YELLOW
        3. Public DNS → YELLOW
        4. VPN with OK DNS → GREEN
        5. VPN with external IP → GREEN
        6. Carries VPN traffic → CYAN
        7. Direct internet → RED
        8. No color

    Args:
        interface: InterfaceInfo object

    Returns:
        ANSI color code or empty string for no color.
    """
    # Priority 1: DNS leak (security issue)
    if interface.dns_leak_status == DnsLeakStatus.LEAK:
        return config.Colors.YELLOW

    # Priority 2: DNS warning
    if interface.dns_leak_status == DnsLeakStatus.WARN:
        return config.Colors.YELLOW

    # Priority 3: Public DNS (suboptimal)
    if interface.dns_leak_status == DnsLeakStatus.PUBLIC:
        return config.Colors.YELLOW

    # Priority 4: VPN with OK DNS
    if (
        interface.interface_type == InterfaceType.VPN
        and interface.dns_leak_status == DnsLeakStatus.OK
    ):
        return config.Colors.GREEN

    # Priority 5: VPN with external IP
    if interface.interface_type == InterfaceType.VPN and interface.external_ipv4 not in (
        "--",
        "N/A",
        "QUERY FAILED",
    ):
        return config.Colors.GREEN

    # Priority 6: Carries VPN traffic
    if interface.carries_vpn:
        return config.Colors.CYAN

    # Priority 7: Direct internet
    if interface.external_ipv4 not in ("--", "N/A", "QUERY FAILED", "NONE"):
        return config.Colors.RED

    # Priority 8: No color
    return ""
