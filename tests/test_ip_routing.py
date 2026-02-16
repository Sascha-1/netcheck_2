"""Tests for network/ip_routing.py.

Tests IP address and routing table parsing with mocked commands.
"""

from unittest.mock import patch

import pytest

from network.ip_routing import (
    get_active_interface,
    get_all_ipv4_addresses,
    get_all_ipv6_addresses,
    get_route_info,
)


class TestGetAllIpv4Addresses:
    """Tests for get_all_ipv4_addresses function."""

    @patch("network.ip_routing.run_command")
    def test_parse_single_interface(self, mock_run) -> None:
        """Test parsing single interface IPv4."""
        mock_run.return_value = """1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536
    inet 127.0.0.1/8 scope host lo
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500
    inet 192.168.1.100/24 brd 192.168.1.255 scope global eth0"""

        result = get_all_ipv4_addresses()

        assert result["lo"] == "127.0.0.1"
        assert result["eth0"] == "192.168.1.100"

    @patch("network.ip_routing.run_command")
    def test_multiple_addresses_takes_first(self, mock_run) -> None:
        """Test multiple addresses on one interface takes first."""
        mock_run.return_value = """2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP>
    inet 192.168.1.100/24 scope global eth0
    inet 192.168.1.101/24 scope global eth0"""

        result = get_all_ipv4_addresses()

        assert result["eth0"] == "192.168.1.100"

    @patch("network.ip_routing.run_command")
    def test_command_failure(self, mock_run) -> None:
        """Test command failure returns empty dict."""
        mock_run.return_value = None

        result = get_all_ipv4_addresses()

        assert result == {}

    @patch("network.ip_routing.run_command")
    def test_no_inet_addresses(self, mock_run) -> None:
        """Test interfaces without inet addresses."""
        mock_run.return_value = """2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP>"""

        result = get_all_ipv4_addresses()

        assert "eth0" not in result


class TestGetAllIpv6Addresses:
    """Tests for get_all_ipv6_addresses function."""

    @patch("network.ip_routing.run_command")
    def test_parse_global_ipv6(self, mock_run) -> None:
        """Test parsing global IPv6 addresses."""
        mock_run.return_value = """2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP>
    inet6 2001:db8::1/64 scope global
    inet6 fe80::1/64 scope link"""

        result = get_all_ipv6_addresses()

        assert result["eth0"] == "2001:db8::1"

    @patch("network.ip_routing.run_command")
    def test_ignore_link_local(self, mock_run) -> None:
        """Test link-local addresses are ignored."""
        mock_run.return_value = """2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP>
    inet6 fe80::1/64 scope link"""

        result = get_all_ipv6_addresses()

        assert "eth0" not in result

    @patch("network.ip_routing.run_command")
    def test_ignore_temporary(self, mock_run) -> None:
        """Test temporary addresses are ignored."""
        mock_run.return_value = """2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP>
    inet6 2001:db8::temp/64 scope global temporary"""

        result = get_all_ipv6_addresses()

        assert "eth0" not in result

    @patch("network.ip_routing.run_command")
    def test_ignore_deprecated(self, mock_run) -> None:
        """Test deprecated addresses are ignored."""
        mock_run.return_value = """2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP>
    inet6 2001:db8::old/64 scope global deprecated"""

        result = get_all_ipv6_addresses()

        assert "eth0" not in result

    @patch("network.ip_routing.run_command")
    def test_command_failure(self, mock_run) -> None:
        """Test command failure returns empty dict."""
        mock_run.return_value = None

        result = get_all_ipv6_addresses()

        assert result == {}


class TestGetRouteInfo:
    """Tests for get_route_info function."""

    @patch("network.ip_routing.run_command")
    def test_route_with_explicit_metric(self, mock_run) -> None:
        """Test route with explicit metric."""
        mock_run.return_value = "default via 192.168.1.1 dev eth0 metric 100"

        gateway, metric = get_route_info("eth0")

        assert gateway == "192.168.1.1"
        assert metric == "100"

    @patch("network.ip_routing.run_command")
    def test_route_without_metric(self, mock_run) -> None:
        """Test route without explicit metric returns DEFAULT."""
        mock_run.return_value = "default via 192.168.1.1 dev eth0"

        gateway, metric = get_route_info("eth0")

        assert gateway == "192.168.1.1"
        assert metric == "DEFAULT"

    @patch("network.ip_routing.run_command")
    def test_no_default_route(self, mock_run) -> None:
        """Test no default route returns NONE."""
        mock_run.return_value = "192.168.1.0/24 dev eth0"

        gateway, metric = get_route_info("eth0")

        assert gateway == "NONE"
        assert metric == "NONE"

    @patch("network.ip_routing.run_command")
    def test_command_failure(self, mock_run) -> None:
        """Test command failure returns NONE."""
        mock_run.return_value = None

        gateway, metric = get_route_info("eth0")

        assert gateway == "NONE"
        assert metric == "NONE"

    @patch("network.ip_routing.run_command")
    def test_route_without_gateway(self, mock_run) -> None:
        """Test route without gateway (on-link route)."""
        mock_run.return_value = "default dev eth0 metric 100"

        gateway, metric = get_route_info("eth0")

        assert gateway == "NONE"
        assert metric == "100"


class TestGetActiveInterface:
    """Tests for get_active_interface function."""

    @patch("network.ip_routing.run_command")
    def test_single_default_route(self, mock_run) -> None:
        """Test single default route."""
        mock_run.return_value = "default via 192.168.1.1 dev eth0 metric 100"

        result = get_active_interface()

        assert result == "eth0"

    @patch("network.ip_routing.run_command")
    def test_multiple_routes_lowest_metric(self, mock_run) -> None:
        """Test multiple routes selects lowest metric."""
        mock_run.return_value = """default via 192.168.1.1 dev eth0 metric 100
default via 10.8.0.1 dev tun0 metric 50"""

        result = get_active_interface()

        assert result == "tun0"  # Lower metric wins

    @patch("network.ip_routing.run_command")
    def test_multiple_routes_default_metric(self, mock_run) -> None:
        """Test multiple routes with DEFAULT metric."""
        mock_run.return_value = """default via 192.168.1.1 dev eth0
default via 10.8.0.1 dev tun0 metric 50"""

        result = get_active_interface()

        assert result == "tun0"  # Explicit metric beats DEFAULT

    @patch("network.ip_routing.run_command")
    def test_all_default_metrics_returns_first(self, mock_run) -> None:
        """Test all DEFAULT metrics returns first."""
        mock_run.return_value = """default via 192.168.1.1 dev eth0
default via 10.8.0.1 dev tun0"""

        result = get_active_interface()

        assert result == "eth0"  # First in list

    @patch("network.ip_routing.run_command")
    def test_no_default_route(self, mock_run) -> None:
        """Test no default route returns None."""
        mock_run.return_value = "192.168.1.0/24 dev eth0"

        result = get_active_interface()

        assert result is None

    @patch("network.ip_routing.run_command")
    def test_command_failure(self, mock_run) -> None:
        """Test command failure returns None."""
        mock_run.return_value = None

        result = get_active_interface()

        assert result is None
