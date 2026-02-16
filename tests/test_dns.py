"""Tests for network/dns.py.

Tests DNS configuration and leak detection with mocked commands.
"""

from unittest.mock import patch

import pytest

from enums import DnsLeakStatus, InterfaceType
from models import DNSConfig, InterfaceInfo
from network.dns import (
    _extract_current_dns,
    _extract_ips_from_text,
    _parse_dns_section,
    check_dns_leaks_all_interfaces,
    collect_dns_servers_by_category,
    detect_dns_leak,
    get_interface_dns,
)


class TestExtractIpsFromText:
    """Tests for _extract_ips_from_text function."""

    def test_extract_ipv4(self) -> None:
        """Test IPv4 extraction."""
        text = "DNS Servers: 8.8.8.8 1.1.1.1"
        ips = _extract_ips_from_text(text)
        assert "8.8.8.8" in ips
        assert "1.1.1.1" in ips

    def test_extract_ipv6(self) -> None:
        """Test IPv6 extraction."""
        text = "DNS Servers: 2001:db8::1"
        ips = _extract_ips_from_text(text)
        assert "2001:db8::1" in ips

    def test_extract_mixed(self) -> None:
        """Test mixed IPv4 and IPv6."""
        text = "DNS: 8.8.8.8 2001:db8::1"
        ips = _extract_ips_from_text(text)
        assert "8.8.8.8" in ips
        assert "2001:db8::1" in ips

    def test_no_ips(self) -> None:
        """Test no IPs returns empty list."""
        text = "No DNS servers configured"
        ips = _extract_ips_from_text(text)
        assert ips == []


class TestParseDnsSection:
    """Tests for _parse_dns_section function."""

    def test_parse_single_line(self) -> None:
        """Test parsing DNS on single line."""
        lines = [
            "Link 2 (eth0)",
            "DNS Servers: 8.8.8.8",
        ]
        dns = _parse_dns_section(lines)
        assert "8.8.8.8" in dns

    def test_parse_multiple_lines(self) -> None:
        """Test parsing DNS across multiple lines."""
        lines = [
            "Link 2 (eth0)",
            "DNS Servers: 8.8.8.8",
            "             1.1.1.1",
        ]
        dns = _parse_dns_section(lines)
        assert "8.8.8.8" in dns
        assert "1.1.1.1" in dns

    def test_stop_at_next_section(self) -> None:
        """Test parsing stops at next section."""
        lines = [
            "DNS Servers: 8.8.8.8",
            "             1.1.1.1",
            "Current DNS Server: 8.8.8.8",
        ]
        dns = _parse_dns_section(lines)
        # Should not include IPs from "Current DNS Server" line
        assert len(dns) == 2


class TestExtractCurrentDns:
    """Tests for _extract_current_dns function."""

    def test_extract_current(self) -> None:
        """Test extracting current DNS server."""
        lines = [
            "Link 2 (eth0)",
            "Current DNS Server: 8.8.8.8",
        ]
        current = _extract_current_dns(lines)
        assert current == "8.8.8.8"

    def test_no_current(self) -> None:
        """Test no current DNS returns None."""
        lines = [
            "Link 2 (eth0)",
            "DNS Servers: 8.8.8.8",
        ]
        current = _extract_current_dns(lines)
        assert current is None


class TestGetInterfaceDns:
    """Tests for get_interface_dns function."""

    @patch("network.dns.run_command")
    def test_successful_query(self, mock_run) -> None:
        """Test successful DNS query."""
        mock_run.return_value = """Link 2 (eth0)
    Current Scopes: DNS
    DefaultRoute setting: yes
    DNS Servers: 8.8.8.8
                 1.1.1.1
    Current DNS Server: 8.8.8.8"""

        servers, current = get_interface_dns("eth0")

        assert "8.8.8.8" in servers
        assert "1.1.1.1" in servers
        assert current == "8.8.8.8"

    @patch("network.dns.run_command")
    def test_command_failure(self, mock_run) -> None:
        """Test command failure returns empty."""
        mock_run.return_value = None

        servers, current = get_interface_dns("eth0")

        assert servers == []
        assert current is None


