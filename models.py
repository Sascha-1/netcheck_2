"""Data models for network interface information.

All models use dataclasses for immutability and type safety.
Data markers (--, N/A, NONE, DEFAULT, QUERY FAILED) indicate missing/inapplicable values.
"""

from dataclasses import dataclass

from enums import DnsLeakStatus, InterfaceType


@dataclass
class InterfaceInfo:
    """Complete information about a single network interface.

    All fields use data markers for missing/inapplicable values:
        --: Not applicable (e.g., loopback external IP)
        N/A: Not available (e.g., no IPv6 configured)
        NONE: Explicitly no value (e.g., no default route)
        DEFAULT: Using default (e.g., metric not explicitly set)
        QUERY FAILED: API query attempted but failed
    """

    name: str  # Interface name (eth0, wlan0, tun0)
    interface_type: InterfaceType  # Classification enum
    device: str  # Hardware name or "N/A"
    internal_ipv4: str  # Local IPv4 or "N/A"
    internal_ipv6: str  # Global IPv6 or "N/A"
    dns_servers: list[str]  # Configured DNS servers
    current_dns: str | None  # Active DNS or None
    dns_leak_status: DnsLeakStatus  # OK/PUBLIC/LEAK/WARN/--
    external_ipv4: str  # Public IPv4 or --/QUERY FAILED
    external_ipv6: str  # Public IPv6 or --/N/A/QUERY FAILED
    egress_isp: str  # ISP name+AS or --/QUERY FAILED
    egress_country: str  # Country code or --/QUERY FAILED
    default_gateway: str  # Gateway IP or NONE
    metric: str  # Metric (number/DEFAULT/NONE)
    vpn_server_ip: str | None  # VPN endpoint (VPN interfaces only)
    carries_vpn: bool  # True if carries VPN traffic

    @classmethod
    def create_empty(cls, name: str) -> "InterfaceInfo":
        """Create interface with default markers.

        Args:
            name: Interface name

        Returns:
            InterfaceInfo with all fields set to appropriate default markers.
        """
        return cls(
            name=name,
            interface_type=InterfaceType.UNKNOWN,
            device="N/A",
            internal_ipv4="N/A",
            internal_ipv6="N/A",
            dns_servers=[],
            current_dns=None,
            dns_leak_status=DnsLeakStatus.NOT_APPLICABLE,
            external_ipv4="--",
            external_ipv6="--",
            egress_isp="--",
            egress_country="--",
            default_gateway="NONE",
            metric="NONE",
            vpn_server_ip=None,
            carries_vpn=False,
        )


@dataclass
class EgressInfo:
    """External IP and ISP information from API.

    Represents data returned from ipinfo.io API queries.
    """

    external_ip: str  # IPv4 address or "QUERY FAILED"
    external_ipv6: str  # IPv6 address or "N/A" or "QUERY FAILED"
    isp: str  # ISP name (with AS number) or "QUERY FAILED"
    country: str  # Country code or "QUERY FAILED"

    @classmethod
    def create_error(cls) -> "EgressInfo":
        """Create error response when API query fails.

        Returns:
            EgressInfo with all fields set to "QUERY FAILED".
        """
        return cls(
            external_ip="QUERY FAILED",
            external_ipv6="QUERY FAILED",
            isp="QUERY FAILED",
            country="QUERY FAILED",
        )
