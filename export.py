"""JSON export functionality.

Exports network interface data to JSON format with metadata.
Flattens nested dataclass structure for JSON compatibility.
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
                i.interface_type == InterfaceType.VPN and i.ip.ipv4 != "N/A"
                for i in interfaces
            ),
            "vpn_interfaces": sum(
                1 for i in interfaces if i.interface_type == InterfaceType.VPN
            ),
            "dns_leak_detected": any(
                i.dns.leak_status == DnsLeakStatus.LEAK for i in interfaces
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
    """Convert InterfaceInfo to dictionary (flatten nested structure).
    
    Flattens nested dataclasses for JSON compatibility while maintaining
    logical grouping in the output structure.

    Args:
        interface: InterfaceInfo object

    Returns:
        Dictionary representation suitable for JSON serialization.
    """
    return {
        "name": interface.name,
        "interface_type": interface.interface_type.value,
        "device": interface.device,
        # IP configuration (nested in model, flat in JSON)
        "internal_ipv4": interface.ip.ipv4,
        "internal_ipv6": interface.ip.ipv6,
        # DNS configuration (nested in model, flat in JSON)
        "dns_servers": interface.dns.servers,
        "current_dns": interface.dns.current_server,
        "dns_leak_status": interface.dns.leak_status.value,
        # Egress information (nested in model, flat in JSON)
        "external_ipv4": interface.egress.external_ip,
        "external_ipv6": interface.egress.external_ipv6,
        "egress_isp": interface.egress.isp,
        "egress_country": interface.egress.country,
        # Routing information (nested in model, flat in JSON)
        "default_gateway": interface.routing.gateway,
        "metric": interface.routing.metric,
        # VPN information (nested in model, flat in JSON)
        "vpn_server_ip": interface.vpn.server_ip,
        "carries_vpn": interface.vpn.carries_vpn,
    }
