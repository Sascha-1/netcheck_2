"""Tests for models.py and enums.py.

Tests data model creation, validation, and enum types.
"""

import pytest

from enums import DataMarker, DnsLeakStatus, InterfaceType
from models import (
    DNSConfig,
    EgressInfo,
    InterfaceInfo,
    IPConfig,
    RoutingInfo,
    VPNInfo,
)


class TestInterfaceType:
    """Tests for InterfaceType enum."""

    def test_all_types_defined(self):
        """Test all interface types are defined."""
        assert InterfaceType.LOOPBACK == "loopback"
        assert InterfaceType.ETHERNET == "ethernet"
        assert InterfaceType.WIRELESS == "wireless"
        assert InterfaceType.VPN == "vpn"
        assert InterfaceType.CELLULAR == "cellular"
        assert InterfaceType.TETHER == "tether"
        assert InterfaceType.VIRTUAL == "virtual"
        assert InterfaceType.BRIDGE == "bridge"
        assert InterfaceType.UNKNOWN == "unknown"

    def test_enum_values_are_strings(self):
        """Test enum values are strings."""
        assert isinstance(InterfaceType.ETHERNET.value, str)


class TestDnsLeakStatus:
    """Tests for DnsLeakStatus enum."""

    def test_all_statuses_defined(self):
        """Test all DNS leak statuses are defined."""
        assert DnsLeakStatus.OK == "OK"
        assert DnsLeakStatus.PUBLIC == "PUBLIC"
        assert DnsLeakStatus.LEAK == "LEAK"
        assert DnsLeakStatus.WARN == "WARN"
        assert DnsLeakStatus.NOT_APPLICABLE == "--"


class TestDataMarker:
    """Tests for DataMarker enum."""

    def test_all_markers_defined(self):
        """Test all data markers are defined."""
        assert DataMarker.NOT_APPLICABLE == "--"
        assert DataMarker.NOT_AVAILABLE == "N/A"
        assert DataMarker.NONE_VALUE == "NONE"
        assert DataMarker.DEFAULT == "DEFAULT"
        assert DataMarker.QUERY_FAILED == "QUERY FAILED"


class TestIPConfig:
    """Tests for IPConfig dataclass."""

    def test_create_basic(self):
        """Test basic IPConfig creation."""
        config = IPConfig(ipv4="192.168.1.1", ipv6="2001:db8::1")
        assert config.ipv4 == "192.168.1.1"
        assert config.ipv6 == "2001:db8::1"

    def test_create_empty(self):
        """Test create_empty factory method."""
        config = IPConfig.create_empty()
        assert config.ipv4 == "N/A"
        assert config.ipv6 == "N/A"


class TestDNSConfig:
    """Tests for DNSConfig dataclass."""

    def test_create_basic(self):
        """Test basic DNSConfig creation."""
        config = DNSConfig(
            servers=["8.8.8.8", "1.1.1.1"],
            current_server="8.8.8.8",
            leak_status=DnsLeakStatus.OK,
        )
        assert config.servers == ["8.8.8.8", "1.1.1.1"]
        assert config.current_server == "8.8.8.8"
        assert config.leak_status == DnsLeakStatus.OK

    def test_create_empty(self):
        """Test create_empty factory method."""
        config = DNSConfig.create_empty()
        assert config.servers == []
        assert config.current_server is None
        assert config.leak_status == DnsLeakStatus.NOT_APPLICABLE


class TestRoutingInfo:
    """Tests for RoutingInfo dataclass."""

    def test_create_basic(self):
        """Test basic RoutingInfo creation."""
        info = RoutingInfo(gateway="192.168.1.1", metric="100")
        assert info.gateway == "192.168.1.1"
        assert info.metric == "100"

    def test_create_empty(self):
        """Test create_empty factory method."""
        info = RoutingInfo.create_empty()
        assert info.gateway == "NONE"
        assert info.metric == "NONE"


class TestVPNInfo:
    """Tests for VPNInfo dataclass."""

    def test_create_basic(self):
        """Test basic VPNInfo creation."""
        info = VPNInfo(server_ip="198.51.100.1", carries_vpn=True)
        assert info.server_ip == "198.51.100.1"
        assert info.carries_vpn is True

    def test_create_empty(self):
        """Test create_empty factory method."""
        info = VPNInfo.create_empty()
        assert info.server_ip is None
        assert info.carries_vpn is False


class TestEgressInfo:
    """Tests for EgressInfo dataclass."""

    def test_create_basic(self):
        """Test basic EgressInfo creation."""
        info = EgressInfo(
            external_ip="203.0.113.1",
            external_ipv6="2001:db8::1",
            isp="AS12345 Example ISP",
            country="US",
        )
        assert info.external_ip == "203.0.113.1"
        assert info.external_ipv6 == "2001:db8::1"
        assert info.isp == "AS12345 Example ISP"
        assert info.country == "US"

    def test_create_error(self):
        """Test create_error factory method."""
        info = EgressInfo.create_error()
        assert info.external_ip == "QUERY FAILED"
        assert info.external_ipv6 == "QUERY FAILED"
        assert info.isp == "QUERY FAILED"
        assert info.country == "QUERY FAILED"

    def test_create_empty(self):
        """Test create_empty factory method."""
        info = EgressInfo.create_empty()
        assert info.external_ip == "--"
        assert info.external_ipv6 == "--"
        assert info.isp == "--"
        assert info.country == "--"


class TestInterfaceInfo:
    """Tests for InterfaceInfo dataclass."""

    def test_create_basic(self):
        """Test basic InterfaceInfo creation."""
        iface = InterfaceInfo(
            name="eth0",
            interface_type=InterfaceType.ETHERNET,
            device="Intel I225-V",
            ip=IPConfig(ipv4="192.168.1.1", ipv6="N/A"),
            dns=DNSConfig.create_empty(),
            egress=EgressInfo.create_empty(),
            routing=RoutingInfo.create_empty(),
            vpn=VPNInfo.create_empty(),
        )
        assert iface.name == "eth0"
        assert iface.interface_type == InterfaceType.ETHERNET
        assert iface.device == "Intel I225-V"

    def test_create_empty(self):
        """Test create_empty factory method."""
        iface = InterfaceInfo.create_empty("wlan0")
        assert iface.name == "wlan0"
        assert iface.interface_type == InterfaceType.UNKNOWN
        assert iface.device == "N/A"
        assert iface.ip.ipv4 == "N/A"
        assert iface.ip.ipv6 == "N/A"
        assert iface.dns.servers == []
        assert iface.egress.external_ip == "--"
        assert iface.routing.gateway == "NONE"
        assert iface.vpn.server_ip is None

    def test_complete_interface(self):
        """Test complete interface with all fields populated."""
        iface = InterfaceInfo(
            name="tun0",
            interface_type=InterfaceType.VPN,
            device="N/A",
            ip=IPConfig(ipv4="10.8.0.2", ipv6="N/A"),
            dns=DNSConfig(
                servers=["10.8.0.1"],
                current_server="10.8.0.1",
                leak_status=DnsLeakStatus.OK,
            ),
            egress=EgressInfo(
                external_ip="203.0.113.99",
                external_ipv6="N/A",
                isp="ProtonVPN",
                country="CH",
            ),
            routing=RoutingInfo(gateway="10.8.0.1", metric="50"),
            vpn=VPNInfo(server_ip="198.51.100.1", carries_vpn=False),
        )
        assert iface.name == "tun0"
        assert iface.interface_type == InterfaceType.VPN
        assert iface.dns.leak_status == DnsLeakStatus.OK
        assert iface.vpn.server_ip == "198.51.100.1"
