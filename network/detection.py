"""Interface detection and hardware identification.

Classifies network interfaces and identifies hardware devices.
Uses rule-based detection pattern for maintainability.
"""

import re
from functools import lru_cache
from pathlib import Path
from typing import Callable

import config
from enums import InterfaceType
from logging_config import get_logger
from utils import run_command, sanitize_for_log, validate_interface_name

logger = get_logger(__name__)


def get_interface_list() -> list[str]:
    """Get list of all network interfaces.

    Command: ip -o link show

    Returns all interfaces regardless of state (UP/DOWN).

    Returns:
        List of validated interface names.
    """
    output = run_command(["ip", "-o", "link", "show"])
    if not output:
        return []

    interfaces = []
    for line in output.split("\n"):
        # Format: "1: lo: <LOOPBACK,UP,LOWER_UP> ..."
        match = re.match(r"^\d+:\s+([^:@]+)", line)
        if match:
            iface = match.group(1).strip()
            if validate_interface_name(iface):
                interfaces.append(iface)

    return interfaces


# Type alias for interface type detection predicate
TypeDetector = Callable[[str], tuple[bool, InterfaceType | None]]


def detect_interface_type(iface_name: str) -> InterfaceType:
    """Detect interface type using rule-based priority chain.
    
    Uses rule-based pattern for maintainability:
    - Easy to add/remove/reorder detection rules
    - Each detector is self-contained
    - No complex nested if/elif chains
    - Follows Open/Closed Principle
    
    Priority:
        1. Loopback (name == "lo")
        2. USB tethering (sysfs driver check)
        3. VPN name (vpn/tun/tap/ppp/wg)
        4. Wireless (sysfs phy80211)
        5. Kernel type (ip -d link show)
        6. Name patterns
        7. UNKNOWN (default)

    Args:
        iface_name: Interface name

    Returns:
        InterfaceType enum value
    """
    # Define detection rules as functions
    # Each returns (matched: bool, type: InterfaceType | None)
    detectors: list[TypeDetector] = [
        _detect_loopback,
        _detect_usb_tether,
        _detect_vpn_by_name,
        _detect_wireless,
        _detect_by_kernel_type,
        _detect_by_name_pattern,
    ]

    # Try each detector in priority order
    for detector in detectors:
        matched, iface_type = detector(iface_name)
        if matched and iface_type is not None:
            return iface_type

    # Default: unknown
    return InterfaceType.UNKNOWN


# Detection rule implementations
# Each returns (matched, type) tuple


def _detect_loopback(iface_name: str) -> tuple[bool, InterfaceType | None]:
    """Detect loopback interface."""
    if iface_name == "lo":
        return (True, InterfaceType.LOOPBACK)
    return (False, None)


def _detect_usb_tether(iface_name: str) -> tuple[bool, InterfaceType | None]:
    """Detect USB tethered device."""
    if is_usb_tethered_device(iface_name):
        return (True, InterfaceType.TETHER)
    return (False, None)


def _detect_vpn_by_name(iface_name: str) -> tuple[bool, InterfaceType | None]:
    """Detect VPN by name patterns."""
    name_lower = iface_name.lower()
    if "vpn" in name_lower or iface_name.startswith(("tun", "tap", "ppp", "wg")):
        return (True, InterfaceType.VPN)
    return (False, None)


def _detect_wireless(iface_name: str) -> tuple[bool, InterfaceType | None]:
    """Detect wireless interface via sysfs phy80211."""
    if _is_wireless(iface_name):
        return (True, InterfaceType.WIRELESS)
    return (False, None)


def _detect_by_kernel_type(iface_name: str) -> tuple[bool, InterfaceType | None]:
    """Detect type from kernel link information."""
    output = run_command(["ip", "-d", "link", "show", iface_name])
    if not output:
        return (False, None)

    output_lower = output.lower()

    # Check for VPN types
    if "wireguard" in output_lower or "tun" in output_lower or "tap" in output_lower:
        return (True, InterfaceType.VPN)

    # Check for virtual types
    if "veth" in output_lower:
        return (True, InterfaceType.VIRTUAL)

    # Check for bridge
    if "bridge" in output_lower:
        return (True, InterfaceType.BRIDGE)

    return (False, None)


def _detect_by_name_pattern(iface_name: str) -> tuple[bool, InterfaceType | None]:
    """Detect type by interface name prefix patterns."""
    for prefix, iface_type in config.INTERFACE_TYPE_PATTERNS.items():
        if iface_name.startswith(prefix):
            return (True, InterfaceType(iface_type))
    return (False, None)


def is_usb_tethered_device(iface: str) -> bool:
    """Check if interface is USB tethered device.

    Method:
        1. Check device path contains "/usb"
        2. Get driver name from sysfs
        3. Match against USB_TETHER_DRIVERS

    Args:
        iface: Interface name

    Returns:
        True if USB tethering device, False otherwise.
    """
    is_usb, driver, _ = _get_usb_info(iface)

    if not is_usb or not driver:
        return False

    return driver in config.USB_TETHER_DRIVERS


