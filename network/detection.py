"""Interface detection and hardware identification.

Classifies network interfaces and identifies hardware devices.
"""

import re
from functools import lru_cache
from pathlib import Path

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


def detect_interface_type(iface_name: str) -> InterfaceType:
    """Detect interface type using priority chain.

    Priority:
        1. Loopback (name == "lo")
        2. USB tethering (sysfs driver check)
        3. VPN name (vpn/tun/tap/ppp/wg)
        4. Wireless (sysfs phy80211)
        5. Kernel type (ip -d link show)
        6. Name patterns
        7. UNKNOWN

    Args:
        iface_name: Interface name

    Returns:
        InterfaceType enum value
    """
    # Priority 1: Loopback
    if iface_name == "lo":
        return InterfaceType.LOOPBACK

    # Priority 2: USB tethering
    if is_usb_tethered_device(iface_name):
        return InterfaceType.TETHER

    # Priority 3: VPN name patterns
    name_lower = iface_name.lower()
    if "vpn" in name_lower or iface_name.startswith(("tun", "tap", "ppp", "wg")):
        return InterfaceType.VPN

    # Priority 4: Wireless (sysfs phy80211)
    if _is_wireless(iface_name):
        return InterfaceType.WIRELESS

    # Priority 5: Kernel link type
    output = run_command(["ip", "-d", "link", "show", iface_name])
    if output:
        output_lower = output.lower()
        if "wireguard" in output_lower or "tun" in output_lower or "tap" in output_lower:
            return InterfaceType.VPN
        if "veth" in output_lower:
            return InterfaceType.VIRTUAL
        if "bridge" in output_lower:
            return InterfaceType.BRIDGE

    # Priority 6: Name patterns
    for prefix, iface_type in config.INTERFACE_TYPE_PATTERNS.items():
        if iface_name.startswith(prefix):
            return InterfaceType(iface_type)

    # Priority 7: Unknown
    return InterfaceType.UNKNOWN


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
    """Get hardware device name.

    Algorithm:
        1. If loopback/VPN/virtual: return "N/A"
        2. Try USB device name
        3. Try PCI device name
        4. Return "N/A" if none found

    Args:
        iface_name: Interface name
        iface_type: Interface type

    Returns:
        Device name (raw - cleaned in display layer) or "N/A".
    """
    # Virtual interfaces have no hardware
    if iface_type in (
        InterfaceType.LOOPBACK,
        InterfaceType.VPN,
        InterfaceType.VIRTUAL,
        InterfaceType.BRIDGE,
    ):
        return "N/A"

    # Try USB
    is_usb, _, usb_ids = _get_usb_info(iface_name)
    if is_usb and usb_ids:
        name = get_usb_device_name(iface_name)
        if name:
            return name
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
    """Lookup PCI device name via lspci.

    Args:
        iface: Interface name

    Returns:
        Device name string or None if lookup fails.
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
    # Extract after first colon
    parts = output.split(":", 1)
    if len(parts) > 1:
        return parts[1].strip()

    return None


def get_usb_device_name(iface: str) -> str | None:
    """Lookup USB device name via lsusb.

    Args:
        iface: Interface name

    Returns:
        Device name string or None if lookup fails.
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
