"""Tests for orchestrator.py - FIXED VERSION.

Tests orchestration logic, dependency checking, and data collection workflow.
Uses extensive mocking for external dependencies (system commands, network APIs).

FIXES APPLIED:
- Lines 207-208: Added explicit type annotations to empty dict collections
  - all_ipv4: dict[str, str] = {}
  - all_ipv6: dict[str, str] = {}
"""

from pathlib import Path
from unittest.mock import Mock, patch, call

import pytest

from config import REQUIRED_COMMANDS
from enums import DnsLeakStatus, InterfaceType
from models import DNSConfig, EgressInfo, InterfaceInfo, IPConfig, RoutingInfo, VPNInfo
from orchestrator import (
    check_dependencies,
    collect_network_data,
    process_single_interface,
)


class TestCheckDependencies:
    """Tests for check_dependencies function."""

    @patch("orchestrator.command_exists")
    def test_all_dependencies_present(self, mock_exists) -> None:
        """Test when all required commands exist."""
        mock_exists.return_value = True

        result = check_dependencies()

        assert result is True
        # Should check each required command
        assert mock_exists.call_count == len(REQUIRED_COMMANDS)

    @patch("orchestrator.command_exists")
    def test_missing_single_dependency(self, mock_exists, caplog) -> None:
        """Test when one required command is missing."""
        # All exist except 'resolvectl'
        mock_exists.side_effect = lambda cmd: cmd != "resolvectl"

        result = check_dependencies()

        assert result is False
        # Should log error for missing command
        assert "Missing required command: resolvectl" in caplog.text
        assert "sudo apt install systemd-resolved" in caplog.text

    @patch("orchestrator.command_exists")
    def test_missing_multiple_dependencies(self, mock_exists, caplog) -> None:
        """Test when multiple commands are missing."""
        # Only 'ip' and 'ss' are missing
        mock_exists.side_effect = lambda cmd: cmd not in ["ip", "ss"]

        result = check_dependencies()

        assert result is False
        assert "Missing required command: ip" in caplog.text
        assert "Missing required command: ss" in caplog.text
        assert "sudo apt install iproute2" in caplog.text

    @patch("orchestrator.command_exists")
    @pytest.mark.parametrize("missing_cmd,expected_hint", [
        ("resolvectl", "systemd-resolved"),
        ("ip", "iproute2"),
        ("lspci", "pciutils"),
        ("lsusb", "usbutils"),
        ("ethtool", "ethtool"),
        ("ss", "iproute2"),
        ("mmcli", "modemmanager"),
    ])
    def test_specific_install_hints(self, mock_exists, missing_cmd, expected_hint, caplog) -> None:
        """Test install hints for each command."""
        mock_exists.side_effect = lambda cmd: cmd != missing_cmd

        result = check_dependencies()

        assert result is False
        assert f"Missing required command: {missing_cmd}" in caplog.text
        assert expected_hint in caplog.text

    @patch("orchestrator.command_exists")
    def test_all_dependencies_missing(self, mock_exists, caplog) -> None:
        """Test when all required commands are missing."""
        mock_exists.return_value = False

        result = check_dependencies()

        assert result is False
        # Should log error for each command
        for cmd in REQUIRED_COMMANDS:
            assert f"Missing required command: {cmd}" in caplog.text


