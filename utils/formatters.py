"""Text formatting utilities.

Provides functions for cleaning and formatting text for display.
"""

import re

import config


def cleanup_device_name(device_name: str) -> str:
    """Clean device name by removing technical jargon.

    Removes:
        - Parentheses/brackets content
        - Corporate terms (Co., Inc., Corp.)
        - Technical jargon (Controller, 802.11ax, etc.)

    Args:
        device_name: Raw device name from lspci/lsusb

    Returns:
        Cleaned name or original if result would be empty.
    """
    if device_name in ("N/A", "--", "NONE"):
        return device_name

    cleaned = device_name

    # Remove parentheses content
    cleaned = re.sub(r"\([^)]*\)", "", cleaned)

    # Remove brackets content
    cleaned = re.sub(r"\[[^\]]*\]", "", cleaned)

    # Remove cleanup terms (case-insensitive)
    # Sort by length (longest first) to avoid partial matches
    terms = sorted(config.DEVICE_NAME_CLEANUP, key=len, reverse=True)
    for term in terms:
        pattern = r"\b" + re.escape(term) + r"(?=\s|[.,\-]|$)"
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Normalize whitespace
    cleaned = " ".join(cleaned.split())
    cleaned = cleaned.strip(" ,-")

    # Return original if cleaning produces empty
    if not cleaned:
        return device_name

    return cleaned


def cleanup_isp_name(isp: str) -> str:
    """Remove AS number prefix from ISP name.

    Example: "AS12345 Comcast" → "Comcast"

    Args:
        isp: ISP name from ipinfo.io (may include AS number)

    Returns:
        ISP name without AS prefix.
    """
    if isp in ("--", "N/A", "QUERY FAILED"):
        return isp

    match = re.match(r"^AS\d+\s+(.+)$", isp)
    if match:
        return match.group(1)

    return isp


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
