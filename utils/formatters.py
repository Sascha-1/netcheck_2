"""Text formatting utilities for DISPLAY ONLY.

All cleanup functions work on DISPLAY DATA, never on raw data.
Raw data in models.py remains unchanged for data integrity.

Shared Cleanup Architecture:
- CORPORATE_SUFFIXES: Used by both device and ISP cleanup
- DEVICE_TECHNICAL_TERMS: Device-specific cleanup
- Combined for comprehensive device cleanup
- All matching is CASE-INSENSITIVE
"""

import re

import config


def cleanup_device_name(device_name: str) -> str:
    """Clean device name for DISPLAY (raw data unchanged).

    This is DISPLAY-LAYER ONLY. Raw data in InterfaceInfo remains unchanged.

    Process:
        1. Skip markers (N/A, --, NONE)
        2. Remove PCI/USB prefixes (00.0, Bus 001, etc.)
        3. Remove technical jargon (CASE-INSENSITIVE)
        4. Remove corporate suffixes (CASE-INSENSITIVE)
        5. Remove parentheses/brackets content
        6. Normalize whitespace

    Examples:
        "Intel Corporation Ethernet Controller I225-V" → "Intel I225-V"
        "Realtek CORP. RTL8111" → "Realtek RTL8111"
        "Broadcom Inc. BCM4360" → "Broadcom BCM4360"

    Args:
        device_name: Raw device name from hardware detection

    Returns:
        Cleaned name for display or original if result would be empty.
    """
    if device_name in ("N/A", "--", "NONE", "USB Device"):
        return device_name

    cleaned = device_name

    # Remove PCI prefix: "00:1f.6 " or "00.0 "
    cleaned = re.sub(r"^\d+[:.]\S+\s+", "", cleaned)

    # Remove USB prefix: "Bus 001 Device 003: "
    cleaned = re.sub(r"^Bus\s+\d+\s+Device\s+\d+:\s+", "", cleaned, flags=re.IGNORECASE)

    # Remove USB ID prefix: "ID 18d1:4eeb "
    cleaned = re.sub(r"ID\s+[0-9a-f]{4}:[0-9a-f]{4}\s+", "", cleaned, flags=re.IGNORECASE)

    # Remove parentheses content
    cleaned = re.sub(r"\([^)]*\)", "", cleaned)

    # Remove brackets content
    cleaned = re.sub(r"\[[^\]]*\]", "", cleaned)

    # Build combined cleanup terms (corporate + technical)
    all_terms = config.CORPORATE_SUFFIXES + config.DEVICE_TECHNICAL_TERMS

    # Remove cleanup terms (CASE-INSENSITIVE)
    # Sort by length (longest first to avoid partial matches)
    # Example: "Corporation" before "Corp" to match the longer form first
    terms = sorted(all_terms, key=len, reverse=True)
    for term in terms:
        # Pattern matches word boundaries to avoid partial word matches
        # Example: "Inc." matches "Broadcom Inc." but not "Incendiary"
        pattern = r"\b" + re.escape(term) + r"(?=\s|[.,\-]|$)"
        # CASE-INSENSITIVE: "Corp", "corp", "CORP" all match
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Normalize whitespace
    cleaned = " ".join(cleaned.split())
    cleaned = cleaned.strip(" ,:.-")

    # Return original if cleaning produces empty
    if not cleaned:
        return device_name

    return cleaned


def cleanup_isp_name(isp: str) -> str:
    """Clean ISP name for DISPLAY (raw data unchanged).

    This is DISPLAY-LAYER ONLY. Raw data in InterfaceInfo remains unchanged.

    Process:
        1. Skip markers (--, N/A, QUERY FAILED)
        2. Remove AS number prefix (AS12345)
        3. Remove corporate suffixes (CASE-INSENSITIVE)

    Examples:
        "AS12345 Comcast Corporation" → "Comcast"
        "AS701 Verizon Inc." → "Verizon"
        "Google LLC" → "Google"

    Args:
        isp: ISP name from ipinfo.io (may include AS number)

    Returns:
        Cleaned ISP name for display.
    """
    if isp in ("--", "N/A", "QUERY FAILED"):
        return isp

    cleaned = isp

    # Remove AS number prefix: "AS12345 Comcast" → "Comcast"
    cleaned = re.sub(r"^AS\d+\s+", "", cleaned)

    # Remove corporate suffixes (CASE-INSENSITIVE)
    # Uses same list as device cleanup for consistency
    terms = sorted(config.CORPORATE_SUFFIXES, key=len, reverse=True)
    for term in terms:
        pattern = r"\b" + re.escape(term) + r"(?=\s|[.,\-]|$)"
        # CASE-INSENSITIVE: "Corp", "corp", "CORP" all match
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Normalize whitespace
    cleaned = " ".join(cleaned.split())
    cleaned = cleaned.strip(" ,:.-")

    # Return original if cleaning produces empty
    if not cleaned:
        return isp

    return cleaned


def shorten_text(text: str, max_length: int) -> str:
    """Truncate text to fit column width.

    Tries to break at word boundary.
    Adds "..." if truncated.

    Args:
        text: Text to truncate
        max_length: Maximum length (including "..." if truncated)

    Returns:
        Truncated text with "..." if needed.
    """
    if len(text) <= max_length:
        return text

    # Truncate with space for "..."
    truncated = text[: max_length - 3]

    # Try to break at word boundary
    last_space = truncated.rfind(" ")
    if last_space > max_length * 0.7:  # Good break point
        return truncated[:last_space] + "..."

    return truncated + "..."
