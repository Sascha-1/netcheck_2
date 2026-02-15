"""Tests for utils/validators.py.

Tests input validation for interface names, IP addresses, and security checks.
"""

import pytest

from utils.validators import (
    is_valid_ip,
    is_valid_ipv4,
    is_valid_ipv6,
    validate_interface_name,
)


class TestValidateInterfaceName:
    """Tests for validate_interface_name function."""

    def test_valid_standard_names(self):
        """Test standard valid interface names."""
        assert validate_interface_name("eth0") is True
        assert validate_interface_name("wlan0") is True
        assert validate_interface_name("enp0s3") is True
        assert validate_interface_name("wlp2s0") is True

    def test_valid_special_characters(self):
        """Test valid special characters in interface names."""
        assert validate_interface_name("eth0.100") is True  # VLAN
        assert validate_interface_name("eth0:1") is True  # Alias
        assert validate_interface_name("eth0@if2") is True  # veth pair
        assert validate_interface_name("br-1234") is True  # Bridge
        assert validate_interface_name("docker_bridge") is True  # Underscore

    def test_valid_max_length(self):
        """Test maximum valid length (64 characters)."""
        assert validate_interface_name("a" * 64) is True
        assert validate_interface_name("eth" + "0" * 61) is True

    def test_invalid_empty(self):
        """Test empty string is invalid."""
        assert validate_interface_name("") is False

    def test_invalid_too_long(self):
        """Test names over 64 characters are invalid."""
        assert validate_interface_name("a" * 65) is False
        assert validate_interface_name("eth" + "0" * 62) is False

    def test_invalid_characters(self):
        """Test invalid characters are rejected."""
        assert validate_interface_name("eth 0") is False  # Space
        assert validate_interface_name("eth/0") is False  # Slash
        assert validate_interface_name("eth\\0") is False  # Backslash
        assert validate_interface_name("eth'0") is False  # Single quote
        assert validate_interface_name('eth"0') is False  # Double quote
        assert validate_interface_name("eth\n0") is False  # Newline
        assert validate_interface_name("eth\t0") is False  # Tab

    def test_security_injection_attempts(self):
        """Test command injection attempts are blocked."""
        assert validate_interface_name("eth0; rm -rf /") is False
        assert validate_interface_name("eth0 && malicious") is False
        assert validate_interface_name("eth0|cat /etc/passwd") is False
        assert validate_interface_name("../../../etc/passwd") is False


class TestIsValidIPv4:
    """Tests for is_valid_ipv4 function."""

    def test_valid_standard_addresses(self):
        """Test standard valid IPv4 addresses."""
        assert is_valid_ipv4("192.168.1.1") is True
        assert is_valid_ipv4("10.0.0.1") is True
        assert is_valid_ipv4("172.16.0.1") is True
        assert is_valid_ipv4("8.8.8.8") is True
        assert is_valid_ipv4("1.1.1.1") is True

    def test_valid_edge_cases(self):
        """Test edge case valid addresses."""
        assert is_valid_ipv4("0.0.0.0") is True
        assert is_valid_ipv4("255.255.255.255") is True
        assert is_valid_ipv4("127.0.0.1") is True

    def test_invalid_none(self):
        """Test None input is invalid."""
        assert is_valid_ipv4(None) is False

    def test_invalid_empty(self):
        """Test empty string is invalid."""
        assert is_valid_ipv4("") is False

    def test_invalid_format(self):
        """Test invalid formats are rejected."""
        assert is_valid_ipv4("192.168.1") is False  # Too few octets
        assert is_valid_ipv4("192.168.1.1.1") is False  # Too many octets
        assert is_valid_ipv4("192.168.1.256") is False  # Octet > 255
        assert is_valid_ipv4("192.168.-1.1") is False  # Negative octet
        assert is_valid_ipv4("192.168.1.a") is False  # Non-numeric

    def test_invalid_ipv6(self):
        """Test IPv6 addresses are rejected."""
        assert is_valid_ipv4("2001:db8::1") is False
        assert is_valid_ipv4("::1") is False


class TestIsValidIPv6:
    """Tests for is_valid_ipv6 function."""

    def test_valid_standard_addresses(self):
        """Test standard valid IPv6 addresses."""
        assert is_valid_ipv6("2001:db8::1") is True
        assert is_valid_ipv6("::1") is True
        assert is_valid_ipv6("fe80::1") is True
        assert is_valid_ipv6("2607:f8b0:4004:814::200e") is True

    def test_valid_with_zone_identifier(self):
        """Test zone identifiers are stripped and address is valid."""
        assert is_valid_ipv6("fe80::1%eth0") is True
        assert is_valid_ipv6("fe80::abcd:ef01:2345:6789%wlan0") is True

    def test_valid_edge_cases(self):
        """Test edge case valid addresses."""
        assert is_valid_ipv6("::") is True  # All zeros
        assert is_valid_ipv6("::ffff:192.0.2.1") is True  # IPv4-mapped

    def test_invalid_none(self):
        """Test None input is invalid."""
        assert is_valid_ipv6(None) is False

    def test_invalid_empty(self):
        """Test empty string is invalid."""
        assert is_valid_ipv6("") is False

    def test_invalid_format(self):
        """Test invalid formats are rejected."""
        assert is_valid_ipv6("gggg::1") is False  # Invalid hex
        assert is_valid_ipv6("2001:db8::1::2") is False  # Double ::
        assert is_valid_ipv6("192.168.1.1") is False  # IPv4

    def test_zone_identifier_stripping(self):
        """Test zone identifier is properly stripped before validation."""
        # Valid address with zone
        assert is_valid_ipv6("fe80::1%eth0") is True
        # Invalid address even with zone
        assert is_valid_ipv6("invalid::address::1%eth0") is False


class TestIsValidIP:
    """Tests for is_valid_ip function."""

    def test_valid_ipv4(self):
        """Test IPv4 addresses are recognized."""
        assert is_valid_ip("192.168.1.1") is True
        assert is_valid_ip("8.8.8.8") is True

    def test_valid_ipv6(self):
        """Test IPv6 addresses are recognized."""
        assert is_valid_ip("2001:db8::1") is True
        assert is_valid_ip("::1") is True
        assert is_valid_ip("fe80::1%eth0") is True

    def test_invalid_none(self):
        """Test None input is invalid."""
        assert is_valid_ip(None) is False

    def test_invalid_empty(self):
        """Test empty string is invalid."""
        assert is_valid_ip("") is False

    def test_invalid_format(self):
        """Test completely invalid formats are rejected."""
        assert is_valid_ip("not an ip") is False
        assert is_valid_ip("192.168") is False
        assert is_valid_ip("gggg::1") is False