class TestProcessSingleInterface:
    """Tests for process_single_interface function."""

    @patch("orchestrator.get_device_name")
    @patch("orchestrator.get_route_info")
    @patch("orchestrator.get_interface_dns")
    @patch("orchestrator.detect_interface_type")
    def test_process_non_active_interface(
        self,
        mock_detect_type,
        mock_dns,
        mock_route,
        mock_device,
    ):
        """Test processing non-active interface."""
        # Setup mocks
        mock_detect_type.return_value = InterfaceType.ETHERNET
        mock_device.return_value = "Intel I225-V"
        mock_dns.return_value = (["192.168.1.1"], "192.168.1.1")
        mock_route.return_value = ("192.168.1.1", "100")

        # Process interface (not active, no egress data)
        all_ipv4 = {"eth0": "192.168.1.100"}
        all_ipv6 = {"eth0": "N/A"}

        result = process_single_interface(
            iface_name="eth0",
            active_interface="wlan0",  # Different interface is active
            egress=None,
            all_ipv4=all_ipv4,
            all_ipv6=all_ipv6,
        )

        # Verify result
        assert result.name == "eth0"
        assert result.interface_type == InterfaceType.ETHERNET
        assert result.device == "Intel I225-V"
        assert result.ip.ipv4 == "192.168.1.100"
        assert result.ip.ipv6 == "N/A"
        assert result.dns.servers == ["192.168.1.1"]
        assert result.dns.current_server == "192.168.1.1"
        assert result.routing.gateway == "192.168.1.1"
        assert result.routing.metric == "100"
        # Egress should be empty for non-active interface
        assert result.egress.external_ip == "--"
        assert result.egress.isp == "--"

    @patch("orchestrator.get_device_name")
    @patch("orchestrator.get_route_info")
    @patch("orchestrator.get_interface_dns")
    @patch("orchestrator.detect_interface_type")
    def test_process_active_interface_with_egress(
        self,
        mock_detect_type,
        mock_dns,
        mock_route,
        mock_device,
    ):
        """Test processing active interface with egress data."""
        # Setup mocks
        mock_detect_type.return_value = InterfaceType.VPN
        mock_device.return_value = "N/A"
        mock_dns.return_value = (["10.2.0.1"], "10.2.0.1")
        mock_route.return_value = ("100.85.0.1", "98")

        # Create egress info
        egress = EgressInfo(
            external_ip="159.26.108.32",
            external_ipv6="2a02:6ea0:c501:6262::12",
            isp="Proton",
            country="SE",
        )

        # Process active interface
        all_ipv4 = {"pvpnksintrf0": "100.85.0.1"}
        all_ipv6 = {"pvpnksintrf0": "fdeb:446c:912d:8da::"}

        result = process_single_interface(
            iface_name="pvpnksintrf0",
            active_interface="pvpnksintrf0",  # This is the active interface
            egress=egress,
            all_ipv4=all_ipv4,
            all_ipv6=all_ipv6,
        )

        # Verify result
        assert result.name == "pvpnksintrf0"
        assert result.interface_type == InterfaceType.VPN
        assert result.ip.ipv4 == "100.85.0.1"
        assert result.egress == egress  # Should have egress data
        assert result.egress.external_ip == "159.26.108.32"
        assert result.egress.country == "SE"

    @patch("orchestrator.get_device_name")
    @patch("orchestrator.get_route_info")
    @patch("orchestrator.get_interface_dns")
    @patch("orchestrator.detect_interface_type")
    def test_process_interface_with_no_ip(
        self,
        mock_detect_type,
        mock_dns,
        mock_route,
        mock_device,
    ):
        """Test processing interface with no IP assigned."""
        mock_detect_type.return_value = InterfaceType.ETHERNET
        mock_device.return_value = "Intel I225-V"
        mock_dns.return_value = ([], None)
        mock_route.return_value = ("NONE", "NONE")

        # Interface has no IP - FIXED: Added type annotations
        all_ipv4: dict[str, str] = {}  # Interface not in dict
        all_ipv6: dict[str, str] = {}

        result = process_single_interface(
            iface_name="eno1",
            active_interface=None,
            egress=None,
            all_ipv4=all_ipv4,
            all_ipv6=all_ipv6,
        )

        # Should use "N/A" for missing IPs
        assert result.ip.ipv4 == "N/A"
        assert result.ip.ipv6 == "N/A"
        assert result.routing.gateway == "NONE"
        assert result.routing.metric == "NONE"

    @patch("orchestrator.get_device_name")
    @patch("orchestrator.get_route_info")
    @patch("orchestrator.get_interface_dns")
    @patch("orchestrator.detect_interface_type")
    def test_process_loopback_interface(
        self,
        mock_detect_type,
        mock_dns,
        mock_route,
        mock_device,
    ):
        """Test processing loopback interface."""
        mock_detect_type.return_value = InterfaceType.LOOPBACK
        mock_device.return_value = "N/A"
        mock_dns.return_value = ([], None)
        mock_route.return_value = ("NONE", "NONE")

        all_ipv4 = {"lo": "127.0.0.1"}
        all_ipv6 = {"lo": "N/A"}

        result = process_single_interface(
            iface_name="lo",
            active_interface=None,
            egress=None,
            all_ipv4=all_ipv4,
            all_ipv6=all_ipv6,
        )

        assert result.interface_type == InterfaceType.LOOPBACK
        assert result.ip.ipv4 == "127.0.0.1"
        assert result.device == "N/A"


