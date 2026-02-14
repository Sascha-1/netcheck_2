"""Table output formatting and display.

Formats network interface data as a color-coded table.
Uses rule-based pattern for color selection (maintainable, extensible).
"""

import sys
from typing import Callable, TextIO

import config
from colors import Color
from enums import DnsLeakStatus, InterfaceType
from models import InterfaceInfo
from utils import cleanup_device_name, cleanup_isp_name, shorten_text


def format_output(interfaces: list[InterfaceInfo], file: TextIO | None = None) -> None:
    """Format and print table to specified file or stdout.

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
        file: Optional file handle (default: sys.stdout)
    """
    if file is None:
        file = sys.stdout

    # Print header
    print("=" * 228, file=file)
    print("Network Interface Analysis", file=file)
    print("=" * 228, file=file)

    # Print column headers
    headers = []
    for name, width in config.TABLE_COLUMNS:
        headers.append(name.ljust(width))
    print(config.COLUMN_SEPARATOR.join(headers), file=file)
    print("=" * 228, file=file)

    # Print each interface
    for interface in interfaces:
        # Clean names (DISPLAY LAYER ONLY - raw data unchanged)
        device = cleanup_device_name(interface.device)
        isp = cleanup_isp_name(interface.egress.isp)

        # Get color
        color = _get_row_color(interface)

        # Format row
        row_data = [
            interface.name,
            interface.interface_type.value,
            device,
            interface.ip.ipv4,
            interface.ip.ipv6,
            interface.dns.current_server or "--",
            interface.egress.external_ip,
            interface.egress.external_ipv6,
            isp,
            interface.egress.country,
            interface.routing.gateway,
            interface.routing.metric,
        ]

        # Truncate and pad
        row_parts = []
        for (name, width), data in zip(config.TABLE_COLUMNS, row_data):
            truncated = shorten_text(str(data), width)
            row_parts.append(truncated.ljust(width))

        # Print with color
        row = config.COLUMN_SEPARATOR.join(row_parts)
        if color:
            print(f"{color}{row}{Color.RESET}", file=file)
        else:
            print(row, file=file)

    # Print footer
    print("=" * 228, file=file)
    print("\nLegend:", file=file)
    print(f"{Color.GREEN}GREEN{Color.RESET}   - VPN tunnel (encrypted, DNS OK)", file=file)
    print(f"{Color.CYAN}CYAN{Color.RESET}    - Physical interface carrying VPN traffic", file=file)
    print(f"{Color.RED}RED{Color.RESET}     - Direct internet (unencrypted)", file=file)
    print(
        f"{Color.MAGENTA}MAGENTA{Color.RESET} - DNS LEAK (ISP sees all queries - fix immediately!)",
        file=file,
    )
    print(
        f"{Color.YELLOW}YELLOW{Color.RESET}  - "
        "DNS warning (using public DNS or unknown provider)\n",
        file=file,
    )


# Type alias for color selection predicate
ColorPredicate = Callable[[InterfaceInfo], bool]


def _get_row_color(interface: InterfaceInfo) -> str:
    """Determine row color based on priority rules.
    
    Uses rule-based pattern for maintainability:
    - Easy to add/remove/reorder rules
    - Each rule is self-documenting
    - No complex nested if/elif chains
    - Follows Open/Closed Principle
    
    Priority (first match wins):
        1. DNS leak (LEAK) -> MAGENTA (CRITICAL)
        2. DNS warning (WARN) -> YELLOW
        3. Public DNS (PUBLIC) -> YELLOW
        4. VPN with OK DNS -> GREEN
        5. VPN with external IP -> GREEN
        6. Carries VPN traffic -> CYAN
        7. Direct internet -> RED
        8. No color (default)

    Args:
        interface: InterfaceInfo object

    Returns:
        ANSI color code or empty string for no color.
    """
    # Define rules as (predicate, color) tuples
    # Rules are evaluated in order - first match wins
    rules: list[tuple[ColorPredicate, str]] = [
        # Priority 1: DNS leak (CRITICAL - ISP sees all queries)
        (
            lambda i: i.dns.leak_status == DnsLeakStatus.LEAK,
            Color.MAGENTA,
        ),
        # Priority 2: DNS warning (unknown DNS)
        (
            lambda i: i.dns.leak_status == DnsLeakStatus.WARN,
            Color.YELLOW,
        ),
        # Priority 3: Public DNS (suboptimal but not leaking to ISP)
        (
            lambda i: i.dns.leak_status == DnsLeakStatus.PUBLIC,
            Color.YELLOW,
        ),
        # Priority 4: VPN with OK DNS
        (
            lambda i: i.interface_type == InterfaceType.VPN
            and i.dns.leak_status == DnsLeakStatus.OK,
            Color.GREEN,
        ),
        # Priority 5: VPN with external IP
        (
            lambda i: i.interface_type == InterfaceType.VPN
            and i.egress.external_ip not in ("--", "N/A", "QUERY FAILED"),
            Color.GREEN,
        ),
        # Priority 6: Carries VPN traffic
        (
            lambda i: i.vpn.carries_vpn,
            Color.CYAN,
        ),
        # Priority 7: Direct internet
        (
            lambda i: i.egress.external_ip not in ("--", "N/A", "QUERY FAILED", "NONE"),
            Color.RED,
        ),
    ]

    # Find first matching rule
    for predicate, color in rules:
        if predicate(interface):
            return color

    # Default: no color
    return ""