class TestCollectDnsServersByCategory:
    """Tests for collect_dns_servers_by_category function."""

    def test_categorize_vpn_dns(self) -> None:
        """Test VPN DNS is categorized correctly."""
        interfaces = [
            InterfaceInfo.create_empty("tun0"),
        ]
        interfaces[0].interface_type = InterfaceType.VPN
        interfaces[0].dns = DNSConfig(
            servers=["10.8.0.1"],
            current_server="10.8.0.1",
            leak_status=DnsLeakStatus.NOT_APPLICABLE,
        )

        vpn_dns, isp_dns = collect_dns_servers_by_category(interfaces)

        assert "10.8.0.1" in vpn_dns
        assert len(isp_dns) == 0

    def test_categorize_isp_dns(self) -> None:
        """Test ISP DNS is categorized correctly."""
        interfaces = [
            InterfaceInfo.create_empty("eth0"),
        ]
        interfaces[0].interface_type = InterfaceType.ETHERNET
        interfaces[0].dns = DNSConfig(
            servers=["192.168.1.1"],
            current_server="192.168.1.1",
            leak_status=DnsLeakStatus.NOT_APPLICABLE,
        )

        vpn_dns, isp_dns = collect_dns_servers_by_category(interfaces)

        assert "192.168.1.1" in isp_dns
        assert len(vpn_dns) == 0

    def test_deduplication(self) -> None:
        """Test duplicate DNS servers are deduplicated."""
        interfaces = [
            InterfaceInfo.create_empty("eth0"),
            InterfaceInfo.create_empty("eth1"),
        ]
        for iface in interfaces:
            iface.interface_type = InterfaceType.ETHERNET
            iface.dns = DNSConfig(
                servers=["8.8.8.8"],
                current_server="8.8.8.8",
                leak_status=DnsLeakStatus.NOT_APPLICABLE,
            )

        vpn_dns, isp_dns = collect_dns_servers_by_category(interfaces)

        assert len(isp_dns) == 1
        assert "8.8.8.8" in isp_dns


class TestDetectDnsLeak:
    """Tests for detect_dns_leak function."""

    def test_no_vpn_active(self) -> None:
        """Test returns NOT_APPLICABLE when no VPN active."""
        result = detect_dns_leak(
            "eth0",
            "192.168.1.1",
            ["8.8.8.8"],
            False,
            [],  # No VPN DNS
            ["192.168.1.1"],
        )
        assert result == DnsLeakStatus.NOT_APPLICABLE.value

    def test_no_configured_dns(self) -> None:
        """Test returns NOT_APPLICABLE when no DNS configured."""
        result = detect_dns_leak(
            "eth0",
            "192.168.1.1",
            [],  # No configured DNS
            False,
            ["10.8.0.1"],
            ["192.168.1.1"],
        )
        assert result == DnsLeakStatus.NOT_APPLICABLE.value

    def test_isp_dns_leak(self) -> None:
        """Test detects ISP DNS leak."""
        result = detect_dns_leak(
            "eth0",
            "192.168.1.1",
            ["192.168.1.1"],  # Using ISP DNS
            False,
            ["10.8.0.1"],  # VPN DNS available
            ["192.168.1.1"],  # ISP DNS
        )
        assert result == DnsLeakStatus.LEAK.value

    def test_vpn_dns_ok(self) -> None:
        """Test VPN DNS is OK."""
        result = detect_dns_leak(
            "tun0",
            "10.8.0.2",
            ["10.8.0.1"],  # Using VPN DNS
            True,
            ["10.8.0.1"],  # VPN DNS
            ["192.168.1.1"],  # ISP DNS
        )
        assert result == DnsLeakStatus.OK.value

    def test_public_dns(self) -> None:
        """Test public DNS detection."""
        result = detect_dns_leak(
            "eth0",
            "192.168.1.1",
            ["8.8.8.8"],  # Using Google DNS
            False,
            ["10.8.0.1"],  # VPN DNS available
            ["192.168.1.1"],  # ISP DNS
        )
        assert result == DnsLeakStatus.PUBLIC.value

    def test_unknown_dns_warn(self) -> None:
        """Test unknown DNS triggers warning."""
        result = detect_dns_leak(
            "eth0",
            "192.168.1.1",
            ["1.2.3.4"],  # Unknown DNS
            False,
            ["10.8.0.1"],  # VPN DNS
            ["192.168.1.1"],  # ISP DNS
        )
        assert result == DnsLeakStatus.WARN.value


class TestCheckDnsLeaksAllInterfaces:
    """Tests for check_dns_leaks_all_interfaces function."""

    def test_updates_leak_status(self) -> None:
        """Test leak status is updated in-place."""
        interfaces = [
            InterfaceInfo.create_empty("tun0"),
            InterfaceInfo.create_empty("eth0"),
        ]
        # Setup VPN interface
        interfaces[0].interface_type = InterfaceType.VPN
        interfaces[0].ip.ipv4 = "10.8.0.2"
        interfaces[0].dns = DNSConfig(
            servers=["10.8.0.1"],
            current_server="10.8.0.1",
            leak_status=DnsLeakStatus.NOT_APPLICABLE,
        )
        # Setup Ethernet interface
        interfaces[1].interface_type = InterfaceType.ETHERNET
        interfaces[1].ip.ipv4 = "192.168.1.100"
        interfaces[1].dns = DNSConfig(
            servers=["192.168.1.1"],
            current_server="192.168.1.1",
            leak_status=DnsLeakStatus.NOT_APPLICABLE,
        )

        check_dns_leaks_all_interfaces(interfaces)

        # VPN using VPN DNS should be OK
        assert interfaces[0].dns.leak_status == DnsLeakStatus.OK
        # Ethernet using ISP DNS while VPN active should be LEAK
        assert interfaces[1].dns.leak_status == DnsLeakStatus.LEAK
