"""Network analysis modules for netcheck.

Provides interface detection, IP configuration, DNS analysis,
external IP queries, and VPN tunnel analysis.
"""

from .detection import (
    detect_interface_type,
    get_device_name,
    get_interface_list,
)
from .dns import check_dns_leaks_all_interfaces, get_interface_dns
from .external_ip import get_egress_info
from .ip_routing import (
    get_active_interface,
    get_all_ipv4_addresses,
    get_all_ipv6_addresses,
    get_route_info,
)
from .routing_utils import get_metric_sort_key
from .vpn_underlay import detect_vpn_underlay

__all__ = [
    # Detection
    "get_interface_list",
    "detect_interface_type",
    "get_device_name",
    # IP and Routing
    "get_all_ipv4_addresses",
    "get_all_ipv6_addresses",
    "get_route_info",
    "get_active_interface",
    # DNS
    "get_interface_dns",
    "check_dns_leaks_all_interfaces",
    # External IP
    "get_egress_info",
    # VPN
    "detect_vpn_underlay",
    # Routing Utilities
    "get_metric_sort_key",
]
