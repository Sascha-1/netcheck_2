"""Tests for utils/formatters.py.

Tests text formatting utilities for display layer cleanup.
"""

import pytest

from utils.formatters import cleanup_device_name, cleanup_isp_name, shorten_text


class TestCleanupDeviceName:
    """Tests for cleanup_device_name function."""

    def test_passthrough_markers(self) -> None:
        """Test data markers are passed through unchanged."""
        assert cleanup_device_name("N/A") == "N/A"
        assert cleanup_device_name("--") == "--"
        assert cleanup_device_name("NONE") == "NONE"
        assert cleanup_device_name("USB Device") == "USB Device"

    def test_remove_pci_prefix(self) -> None:
        """Test PCI address prefixes are removed."""
        result = cleanup_device_name("00:1f.6 Intel Controller")
        assert "00:1f.6" not in result
        assert "Intel" in result

    def test_remove_usb_prefix(self) -> None:
        """Test USB prefixes are removed."""
        result = cleanup_device_name("Bus 001 Device 003: Google Pixel")
        assert "Bus 001" not in result or "Device 003" not in result
        assert "Google" in result or "Pixel" in result

    def test_remove_corporate_suffixes(self) -> None:
        """Test corporate legal suffixes are removed (case-insensitive)."""
        assert cleanup_device_name("Intel Corporation") == "Intel"
        assert cleanup_device_name("Qualcomm Inc.") == "Qualcomm"
        assert cleanup_device_name("Google LLC") == "Google"
        assert cleanup_device_name("Atheros Co.") == "Atheros"

    def test_remove_technical_terms(self) -> None:
        """Test technical jargon is removed (case-insensitive)."""
        result = cleanup_device_name("Intel Ethernet Controller I225-V")
        assert "Controller" not in result
        assert "Intel" in result
        assert "I225-V" in result

    def test_remove_parentheses_content(self) -> None:
        """Test content in parentheses is removed."""
        result = cleanup_device_name("Intel I225-V (rev 03)")
        assert "rev 03" not in result
        assert "Intel" in result

    def test_case_insensitive_matching(self) -> None:
        """Test matching is case-insensitive."""
        assert cleanup_device_name("Intel CORPORATION") == "Intel"
        assert cleanup_device_name("Intel corporation") == "Intel"
        assert cleanup_device_name("Intel Corp") == "Intel"

    def test_complex_real_example(self) -> None:
        """Test real-world complex device names."""
        input_name = "00:1f.6 Ethernet Controller: Intel Corporation I225-V (rev 03)"
        result = cleanup_device_name(input_name)
        assert "Intel" in result
        assert "I225-V" in result
        assert "00:1f.6" not in result
        assert "Corporation" not in result
        assert "rev 03" not in result

    def test_returns_original_if_empty(self) -> None:
        """Test original is returned if cleaning produces empty string."""
        original = "Corporation Inc. Ltd."
        result = cleanup_device_name(original)
        assert result == original

    def test_wireless_device(self) -> None:
        """Test wireless device name cleanup."""
        input_name = "MEDIATEK Corp. MT7922 802.11ax PCI Express Wireless Network Adapter"
        result = cleanup_device_name(input_name)
        assert "MEDIATEK" in result
        assert "MT7922" in result
        assert "Corp" not in result
        assert "802.11ax" not in result


class TestCleanupIspName:
    """Tests for cleanup_isp_name function."""

    def test_passthrough_markers(self) -> None:
        """Test data markers are passed through unchanged."""
        assert cleanup_isp_name("--") == "--"
        assert cleanup_isp_name("N/A") == "N/A"
        assert cleanup_isp_name("QUERY FAILED") == "QUERY FAILED"

    def test_remove_as_number(self) -> None:
        """Test AS number prefix is removed."""
        assert cleanup_isp_name("AS12345 Comcast") == "Comcast"
        assert cleanup_isp_name("AS701 Verizon") == "Verizon"
        assert cleanup_isp_name("AS15169 Google") == "Google"

    def test_remove_corporate_suffixes(self) -> None:
        """Test corporate suffixes are removed (case-insensitive)."""
        assert cleanup_isp_name("Comcast Corporation") == "Comcast"
        assert cleanup_isp_name("Verizon Inc.") == "Verizon"
        assert cleanup_isp_name("Google LLC") == "Google"

    def test_case_insensitive_matching(self) -> None:
        """Test matching is case-insensitive."""
        assert cleanup_isp_name("Comcast CORPORATION") == "Comcast"
        assert cleanup_isp_name("Verizon corporation") == "Verizon"
        assert cleanup_isp_name("Google llc") == "Google"

    def test_combined_as_and_suffix(self) -> None:
        """Test both AS number and suffix are removed."""
        assert cleanup_isp_name("AS12345 Comcast Corporation") == "Comcast"
        assert cleanup_isp_name("AS701 Verizon Inc.") == "Verizon"

    def test_returns_original_if_empty(self) -> None:
        """Test original is returned if cleaning produces empty string."""
        original = "Corporation Inc."
        result = cleanup_isp_name(original)
        assert result == original

    def test_real_world_examples(self) -> None:
        """Test real-world ISP names."""
        assert cleanup_isp_name("AS7922 Comcast Cable Communications, LLC") == "Comcast Cable Communications"
        assert cleanup_isp_name("AS15169 Google LLC") == "Google"


class TestShortenText:
    """Tests for shorten_text function."""

    def test_text_shorter_than_max(self) -> None:
        """Test text shorter than max_length is unchanged."""
        assert shorten_text("short", 10) == "short"
        assert shorten_text("exact", 5) == "exact"

    def test_text_equal_to_max(self) -> None:
        """Test text equal to max_length is unchanged."""
        assert shorten_text("12345", 5) == "12345"

    def test_text_longer_than_max(self) -> None:
        """Test text longer than max_length is truncated."""
        result = shorten_text("this is a long text", 10)
        assert len(result) == 10
        assert result.endswith("...")

    def test_word_boundary_break(self) -> None:
        """Test truncation at word boundary."""
        # Text: "hello world this is long" (24 chars)
        # Max: 15
        # Implementation finds word boundary at "hello world" and adds "..."
        # Result: "hello world..." (14 chars - less than max is OK)
        result = shorten_text("hello world this is long", 15)
        assert len(result) <= 15
        assert result.endswith("...")
        assert "hello world" in result

    def test_no_good_word_boundary(self) -> None:
        """Test truncation without good word boundary."""
        result = shorten_text("verylongwordwithoutspaces", 10)
        assert result == "verylon..."
        assert len(result) == 10

    def test_edge_case_very_short_max(self) -> None:
        """Test edge case with very short max_length."""
        result = shorten_text("hello", 3)
        assert len(result) <= 3