def get_device_name(iface_name: str, iface_type: InterfaceType) -> str:
    """Get hardware device name (RAW - no cleanup).

    Returns raw hardware names for data integrity.
    Cleanup happens ONLY in display layer (display.py).

    Algorithm:
        1. If loopback/VPN/virtual: return "N/A"
        2. Try USB device name
        3. Try PCI device name
        4. Return "N/A" if none found

    Args:
        iface_name: Interface name
        iface_type: Interface type

    Returns:
        Raw device name or "N/A" (cleanup happens in display layer).
    """
    # Virtual interfaces have no hardware
    if iface_type in (
        InterfaceType.LOOPBACK,
        InterfaceType.VPN,
        InterfaceType.VIRTUAL,
        InterfaceType.BRIDGE,
    ):
        return "N/A"

    # Try USB - FIXED: Check is_usb first, IDs second
    is_usb, _, usb_ids = _get_usb_info(iface_name)
    if is_usb:
        # Try to get specific device name
        if usb_ids:
            name = get_usb_device_name(iface_name)
            if name:
                return name
        # Fallback for USB devices without readable IDs
        return "USB Device"

    # Try PCI
    pci_ids = _get_pci_ids(iface_name)
    if pci_ids:
        name = get_pci_device_name(iface_name)
        if name:
            return name

    return "N/A"


# Helper functions


def _get_sysfs_base_path(iface: str) -> Path:
    """Get base sysfs path for interface.

    Args:
        iface: Interface name

    Returns:
        Path to /sys/class/net/<interface>
    """
    return Path(f"/sys/class/net/{iface}")


def _get_device_path(iface: str) -> Path | None:
    """Get device path from sysfs, following symlink.

    Args:
        iface: Interface name

    Returns:
        Resolved device path or None if not found.
    """
    device_link = _get_sysfs_base_path(iface) / "device"
    try:
        if device_link.exists() and device_link.is_symlink():
            return device_link.resolve()
    except (OSError, RuntimeError):
        pass
    return None


def _is_wireless(iface: str) -> bool:
    """Check if wireless via phy80211 marker.

    Args:
        iface: Interface name

    Returns:
        True if wireless interface, False otherwise.
    """
    phy_path = _get_sysfs_base_path(iface) / "phy80211"
    return phy_path.exists()


def _get_pci_ids(iface: str) -> tuple[str, str] | None:
    """Get PCI vendor:device IDs from sysfs.

    Args:
        iface: Interface name

    Returns:
        Tuple of (vendor, device) hex IDs or None if not PCI device.
    """
    device_path = _get_device_path(iface)
    if not device_path:
        return None

    try:
        vendor_file = device_path / "vendor"
        device_file = device_path / "device"

        if vendor_file.exists() and device_file.exists():
            vendor = vendor_file.read_text().strip().replace("0x", "")
            device = device_file.read_text().strip().replace("0x", "")
            return (vendor, device)
    except (OSError, IOError):
        pass

    return None


@lru_cache(maxsize=32)
def _get_usb_info(iface: str) -> tuple[bool, str | None, tuple[str, str] | None]:
    """Get USB info (cached for performance).

    Args:
        iface: Interface name

    Returns:
        Tuple of (is_usb, driver, (vendor, product)) where:
            is_usb: True if USB device
            driver: Driver name or None
            (vendor, product): USB IDs or None
    """
    device_path = _get_device_path(iface)
    if not device_path:
        return (False, None, None)

    # Check if USB device (path contains "/usb")
    is_usb = "/usb" in str(device_path)
    if not is_usb:
        return (False, None, None)

    # Get driver
    driver = None
    driver_link = device_path / "driver"
    if driver_link.exists() and driver_link.is_symlink():
        driver = driver_link.resolve().name

    # Get USB IDs
    ids = None
    try:
        vendor_file = device_path / "idVendor"
        product_file = device_path / "idProduct"

        if vendor_file.exists() and product_file.exists():
            vendor = vendor_file.read_text().strip()
            product = product_file.read_text().strip()
            # Validate format (4 hex digits)
            if len(vendor) == 4 and len(product) == 4:
                ids = (vendor, product)
    except (OSError, IOError):
        pass

    return (is_usb, driver, ids)


def get_pci_device_name(iface: str) -> str | None:
    """Lookup PCI device name via lspci (RAW - no cleanup).

    Returns raw lspci output for data integrity.
    Cleanup happens ONLY in display layer.

    Args:
        iface: Interface name

    Returns:
        Raw device name string or None if lookup fails.
    """
    pci_ids = _get_pci_ids(iface)
    if not pci_ids:
        return None

    vendor, device = pci_ids
    output = run_command(["lspci", "-d", f"{vendor}:{device}"])
    if not output:
        logger.warning("Failed to lookup PCI device name for %s", sanitize_for_log(iface))
        return None

    # Format: "00:1f.6 Ethernet controller: Intel Corporation ..."
    # FIXED: Find the LAST colon (after "controller:"), not the first
    # Split by space, find first element with trailing colon
    parts = output.split()
    for i, part in enumerate(parts):
        if part.endswith(":"):
            # Found "controller:" - everything after is the device name
            return " ".join(parts[i + 1:])

    # Fallback: just return everything (shouldn't happen with valid lspci output)
    return output


def get_usb_device_name(iface: str) -> str | None:
    """Lookup USB device name via lsusb (RAW - no cleanup).

    Returns raw lsusb output for data integrity.
    Cleanup happens ONLY in display layer.

    Args:
        iface: Interface name

    Returns:
        Raw device name string or None if lookup fails.
    """
    _, _, usb_ids = _get_usb_info(iface)
    if not usb_ids:
        return None

    vendor, product = usb_ids
    output = run_command(["lsusb", "-d", f"{vendor}:{product}"])
    if not output:
        logger.warning("Failed to lookup USB device name for %s", sanitize_for_log(iface))
        return None

    # Format: "Bus 001 Device 003: ID 18d1:4eeb Google Inc. Nexus/Pixel Device"
    # Extract after "ID xxxx:xxxx "
    match = re.search(r"ID\s+[0-9a-f]{4}:[0-9a-f]{4}\s+(.+)$", output, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return None
