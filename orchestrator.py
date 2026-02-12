"""Orchestrator for network data collection.

Coordinates all network modules to collect complete interface information.
"""

import config
from logging_config import get_logger
from models import DNSConfig, EgressInfo, InterfaceInfo, IPConfig, RoutingInfo
from network import (
    check_dns_leaks_all_interfaces,
    detect_interface_type,
    detect_vpn_underlay,
    get_active_interface,
    get_all_ipv4_addresses,
    get_all_ipv6_addresses,
    get_device_name,
    get_egress_info,
    get_interface_dns,
    get_interface_list,
    get_route_info,
)
from utils import command_exists, sanitize_for_log

logger = get_logger(__name__)


def check_dependencies() -> bool:
    """Check all required system commands exist.

    Returns:
        True if all dependencies present, False otherwise.

    Logs:
        ERROR for each missing command with install hint.
    """
    missing = []

    for cmd in config.REQUIRED_COMMANDS:
        if not command_exists(cmd):
            missing.append(cmd)
            logger.error("Error: Missing required command: %s", cmd)

            # Log install hint based on command
            if cmd == "resolvectl":
                logger.error("  Install: sudo apt install systemd-resolved")
            elif cmd == "ip":
                logger.error("  Install: sudo apt install iproute2")
            elif cmd == "lspci":
                logger.error("  Install: sudo apt install pciutils")
            elif cmd == "lsusb":
                logger.error("  Install: sudo apt install usbutils")
            elif cmd == "ethtool":
                logger.error("  Install: sudo apt install ethtool")
            elif cmd == "ss":
                logger.error("  Install: sudo apt install iproute2")

    return len(missing) == 0


def collect_network_data() -> list[InterfaceInfo]:
    """Collect complete network data for all interfaces.

    Returns:
        List of InterfaceInfo objects with complete data.

    Process:
        1. Get interface list
        2. Identify active interface
        3. Query external IP (active only)
        4. Batch query IPs (all interfaces)
        5. Process each interface (sequential)
        6. Check DNS leaks
        7. Detect VPN underlay
    """
    # Step 1: Get all interfaces
    interface_names = get_interface_list()
    if not interface_names:
        logger.error("No network interfaces found")
        return []

    logger.info("Found %d interfaces", len(interface_names))

    # Step 2: Identify active interface
    active_interface = get_active_interface()
    if active_interface:
        logger.info("Active interface: %s", sanitize_for_log(active_interface))
    else:
        logger.info("No active interface (no default route)")

    # Step 3: Query external IP (active interface only)
    egress = None
    if active_interface:
        logger.info("Querying external IP...")
        egress = get_egress_info()

    # Step 4: Batch query all IPs
    logger.debug("Batch querying IPv4 addresses...")
    all_ipv4 = get_all_ipv4_addresses()

    logger.debug("Batch querying IPv6 addresses...")
    all_ipv6 = get_all_ipv6_addresses()

    # Step 5: Process each interface (sequential)
    interfaces = []
    for iface_name in interface_names:
        try:
            interface = process_single_interface(
                iface_name, active_interface, egress, all_ipv4, all_ipv6
            )
            interfaces.append(interface)
        except (OSError, IOError, ValueError, RuntimeError) as e:
            logger.warning(
                "Failed to process %s: %s",
                sanitize_for_log(iface_name),
                sanitize_for_log(str(e)),
            )
            continue

    # Step 6: Check DNS leaks
    logger.debug("Checking DNS leaks...")
    check_dns_leaks_all_interfaces(interfaces)

    # Step 7: Detect VPN underlay
    logger.debug("Detecting VPN underlay...")
    detect_vpn_underlay(interfaces)

    return interfaces


def process_single_interface(
    iface_name: str,
    active_interface: str | None,
    egress: EgressInfo | None,
    all_ipv4: dict[str, str],
    all_ipv6: dict[str, str],
) -> InterfaceInfo:
    """Process single interface.

    Args:
        iface_name: Interface name to process
        active_interface: Name of active interface (or None)
        egress: Egress info for active interface (or None)
        all_ipv4: Batched IPv4 results
        all_ipv6: Batched IPv6 results

    Returns:
        Complete InterfaceInfo object.
    """
    # Create base interface
    interface = InterfaceInfo.create_empty(iface_name)

    # Detect type
    interface.interface_type = detect_interface_type(iface_name)
    logger.debug(
        "[%s] Type: %s",
        sanitize_for_log(iface_name),
        interface.interface_type.value,
    )

    # Get hardware device name
    interface.device = get_device_name(iface_name, interface.interface_type)
    logger.debug(
        "[%s] Device: %s",
        sanitize_for_log(iface_name),
        sanitize_for_log(interface.device),
    )

    # Set IP configuration
    interface.ip = IPConfig(
        ipv4=all_ipv4.get(iface_name, "N/A"),
        ipv6=all_ipv6.get(iface_name, "N/A"),
    )

    # Get DNS configuration
    dns_servers, current_dns = get_interface_dns(iface_name)
    interface.dns = DNSConfig(
        servers=dns_servers,
        current_server=current_dns,
        leak_status=interface.dns.leak_status,  # Keep default, will be set by check_dns_leaks
    )

    # Get routing info
    gateway, metric = get_route_info(iface_name)
    interface.routing = RoutingInfo(gateway=gateway, metric=metric)
    logger.debug(
        "[%s] Gateway: %s, Metric: %s",
        sanitize_for_log(iface_name),
        sanitize_for_log(gateway),
        sanitize_for_log(metric),
    )

    # Attach egress info if active interface
    if iface_name == active_interface and egress:
        interface.egress = egress
    else:
        interface.egress = EgressInfo.create_empty()

    return interface
