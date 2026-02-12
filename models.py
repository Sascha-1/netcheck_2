"""Data models for network interface information.

All models use dataclasses for immutability and type safety.
Data markers (--, N/A, NONE, DEFAULT, QUERY FAILED) indicate missing/inapplicable values.

Architecture: Nested dataclasses group related attributes (SRP principle):
- IPConfig: IP address configuration
- DNSConfig: DNS configuration and leak detection
- RoutingInfo: Routing table information
- VPNInfo: VPN-specific metadata
- EgressInfo: External connectivity information
"""

from dataclasses import dataclass

from enums import DnsLeakStatus, InterfaceType


@dataclass
class IPConfig:
    """IP address configuration for an interface.
    
    Groups IPv4 and IPv6 addresses together following Single Responsibility.
    """

    ipv4: str  # IPv4 address or "N/A"
    ipv6: str  # IPv6 address or "N/A"

    @classmethod
    def create_empty(cls) -> "IPConfig":
        """Create IP config with default markers."""
        return cls(ipv4="N/A", ipv6="N/A")


@dataclass
class DNSConfig:
    """DNS configuration and leak detection status.
    
    Groups all DNS-related information together.
    """

    servers: list[str]  # Configured DNS servers
    current_server: str | None  # Active DNS server or None
    leak_status: DnsLeakStatus  # OK/PUBLIC/LEAK/WARN/--

    @classmethod
    def create_empty(cls) -> "DNSConfig":
        """Create DNS config with default markers."""
        return cls(
            servers=[],
            current_server=None,
            leak_status=DnsLeakStatus.NOT_APPLICABLE,
        )


@dataclass
class RoutingInfo:
    """Routing table information for an interface.
    
    Groups gateway and metric together.
    """

    gateway: str  # Gateway IP or "NONE"
    metric: str  # Metric (number/DEFAULT/NONE)

    @classmethod
    def create_empty(cls) -> "RoutingInfo":
        """Create routing info with default markers."""
        return cls(gateway="NONE", metric="NONE")


@dataclass
class VPNInfo:
    """VPN-specific metadata.
    
    Groups VPN server and carrier information.
    """

    server_ip: str | None  # VPN endpoint (VPN interfaces only)
    carries_vpn: bool  # True if this interface carries VPN traffic

    @classmethod
    def create_empty(cls) -> "VPNInfo":
        """Create VPN info with default markers."""
        return cls(server_ip=None, carries_vpn=False)


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

    @classmethod
    def create_empty(cls) -> "EgressInfo":
        """Create egress info with default markers for non-active interfaces."""
        return cls(
            external_ip="--",
            external_ipv6="--",
            isp="--",
            country="--",
        )


@dataclass
class InterfaceInfo:
    """Complete information about a single network interface.
    
    Uses nested dataclasses to group related attributes (SRP).
    Now has 8 top-level attributes (was 16 - complies with pylint limit of 10).
    
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
    ip: IPConfig  # IP address configuration
    dns: DNSConfig  # DNS configuration and leak detection
    egress: EgressInfo  # External IP and ISP information
    routing: RoutingInfo  # Routing table information
    vpn: VPNInfo  # VPN-specific metadata

    @classmethod
    def create_empty(cls, name: str) -> "InterfaceInfo":
        """Create interface with default markers.

        Args:
            name: Interface name

        Returns:
            InterfaceInfo with all nested configs initialized.
        """
        return cls(
            name=name,
            interface_type=InterfaceType.UNKNOWN,
            device="N/A",
            ip=IPConfig.create_empty(),
            dns=DNSConfig.create_empty(),
            egress=EgressInfo.create_empty(),
            routing=RoutingInfo.create_empty(),
            vpn=VPNInfo.create_empty(),
        )
