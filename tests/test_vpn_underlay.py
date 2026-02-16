"""Tests for network/vpn_underlay.py.

Tests VPN tunnel analysis and underlay detection with mocked commands.
FIXED: Added MagicMock type annotations to all mock parameters
"""

from unittest.mock import patch, MagicMock

import pytest

from enums import InterfaceType
from models import InterfaceInfo, IPConfig, RoutingInfo
from network.vpn_underlay import (
    _is_private_or_cgnat,
    detect_vpn_underlay,
    find_physical_interface_for_vpn,
    get_vpn_server_endpoint,
)


class TestIsPrivateOrCgnat:
    """Tests for _is_private_or_cgnat function."""

    def test_private_ipv4(self) -> None:
        """Test private IPv4 ranges are detected."""
        assert _is_private_or_cgnat("192.168.1.1") is True
        assert _is_private_or_cgnat("10.0.0.1") is True
        assert _is_private_or_cgnat("172.16.0.1") is True

    def test_cgnat_range(self) -> None:
        """Test CGNAT range is detected."""
        assert _is_private_or_cgnat("100.64.0.1") is True
        assert _is_private_or_cgnat("100.127.255.255") is True

    def test_public_ipv4(self) -> None:
        """Test public IPv4 is not private."""
        # Use actual public IPs, not documentation ranges
        assert _is_private_or_cgnat("8.8.8.8") is False
        assert _is_private_or_cgnat("1.1.1.1") is False
        # Note: 203.0.113.x is TEST-NET-3 and may be treated as reserved

    def test_invalid_ip(self) -> None:
        """Test invalid IP returns False."""
        assert _is_private_or_cgnat("invalid") is False
        assert _is_private_or_cgnat("") is False


class TestGetVpnServerEndpoint:
    """Tests for get_vpn_server_endpoint function."""

    @patch("network.vpn_underlay.run_command")
    def test_connection_from_vpn_ip(self, mock_run: MagicMock) -> None:
        """Test VPN server detected from VPN interface IP."""
        # Real ss output format includes more columns
        mock_run.return_value = """tcp   ESTAB      0      0      10.8.0.2:51234              8.8.8.8:51820"""

        result = get_vpn_server_endpoint("tun0", InterfaceType.VPN, "10.8.0.2")

        assert result == "8.8.8.8"

    @patch("network.vpn_underlay.run_command")
    def test_wireguard_port(self, mock_run: MagicMock) -> None:
        """Test WireGuard port (51820) is detected."""
        mock_run.return_value = """tcp   ESTAB      0      0      192.168.1.100:51234         8.8.8.8:51820"""

        result = get_vpn_server_endpoint("tun0", InterfaceType.VPN, "10.8.0.2")

        assert result == "8.8.8.8"

    @patch("network.vpn_underlay.run_command")
    def test_openvpn_port(self, mock_run: MagicMock) -> None:
        """Test OpenVPN ports (1194, 443) are detected."""
        mock_run.return_value = """tcp   ESTAB      0      0      192.168.1.100:51234         8.8.8.8:1194"""

        result = get_vpn_server_endpoint("tun0", InterfaceType.VPN, "10.8.0.2")

        assert result == "8.8.8.8"

    @patch("network.vpn_underlay.run_command")
    def test_ignore_dns_port(self, mock_run: MagicMock) -> None:
        """Test DNS connections (port 53) are ignored."""
        mock_run.return_value = """tcp   ESTAB      0      0      192.168.1.100:51234         8.8.8.8:53"""

        result = get_vpn_server_endpoint("tun0", InterfaceType.VPN, "10.8.0.2")

        assert result is None

    @patch("network.vpn_underlay.run_command")
    def test_ignore_private_ips(self, mock_run: MagicMock) -> None:
        """Test private IPs are ignored."""
        mock_run.return_value = """tcp   ESTAB      0      0      10.8.0.2:51234              192.168.1.1:51820"""

        result = get_vpn_server_endpoint("tun0", InterfaceType.VPN, "10.8.0.2")

        assert result is None

    @patch("network.vpn_underlay.run_command")
    def test_priority_vpn_ip_over_port(self, mock_run: MagicMock) -> None:
        """Test VPN IP match has priority over port match."""
        mock_run.return_value = """tcp   ESTAB      0      0      192.168.1.100:51234         8.8.4.4:51820
tcp   ESTAB      0      0      10.8.0.2:51235              8.8.8.8:443"""

        result = get_vpn_server_endpoint("tun0", InterfaceType.VPN, "10.8.0.2")

        # Connection from VPN IP should win
        assert result == "8.8.8.8"

    @patch("network.vpn_underlay.run_command")
    def test_no_local_ip(self, mock_run: MagicMock) -> None:
        """Test returns None when no local IP."""
        result = get_vpn_server_endpoint("tun0", InterfaceType.VPN, "N/A")

        assert result is None
        mock_run.assert_not_called()

    @patch("network.vpn_underlay.run_command")
    def test_command_failure(self, mock_run: MagicMock) -> None:
        """Test command failure returns None."""
        mock_run.return_value = None

        result = get_vpn_server_endpoint("tun0", InterfaceType.VPN, "10.8.0.2")

        assert result is None


