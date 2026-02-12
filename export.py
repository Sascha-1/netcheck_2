"""JSON export functionality.

Exports network interface data to JSON format with metadata.
"""

import json
from datetime import datetime, timezone
from typing import Any

import config
from enums import DnsLeakStatus, InterfaceType
from models import InterfaceInfo


def export_to_json(
    interfaces: list[InterfaceInfo],
    indent: int = 2,
) -> str:
    """Export to JSON format with metadata.

    Args:
        interfaces: List of InterfaceInfo objects
        indent: JSON indentation (default 2)

    Returns:
        JSON string with metadata and interface data.
    """
    # Build metadata
    metadata = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "interface_count": len(interfaces),
        "tool": config.TOOL_NAME,
        "version": config.VERSION,
        "summary": {
            # VPN is active if any VPN interface has an IP address configured
            "vpn_active": any(
                i.interface_type == InterfaceType.VPN and i.internal_ipv4 != "N/A"
                for i in interfaces
            ),
            "vpn_interfaces": sum(
                1 for i in interfaces if i.interface_type == InterfaceType.VPN
            ),
            "dns_leak_detected": any(
                i.dns_leak_status == DnsLeakStatus.LEAK for i in interfaces
            ),
        },
    }

    # Build output
    output = {
        "metadata": metadata,
        "interfaces": [_interface_to_dict(i) for i in interfaces],
    }

    return json.dumps(output, indent=indent)


def _interface_to_dict(interface: InterfaceInfo) -> dict[str, Any]:
    """Convert InterfaceInfo to dictionary (handle enums).

    Args:
        interface: InterfaceInfo object

    Returns:
        Dictionary representation suitable for JSON serialization.
    """
    return {
        "name": interface.name,
        "interface_type": interface.interface_type.value,
        "device": interface.device,
        "internal_ipv4": interface.internal_ipv4,
        "internal_ipv6": interface.internal_ipv6,
        "dns_servers": interface.dns_servers,
        "current_dns": interface.current_dns,
        "dns_leak_status": interface.dns_leak_status.value,
        "external_ipv4": interface.external_ipv4,
        "external_ipv6": interface.external_ipv6,
        "egress_isp": interface.egress_isp,
        "egress_country": interface.egress_country,
        "default_gateway": interface.default_gateway,
        "metric": interface.metric,
        "vpn_server_ip": interface.vpn_server_ip,
        "carries_vpn": interface.carries_vpn,
    }
