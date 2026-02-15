"""IP address and routing information.

Provides IPv4/IPv6 address detection and routing table analysis.
"""

import re

from logging_config import get_logger
from network.routing_utils import get_metric_sort_key
from utils import run_command, sanitize_for_log

logger = get_logger(__name__)


def get_all_ipv4_addresses() -> dict[str, str]:
    """Batch query all IPv4 addresses.

    Command: ip -4 addr show (single query, all interfaces)

    Returns:
        Dict mapping interface name to IPv4 address.
        Takes first address if interface has multiple.
    """
    output = run_command(["ip", "-4", "addr", "show"])
    if not output:
        return {}

    result = {}
    current_iface = None

    for line in output.split("\n"):
        # Interface header (doesn't start with space)
        if not line.startswith(" "):
            # Format: "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> ..."
            match = re.match(r"^\d+:\s+([^:@]+)", line)
            if match:
                current_iface = match.group(1).strip()

        # Address line (starts with space, contains "inet")
        elif line.strip().startswith("inet ") and current_iface:
            # Only store first address per interface
            if current_iface in result:
                continue

            # Format: "    inet 192.168.1.100/24 brd ..."
            match = re.search(r"inet\s+([0-9.]+)", line)
            if match:
                result[current_iface] = match.group(1)

    return result


def get_all_ipv6_addresses() -> dict[str, str]:
    """Batch query all IPv6 addresses.

    Command: ip -6 addr show

    Filters:
        - Ignore link-local (fe80::)
        - Ignore temporary/deprecated
        - Only global scope

    Returns:
        Dict mapping interface name to IPv6 address.
    """
    output = run_command(["ip", "-6", "addr", "show"])
    if not output:
        return {}

    result = {}
    current_iface = None

    for line in output.split("\n"):
        # Interface header
        if not line.startswith(" "):
            match = re.match(r"^\d+:\s+([^:@]+)", line)
            if match:
                current_iface = match.group(1).strip()

        # Address line
        elif line.strip().startswith("inet6 ") and current_iface:
            # Only store first global address per interface
            if current_iface in result:
                continue

            # Format: "    inet6 2001:db8::1/64 scope global ..."
            # Filter: skip link-local, temporary, deprecated
            if "fe80:" in line:
                continue
            if "temporary" in line or "deprecated" in line:
                continue
            if "scope global" not in line:
                continue

            match = re.search(r"inet6\s+([0-9a-f:]+)", line)
            if match:
                result[current_iface] = match.group(1)

    return result


def get_route_info(iface_name: str) -> tuple[str, str]:
    """Get gateway and metric for interface.

    Command: ip route show dev <interface>

    DESIGN DECISION - Why we return "DEFAULT" instead of querying effective metric:

    When metric is not explicitly shown in routing table, we return "DEFAULT"
    rather than querying the effective value via 'ip route get <destination>'.

    Rationale:
        1. Honesty: "DEFAULT" accurately means "kernel's default, we don't know"
        2. Design principle: Never guess or assume values
        3. Ambiguity: Which destination to query? Results may vary.
        4. Sorting works: "DEFAULT" sorts after explicit metrics (see routing_utils.py)
        5. User clarity: Explicit metric (98) vs DEFAULT is clear enough

    If you need the effective metric, use: ip route get 8.8.8.8 | grep metric

    Args:
        iface_name: Interface name

    Returns:
        Tuple of (gateway, metric) where:
            gateway: IP address or "NONE"
            metric: number string, "DEFAULT", or "NONE"
    """
    output = run_command(["ip", "route", "show", "dev", iface_name])
    if not output:
        return ("NONE", "NONE")

    for line in output.split("\n"):
        if not line.strip().startswith("default"):
            continue

        # Extract gateway
        gateway_match = re.search(r"via\s+([0-9.]+)", line)
        gateway = gateway_match.group(1) if gateway_match else "NONE"

        # Extract metric (explicit only - never guess)
        metric_match = re.search(r"metric\s+(\d+)", line)
        if metric_match:
            metric = metric_match.group(1)
        else:
            # Metric not explicitly shown - return "DEFAULT" honestly
            # See design rationale in docstring above
            metric = "DEFAULT"

        logger.debug(
            "[%s] Route: gateway=%s, metric=%s",
            sanitize_for_log(iface_name),
            sanitize_for_log(gateway),
            sanitize_for_log(metric),
        )

        return (gateway, metric)

    return ("NONE", "NONE")


def get_active_interface() -> str | None:
    """Get interface with default route.

    Command: ip route show default

    If multiple routes:
        - Return interface with lowest numeric metric
        - If all "DEFAULT": return first (kernel's choice)

    Returns:
        Interface name or None if no default route.
    """
    output = run_command(["ip", "route", "show", "default"])
    if not output:
        return None

    routes = []
    for line in output.split("\n"):
        if not line.strip().startswith("default"):
            continue

        # Extract interface
        iface_match = re.search(r"dev\s+(\S+)", line)
        if not iface_match:
            continue
        iface = iface_match.group(1)

        # Extract metric
        metric_match = re.search(r"metric\s+(\d+)", line)
        if metric_match:
            metric = metric_match.group(1)
        else:
            metric = "DEFAULT"

        routes.append((iface, metric))

    if not routes:
        return None

    # Sort using helper function
    routes.sort(key=lambda route: get_metric_sort_key(route[1]))
    return routes[0][0]