class TestFindPhysicalInterfaceForVpn:
    """Tests for find_physical_interface_for_vpn function."""

    def test_ethernet_with_lowest_metric(self) -> None:
        """Test ethernet with lowest metric is selected."""
        interfaces = [
            InterfaceInfo.create_empty("eth0"),
            InterfaceInfo.create_empty("wlan0"),
        ]
        interfaces[0].interface_type = InterfaceType.ETHERNET
        interfaces[0].routing = RoutingInfo(gateway="192.168.1.1", metric="100")
        interfaces[1].interface_type = InterfaceType.WIRELESS
        interfaces[1].routing = RoutingInfo(gateway="10.42.0.1", metric="200")

        result = find_physical_interface_for_vpn("8.8.8.8", interfaces)

        assert result == "eth0"

    def test_wireless_selected(self) -> None:
        """Test wireless can be selected."""
        interfaces = [
            InterfaceInfo.create_empty("wlan0"),
        ]
        interfaces[0].interface_type = InterfaceType.WIRELESS
        interfaces[0].routing = RoutingInfo(gateway="10.42.0.1", metric="100")

        result = find_physical_interface_for_vpn("8.8.8.8", interfaces)

        assert result == "wlan0"

    def test_cellular_can_carry_vpn(self) -> None:
        """Test cellular interface can carry VPN."""
        interfaces = [
            InterfaceInfo.create_empty("wwp0s0"),
        ]
        interfaces[0].interface_type = InterfaceType.CELLULAR
        interfaces[0].routing = RoutingInfo(gateway="192.168.8.1", metric="100")

        result = find_physical_interface_for_vpn("8.8.8.8", interfaces)

        assert result == "wwp0s0"

    def test_tether_can_carry_vpn(self) -> None:
        """Test USB tether can carry VPN."""
        interfaces = [
            InterfaceInfo.create_empty("enx123"),
        ]
        interfaces[0].interface_type = InterfaceType.TETHER
        interfaces[0].routing = RoutingInfo(gateway="10.244.0.1", metric="100")

        result = find_physical_interface_for_vpn("8.8.8.8", interfaces)

        assert result == "enx123"

    def test_ignore_vpn_interfaces(self) -> None:
        """Test VPN interfaces are not selected as carriers."""
        interfaces = [
            InterfaceInfo.create_empty("tun0"),
        ]
        interfaces[0].interface_type = InterfaceType.VPN
        interfaces[0].routing = RoutingInfo(gateway="10.8.0.1", metric="50")

        result = find_physical_interface_for_vpn("8.8.8.8", interfaces)

        assert result is None

    def test_ignore_virtual_interfaces(self) -> None:
        """Test virtual interfaces are not selected."""
        interfaces = [
            InterfaceInfo.create_empty("veth0"),
        ]
        interfaces[0].interface_type = InterfaceType.VIRTUAL
        interfaces[0].routing = RoutingInfo(gateway="172.17.0.1", metric="100")

        result = find_physical_interface_for_vpn("8.8.8.8", interfaces)

        assert result is None

    def test_require_default_gateway(self) -> None:
        """Test interfaces must have default gateway."""
        interfaces = [
            InterfaceInfo.create_empty("eth0"),
        ]
        interfaces[0].interface_type = InterfaceType.ETHERNET
        interfaces[0].routing = RoutingInfo(gateway="NONE", metric="NONE")

        result = find_physical_interface_for_vpn("8.8.8.8", interfaces)

        assert result is None

    def test_default_metric_sorting(self) -> None:
        """Test DEFAULT metric sorts after numeric."""
        interfaces = [
            InterfaceInfo.create_empty("eth0"),
            InterfaceInfo.create_empty("wlan0"),
        ]
        interfaces[0].interface_type = InterfaceType.ETHERNET
        interfaces[0].routing = RoutingInfo(gateway="192.168.1.1", metric="DEFAULT")
        interfaces[1].interface_type = InterfaceType.WIRELESS
        interfaces[1].routing = RoutingInfo(gateway="10.42.0.1", metric="100")

        result = find_physical_interface_for_vpn("8.8.8.8", interfaces)

        # Numeric metric should win over DEFAULT
        assert result == "wlan0"


class TestDetectVpnUnderlay:
    """Tests for detect_vpn_underlay function."""

    @patch("network.vpn_underlay.get_vpn_server_endpoint")
    def test_sets_vpn_server_ip(self, mock_get_server: MagicMock) -> None:
        """Test VPN server IP is set on VPN interface."""
        mock_get_server.return_value = "8.8.8.8"

        interfaces = [
            InterfaceInfo.create_empty("tun0"),
        ]
        interfaces[0].interface_type = InterfaceType.VPN
        interfaces[0].ip = IPConfig(ipv4="10.8.0.2", ipv6="N/A")

        detect_vpn_underlay(interfaces)

        assert interfaces[0].vpn.server_ip == "8.8.8.8"

    @patch("network.vpn_underlay.get_vpn_server_endpoint")
    def test_marks_carrier_interface(self, mock_get_server: MagicMock) -> None:
        """Test carrier interface is marked with carries_vpn."""
        mock_get_server.return_value = "8.8.8.8"

        interfaces = [
            InterfaceInfo.create_empty("tun0"),
            InterfaceInfo.create_empty("eth0"),
        ]
        interfaces[0].interface_type = InterfaceType.VPN
        interfaces[0].ip = IPConfig(ipv4="10.8.0.2", ipv6="N/A")
        interfaces[1].interface_type = InterfaceType.ETHERNET
        interfaces[1].routing = RoutingInfo(gateway="192.168.1.1", metric="100")

        detect_vpn_underlay(interfaces)

        assert interfaces[1].vpn.carries_vpn is True

    @patch("network.vpn_underlay.get_vpn_server_endpoint")
    def test_no_server_detected(self, mock_get_server: MagicMock) -> None:
        """Test handles case when no server detected."""
        mock_get_server.return_value = None

        interfaces = [
            InterfaceInfo.create_empty("tun0"),
        ]
        interfaces[0].interface_type = InterfaceType.VPN
        interfaces[0].ip = IPConfig(ipv4="10.8.0.2", ipv6="N/A")

        # Should not raise error
        detect_vpn_underlay(interfaces)

        assert interfaces[0].vpn.server_ip is None
