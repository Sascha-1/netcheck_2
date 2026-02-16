"""Tests for display.py.

Tests table formatting and display output.
"""

from io import StringIO
from unittest.mock import patch

import pytest

from display import _get_row_color, format_output
from enums import DnsLeakStatus, InterfaceType
from models import InterfaceInfo


class TestGetRowColor:
    """Tests for _get_row_color function."""

    def test_dns_leak_magenta(self) -> None:
        """Test DNS leak gets MAGENTA color."""
        iface = InterfaceInfo.create_empty("eth0")
        iface.dns.leak_status = DnsLeakStatus.LEAK

        from colors import Color
        color = _get_row_color(iface)
        assert color == Color.MAGENTA

    def test_dns_warn_yellow(self) -> None:
        """Test DNS warning gets YELLOW color."""
        iface = InterfaceInfo.create_empty("eth0")
        iface.dns.leak_status = DnsLeakStatus.WARN

        from colors import Color
        color = _get_row_color(iface)
        assert color == Color.YELLOW

    def test_dns_public_yellow(self) -> None:
        """Test public DNS gets YELLOW color."""
        iface = InterfaceInfo.create_empty("eth0")
        iface.dns.leak_status = DnsLeakStatus.PUBLIC

        from colors import Color
        color = _get_row_color(iface)
        assert color == Color.YELLOW

    def test_vpn_with_ok_dns_green(self) -> None:
        """Test VPN with OK DNS gets GREEN color."""
        iface = InterfaceInfo.create_empty("tun0")
        iface.interface_type = InterfaceType.VPN
        iface.dns.leak_status = DnsLeakStatus.OK

        from colors import Color
        color = _get_row_color(iface)
        assert color == Color.GREEN

    def test_vpn_with_external_ip_green(self) -> None:
        """Test VPN with external IP gets GREEN color."""
        iface = InterfaceInfo.create_empty("tun0")
        iface.interface_type = InterfaceType.VPN
        iface.egress.external_ip = "203.0.113.1"

        from colors import Color
        color = _get_row_color(iface)
        assert color == Color.GREEN

    def test_carries_vpn_cyan(self) -> None:
        """Test interface carrying VPN gets CYAN color."""
        iface = InterfaceInfo.create_empty("eth0")
        iface.vpn.carries_vpn = True

        from colors import Color
        color = _get_row_color(iface)
        assert color == Color.CYAN

    def test_direct_internet_red(self) -> None:
        """Test direct internet gets RED color."""
        iface = InterfaceInfo.create_empty("eth0")
        iface.egress.external_ip = "203.0.113.1"

        from colors import Color
        color = _get_row_color(iface)
        assert color == Color.RED

    def test_no_color_loopback(self) -> None:
        """Test loopback gets no color."""
        iface = InterfaceInfo.create_empty("lo")
        iface.interface_type = InterfaceType.LOOPBACK

        color = _get_row_color(iface)
        assert color == ""


class TestFormatOutput:
    """Tests for format_output function."""

    def test_basic_output(self) -> None:
        """Test basic table output."""
        interfaces = [InterfaceInfo.create_empty("eth0")]
        output = StringIO()

        format_output(interfaces, file=output)

        result = output.getvalue()
        assert "Network Interface Analysis" in result
        assert "eth0" in result
        assert "Legend:" in result

    def test_multiple_interfaces(self) -> None:
        """Test output with multiple interfaces."""
        interfaces = [
            InterfaceInfo.create_empty("eth0"),
            InterfaceInfo.create_empty("wlan0"),
        ]
        output = StringIO()

        format_output(interfaces, file=output)

        result = output.getvalue()
        assert "eth0" in result
        assert "wlan0" in result

    def test_legend_present(self) -> None:
        """Test legend is included in output."""
        interfaces = [InterfaceInfo.create_empty("eth0")]
        output = StringIO()

        format_output(interfaces, file=output)

        result = output.getvalue()
        assert "Legend:" in result
        assert "GREEN" in result
        assert "CYAN" in result
        assert "RED" in result
        assert "MAGENTA" in result
        assert "YELLOW" in result

    @patch("display.cleanup_device_name")
    @patch("display.cleanup_isp_name")
    def test_cleanup_called(self, mock_isp, mock_device) -> None:
        """Test cleanup functions are called."""
        mock_device.return_value = "Cleaned Device"
        mock_isp.return_value = "Cleaned ISP"

        iface = InterfaceInfo.create_empty("eth0")
        iface.device = "Raw Device Name"
        iface.egress.isp = "Raw ISP Name"

        output = StringIO()
        format_output([iface], file=output)

        mock_device.assert_called_with("Raw Device Name")
        mock_isp.assert_called_with("Raw ISP Name")

    def test_default_stdout(self) -> None:
        """Test output defaults to stdout."""
        interfaces = [InterfaceInfo.create_empty("eth0")]

        # Should not raise error
        with patch("sys.stdout", new=StringIO()):
            format_output(interfaces)
