"""Tests for export.py.

Tests JSON export functionality and data transformation.
"""

import json
from datetime import datetime

import pytest

from enums import DnsLeakStatus, InterfaceType
from export import export_to_json, _interface_to_dict
from models import (
    DNSConfig,
    EgressInfo,
    InterfaceInfo,
    IPConfig,
    RoutingInfo,
    VPNInfo,
)


class TestInterfaceToDict:
    """Tests for _interface_to_dict function."""

    def test_basic_conversion(self):
        """Test basic interface conversion to dict."""
        iface = InterfaceInfo(
            name="eth0",
            interface_type=InterfaceType.ETHERNET,
            device="Intel I225-V",
            ip=IPConfig(ipv4="192.168.1.1", ipv6="N/A"),
            dns=DNSConfig(
                servers=["8.8.8.8"],
                current_server="8.8.8.8",
                leak_status=DnsLeakStatus.OK,
            ),
            egress=EgressInfo(
                external_ip="203.0.113.1",
                external_ipv6="N/A",
                isp="AS12345 ISP",
                country="US",
            ),
            routing=RoutingInfo(gateway="192.168.1.1", metric="100"),
            vpn=VPNInfo(server_ip=None, carries_vpn=False),
        )

        result = _interface_to_dict(iface)

        assert result["name"] == "eth0"
        assert result["interface_type"] == "ethernet"
        assert result["device"] == "Intel I225-V"
        assert result["internal_ipv4"] == "192.168.1.1"
        assert result["internal_ipv6"] == "N/A"
        assert result["dns_servers"] == ["8.8.8.8"]
        assert result["current_dns"] == "8.8.8.8"
        assert result["dns_leak_status"] == "OK"
        assert result["external_ipv4"] == "203.0.113.1"
        assert result["external_ipv6"] == "N/A"
        assert result["egress_isp"] == "AS12345 ISP"
        assert result["egress_country"] == "US"
        assert result["default_gateway"] == "192.168.1.1"
        assert result["metric"] == "100"
        assert result["vpn_server_ip"] is None
        assert result["carries_vpn"] is False

    def test_vpn_interface(self):
        """Test VPN interface conversion."""
        iface = InterfaceInfo(
            name="tun0",
            interface_type=InterfaceType.VPN,
            device="N/A",
            ip=IPConfig(ipv4="10.8.0.2", ipv6="N/A"),
            dns=DNSConfig.create_empty(),
            egress=EgressInfo.create_empty(),
            routing=RoutingInfo.create_empty(),
            vpn=VPNInfo(server_ip="198.51.100.1", carries_vpn=False),
        )

        result = _interface_to_dict(iface)

        assert result["interface_type"] == "vpn"
        assert result["vpn_server_ip"] == "198.51.100.1"


class TestExportToJson:
    """Tests for export_to_json function."""

    def test_basic_export(self):
        """Test basic JSON export."""
        interfaces = [
            InterfaceInfo.create_empty("eth0"),
        ]

        json_str = export_to_json(interfaces)
        data = json.loads(json_str)

        assert "metadata" in data
        assert "interfaces" in data
        assert isinstance(data["metadata"], dict)
        assert isinstance(data["interfaces"], list)

    def test_metadata_fields(self):
        """Test metadata fields are present."""
        interfaces = []
        json_str = export_to_json(interfaces)
        data = json.loads(json_str)

        metadata = data["metadata"]
        assert "timestamp" in metadata
        assert "interface_count" in metadata
        assert "tool" in metadata
        assert "version" in metadata
        assert "summary" in metadata

        assert metadata["interface_count"] == 0
        assert metadata["tool"] == "netcheck"

    def test_summary_vpn_detection(self):
        """Test summary correctly detects VPN active status."""
        interfaces = [
            InterfaceInfo(
                name="tun0",
                interface_type=InterfaceType.VPN,
                device="N/A",
                ip=IPConfig(ipv4="10.8.0.2", ipv6="N/A"),
                dns=DNSConfig.create_empty(),
                egress=EgressInfo.create_empty(),
                routing=RoutingInfo.create_empty(),
                vpn=VPNInfo.create_empty(),
            ),
        ]

        json_str = export_to_json(interfaces)
        data = json.loads(json_str)

        summary = data["metadata"]["summary"]
        assert summary["vpn_active"] is True
        assert summary["vpn_interfaces"] == 1

    def test_summary_vpn_inactive(self):
        """Test summary shows VPN inactive when no IP."""
        interfaces = [
            InterfaceInfo(
                name="tun0",
                interface_type=InterfaceType.VPN,
                device="N/A",
                ip=IPConfig(ipv4="N/A", ipv6="N/A"),  # No IP = inactive
                dns=DNSConfig.create_empty(),
                egress=EgressInfo.create_empty(),
                routing=RoutingInfo.create_empty(),
                vpn=VPNInfo.create_empty(),
            ),
        ]

        json_str = export_to_json(interfaces)
        data = json.loads(json_str)

        summary = data["metadata"]["summary"]
        assert summary["vpn_active"] is False
        assert summary["vpn_interfaces"] == 1

    def test_summary_dns_leak_detection(self):
        """Test summary correctly detects DNS leaks."""
        interfaces = [
            InterfaceInfo(
                name="eth0",
                interface_type=InterfaceType.ETHERNET,
                device="N/A",
                ip=IPConfig.create_empty(),
                dns=DNSConfig(
                    servers=["192.168.1.1"],
                    current_server="192.168.1.1",
                    leak_status=DnsLeakStatus.LEAK,
                ),
                egress=EgressInfo.create_empty(),
                routing=RoutingInfo.create_empty(),
                vpn=VPNInfo.create_empty(),
            ),
        ]

        json_str = export_to_json(interfaces)
        data = json.loads(json_str)

        summary = data["metadata"]["summary"]
        assert summary["dns_leak_detected"] is True

    def test_custom_indent(self):
        """Test custom indentation."""
        interfaces = []
        json_str = export_to_json(interfaces, indent=4)
        # Should contain 4-space indentation
        assert "    " in json_str

    def test_interface_count(self):
        """Test interface count is accurate."""
        interfaces = [
            InterfaceInfo.create_empty("eth0"),
            InterfaceInfo.create_empty("wlan0"),
            InterfaceInfo.create_empty("tun0"),
        ]

        json_str = export_to_json(interfaces)
        data = json.loads(json_str)

        assert data["metadata"]["interface_count"] == 3
        assert len(data["interfaces"]) == 3

    def test_timestamp_format(self):
        """Test timestamp is ISO format."""
        interfaces = []
        json_str = export_to_json(interfaces)
        data = json.loads(json_str)

        timestamp = data["metadata"]["timestamp"]
        # Should be parseable as ISO datetime
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