class TestCollectNetworkData:
    """Tests for collect_network_data function."""

    @patch("orchestrator.detect_vpn_underlay")
    @patch("orchestrator.check_dns_leaks_all_interfaces")
    @patch("orchestrator.get_all_ipv6_addresses")
    @patch("orchestrator.get_all_ipv4_addresses")
    @patch("orchestrator.get_egress_info")
    @patch("orchestrator.get_active_interface")
    @patch("orchestrator.get_interface_list")
    @patch("orchestrator.process_single_interface")
    def test_collect_with_single_interface(
        self,
        mock_process,
        mock_list,
        mock_active,
        mock_egress,
        mock_ipv4,
        mock_ipv6,
        mock_dns_leaks,
        mock_vpn_underlay,
    ):
        """Test collecting data with single interface."""
        # Setup mocks
        mock_list.return_value = ["eth0"]
        mock_active.return_value = "eth0"
        mock_egress.return_value = EgressInfo.create_error()
        mock_ipv4.return_value = {"eth0": "192.168.1.1"}
        mock_ipv6.return_value = {"eth0": "N/A"}

        # Mock process_single_interface
        test_interface = InterfaceInfo.create_empty("eth0")
        test_interface.interface_type = InterfaceType.ETHERNET
        mock_process.return_value = test_interface

        result = collect_network_data()

        # Verify workflow
        assert len(result) == 1
        assert result[0].name == "eth0"

        # Verify all steps were called
        mock_list.assert_called_once()
        mock_active.assert_called_once()
        mock_egress.assert_called_once()
        mock_ipv4.assert_called_once()
        mock_ipv6.assert_called_once()
        mock_dns_leaks.assert_called_once()
        mock_vpn_underlay.assert_called_once()

    @patch("orchestrator.detect_vpn_underlay")
    @patch("orchestrator.check_dns_leaks_all_interfaces")
    @patch("orchestrator.get_all_ipv6_addresses")
    @patch("orchestrator.get_all_ipv4_addresses")
    @patch("orchestrator.get_egress_info")
    @patch("orchestrator.get_active_interface")
    @patch("orchestrator.get_interface_list")
    @patch("orchestrator.process_single_interface")
    def test_collect_with_multiple_interfaces(
        self,
        mock_process,
        mock_list,
        mock_active,
        mock_egress,
        mock_ipv4,
        mock_ipv6,
        mock_dns_leaks,
        mock_vpn_underlay,
    ):
        """Test collecting data with multiple interfaces."""
        # Setup mocks
        interface_names = ["lo", "eth0", "wlan0", "tun0"]
        mock_list.return_value = interface_names
        mock_active.return_value = "tun0"
        mock_egress.return_value = EgressInfo(
            external_ip="203.0.113.1",
            external_ipv6="N/A",
            isp="ProtonVPN",
            country="CH",
        )
        mock_ipv4.return_value = {
            "lo": "127.0.0.1",
            "eth0": "192.168.1.100",
            "wlan0": "N/A",
            "tun0": "10.8.0.2",
        }
        mock_ipv6.return_value = {iface: "N/A" for iface in interface_names}

        # Mock process_single_interface to return different types
        def create_interface(name, active, egress, ipv4, ipv6):
            iface = InterfaceInfo.create_empty(name)
            if name == "lo":
                iface.interface_type = InterfaceType.LOOPBACK
            elif name == "tun0":
                iface.interface_type = InterfaceType.VPN
            elif name == "wlan0":
                iface.interface_type = InterfaceType.WIRELESS
            else:
                iface.interface_type = InterfaceType.ETHERNET
            return iface

        mock_process.side_effect = create_interface

        result = collect_network_data()

        # Verify results
        assert len(result) == 4
        assert result[0].interface_type == InterfaceType.LOOPBACK
        assert result[1].interface_type == InterfaceType.ETHERNET
        assert result[2].interface_type == InterfaceType.WIRELESS
        assert result[3].interface_type == InterfaceType.VPN

        # Verify process_single_interface was called for each interface
        assert mock_process.call_count == 4

    @patch("orchestrator.get_interface_list")
    def test_collect_with_no_interfaces(self, mock_list) -> None:
        """Test collecting data when no interfaces found."""
        mock_list.return_value = []

        result = collect_network_data()

        assert result == []

    @patch("orchestrator.get_interface_list")
    @patch("orchestrator.get_active_interface")
    def test_collect_with_no_active_interface(self, mock_active, mock_list, caplog) -> None:
        """Test collecting data when no active interface (no default route)."""
        # FIXED: Set log level to INFO to capture logger.info() messages
        import logging
        caplog.set_level(logging.INFO)
        
        mock_list.return_value = ["eth0", "wlan0"]
        mock_active.return_value = None  # No active interface

        # Should not call get_egress_info
        with patch("orchestrator.get_egress_info") as mock_egress:
            with patch("orchestrator.get_all_ipv4_addresses") as mock_ipv4:
                with patch("orchestrator.get_all_ipv6_addresses") as mock_ipv6:
                    with patch("orchestrator.process_single_interface") as mock_process:
                        # FIXED: Added type annotations to empty dicts
                        mock_ipv4.return_value: dict[str, str] = {}
                        mock_ipv6.return_value: dict[str, str] = {}
                        mock_process.return_value = InterfaceInfo.create_empty("eth0")

                        with patch("orchestrator.check_dns_leaks_all_interfaces"):
                            with patch("orchestrator.detect_vpn_underlay"):
                                result = collect_network_data()

            # get_egress_info should NOT be called
            mock_egress.assert_not_called()
            assert "No active interface (no default route)" in caplog.text

    @patch("orchestrator.detect_vpn_underlay")
    @patch("orchestrator.check_dns_leaks_all_interfaces")
    @patch("orchestrator.get_all_ipv6_addresses")
    @patch("orchestrator.get_all_ipv4_addresses")
    @patch("orchestrator.get_egress_info")
    @patch("orchestrator.get_active_interface")
    @patch("orchestrator.get_interface_list")
    @patch("orchestrator.process_single_interface")
    def test_collect_with_processing_error(
        self,
        mock_process,
        mock_list,
        mock_active,
        mock_egress,
        mock_ipv4,
        mock_ipv6,
        mock_dns_leaks,
        mock_vpn_underlay,
        caplog,
    ):
        """Test collecting data when processing one interface fails."""
        mock_list.return_value = ["eth0", "wlan0", "tun0"]
        mock_active.return_value = "eth0"
        mock_egress.return_value = EgressInfo.create_empty()
        mock_ipv4.return_value = {}
        mock_ipv6.return_value = {}

        # Make wlan0 fail, others succeed
        def side_effect_func(name, *args):
            if name == "wlan0":
                raise OSError("Failed to query interface")
            iface = InterfaceInfo.create_empty(name)
            iface.interface_type = InterfaceType.ETHERNET if name == "eth0" else InterfaceType.VPN
            return iface

        mock_process.side_effect = side_effect_func

        result = collect_network_data()

        # Should have 2 interfaces (wlan0 failed)
        assert len(result) == 2
        assert "Failed to process wlan0" in caplog.text

        # DNS leaks and VPN underlay should still be called with partial results
        mock_dns_leaks.assert_called_once()
        mock_vpn_underlay.assert_called_once()

    @patch("orchestrator.detect_vpn_underlay")
    @patch("orchestrator.check_dns_leaks_all_interfaces")
    @patch("orchestrator.get_all_ipv6_addresses")
    @patch("orchestrator.get_all_ipv4_addresses")
    @patch("orchestrator.get_egress_info")
    @patch("orchestrator.get_active_interface")
    @patch("orchestrator.get_interface_list")
    @patch("orchestrator.process_single_interface")
    def test_collect_vpn_scenario(
        self,
        mock_process,
        mock_list,
        mock_active,
        mock_egress,
        mock_ipv4,
        mock_ipv6,
        mock_dns_leaks,
        mock_vpn_underlay,
    ):
        """Test collecting data in VPN scenario (like the log file)."""
        # From the log file: 7 interfaces
        interface_names = ["lo", "eno2", "eno1", "wlp8s0", "pvpnksintrf0", "proton0", "enx6ef4f7e5cb21"]
        mock_list.return_value = interface_names
        mock_active.return_value = "pvpnksintrf0"

        # Mock egress for VPN
        mock_egress.return_value = EgressInfo(
            external_ip="159.26.108.32",
            external_ipv6="2a02:6ea0:c501:6262::12",
            isp="Proton",
            country="SE",
        )

        # Mock IP addresses
        mock_ipv4.return_value = {
            "lo": "127.0.0.1",
            "eno2": "192.168.8.111",
            "eno1": "N/A",
            "wlp8s0": "10.42.0.1",
            "pvpnksintrf0": "100.85.0.1",
            "proton0": "10.2.0.2",
            "enx6ef4f7e5cb21": "10.105.202.42",
        }
        mock_ipv6.return_value = {
            "lo": "N/A",
            "eno2": "N/A",
            "eno1": "N/A",
            "wlp8s0": "N/A",
            "pvpnksintrf0": "fdeb:446c:912d:8da::",
            "proton0": "2a07:b944::2:2",
            "enx6ef4f7e5cb21": "N/A",
        }

        # Mock process_single_interface
        def create_typed_interface(name, *args):
            iface = InterfaceInfo.create_empty(name)
            if name == "lo":
                iface.interface_type = InterfaceType.LOOPBACK
            elif name in ["pvpnksintrf0", "proton0"]:
                iface.interface_type = InterfaceType.VPN
            elif name in ["eno2", "eno1"]:
                iface.interface_type = InterfaceType.ETHERNET
            elif name == "wlp8s0":
                iface.interface_type = InterfaceType.WIRELESS
            elif name == "enx6ef4f7e5cb21":
                iface.interface_type = InterfaceType.TETHER
            return iface

        mock_process.side_effect = create_typed_interface

        result = collect_network_data()

        # Verify all 7 interfaces collected
        assert len(result) == 7

        # Verify VPN-specific calls
        mock_dns_leaks.assert_called_once()
        mock_vpn_underlay.assert_called_once()

        # Verify active interface has egress data
        vpn_interface = next((i for i in result if i.name == "pvpnksintrf0"), None)
        assert vpn_interface is not None
        # Note: In the mock, egress is attached by process_single_interface
        # which we're mocking, so we can't verify the actual egress data here
        # But we verified the workflow calls get_egress_info


class TestCollectNetworkDataIntegration:
    """Integration-style tests for collect_network_data (requires @pytest.mark.integration)."""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not Path("/sys/class/net/lo").exists(),
        reason="Requires real Linux system"
    )
    def test_collect_real_loopback(self) -> None:
        """Test collecting real loopback interface (integration test).

        This test runs on real system hardware.
        Mark with @pytest.mark.integration to skip in CI.
        """
        result = collect_network_data()

        # Should always have at least loopback
        assert len(result) >= 1

        # Find loopback
        lo = next((i for i in result if i.name == "lo"), None)
        assert lo is not None
        assert lo.interface_type == InterfaceType.LOOPBACK
        assert lo.ip.ipv4 == "127.0.0.1"
