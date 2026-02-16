"""Pytest configuration and shared fixtures.

Provides common test fixtures and configuration for the test suite.
"""

import logging
import sys
from pathlib import Path
from typing import Generator

import pytest

# Add parent directory to path so imports work
# This allows: from enums import ... to find /project/enums.py
sys.path.insert(0, str(Path(__file__).parent.parent))

from enums import DnsLeakStatus, InterfaceType
from logging_config import setup_logging
from models import (
    DNSConfig,
    EgressInfo,
    InterfaceInfo,
    IPConfig,
    RoutingInfo,
    VPNInfo,
)


# Configure logging once for entire test session
# This prevents logging handler MagicMock errors
@pytest.fixture(scope="session", autouse=True)
def configure_logging() -> Generator[None, None, None]:
    """Configure logging for all tests.
    
    This ensures all loggers have properly initialized handlers with integer
    .level attributes, preventing TypeError: '>=' not supported between
    instances of 'int' and 'MagicMock'.
    
    Runs once before any tests (scope="session", autouse=True).
    """
    setup_logging(verbose=False)
    yield


@pytest.fixture
def sample_ethernet_interface() -> InterfaceInfo:
    """Create a sample ethernet interface for testing."""
    return InterfaceInfo(
        name="eth0",
        interface_type=InterfaceType.ETHERNET,
        device="Intel Corporation I225-V",
        ip=IPConfig(ipv4="192.168.1.100", ipv6="N/A"),
        dns=DNSConfig(
            servers=["192.168.1.1"],
            current_server="192.168.1.1",
            leak_status=DnsLeakStatus.NOT_APPLICABLE,
        ),
        egress=EgressInfo(
            external_ip="203.0.113.1",
            external_ipv6="N/A",
            isp="AS12345 Example ISP",
            country="US",
        ),
        routing=RoutingInfo(gateway="192.168.1.1", metric="100"),
        vpn=VPNInfo(server_ip=None, carries_vpn=False),
    )


@pytest.fixture
def sample_vpn_interface() -> InterfaceInfo:
    """Create a sample VPN interface for testing."""
    return InterfaceInfo(
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


@pytest.fixture
def sample_wireless_interface() -> InterfaceInfo:
    """Create a sample wireless interface for testing."""
    return InterfaceInfo(
        name="wlan0",
        interface_type=InterfaceType.WIRELESS,
        device="MEDIATEK Corp. MT7922",
        ip=IPConfig(ipv4="10.42.0.1", ipv6="N/A"),
        dns=DNSConfig.create_empty(),
        egress=EgressInfo.create_empty(),
        routing=RoutingInfo(gateway="NONE", metric="NONE"),
        vpn=VPNInfo.create_empty(),
    )


@pytest.fixture
def sample_cellular_interface() -> InterfaceInfo:
    """Create a sample cellular interface for testing."""
    return InterfaceInfo(
        name="wwp0s0",
        interface_type=InterfaceType.CELLULAR,
        device="Quectel Wireless Solutions Co., Ltd. Quectel EM05-G",
        ip=IPConfig(ipv4="192.168.8.100", ipv6="N/A"),
        dns=DNSConfig(
            servers=["192.168.8.1"],
            current_server="192.168.8.1",
            leak_status=DnsLeakStatus.NOT_APPLICABLE,
        ),
        egress=EgressInfo.create_empty(),
        routing=RoutingInfo(gateway="192.168.8.1", metric="200"),
        vpn=VPNInfo.create_empty(),
    )


@pytest.fixture
def sample_tether_interface() -> InterfaceInfo:
    """Create a sample USB tether interface for testing."""
    return InterfaceInfo(
        name="enxb2707db29505",
        interface_type=InterfaceType.TETHER,
        device="Google Inc. Pixel 9a",
        ip=IPConfig(ipv4="10.244.167.235", ipv6="N/A"),
        dns=DNSConfig.create_empty(),
        egress=EgressInfo.create_empty(),
        routing=RoutingInfo(gateway="10.244.167.62", metric="101"),
        vpn=VPNInfo.create_empty(),
    )


@pytest.fixture
def sample_loopback_interface() -> InterfaceInfo:
    """Create a sample loopback interface for testing."""
    return InterfaceInfo(
        name="lo",
        interface_type=InterfaceType.LOOPBACK,
        device="N/A",
        ip=IPConfig(ipv4="127.0.0.1", ipv6="N/A"),
        dns=DNSConfig.create_empty(),
        egress=EgressInfo.create_empty(),
        routing=RoutingInfo.create_empty(),
        vpn=VPNInfo.create_empty(),
    )


@pytest.fixture
def sample_interface_list(
    sample_loopback_interface: InterfaceInfo,
    sample_ethernet_interface: InterfaceInfo,
    sample_wireless_interface: InterfaceInfo,
    sample_vpn_interface: InterfaceInfo,
) -> list[InterfaceInfo]:
    """Create a list of sample interfaces for testing."""
    return [
        sample_loopback_interface,
        sample_ethernet_interface,
        sample_wireless_interface,
        sample_vpn_interface,
    ]
