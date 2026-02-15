"""Tests for config.py.

Tests configuration constants, exit codes, and data validation.
"""

import pytest

from config import (
    COLUMN_SEPARATOR,
    CORPORATE_SUFFIXES,
    DEVICE_TECHNICAL_TERMS,
    ExitCode,
    TABLE_COLUMNS,
    TOOL_NAME,
    VERSION,
)


class TestExitCode:
    """Tests for ExitCode enum."""

    def test_exit_code_values(self):
        """Test exit code numeric values."""
        assert ExitCode.SUCCESS == 0
        assert ExitCode.GENERAL_ERROR == 1
        assert ExitCode.MISSING_DEPENDENCIES == 2
        assert ExitCode.PERMISSION_DENIED == 3
        assert ExitCode.INVALID_ARGUMENTS == 4

    def test_exit_code_is_int(self):
        """Test exit codes are integers."""
        assert isinstance(ExitCode.SUCCESS, int)
        assert isinstance(ExitCode.GENERAL_ERROR, int)
        assert isinstance(ExitCode.MISSING_DEPENDENCIES, int)

    def test_exit_code_comparison(self):
        """Test exit codes can be compared."""
        assert ExitCode.SUCCESS < ExitCode.GENERAL_ERROR
        assert ExitCode.GENERAL_ERROR < ExitCode.MISSING_DEPENDENCIES
        assert ExitCode.INVALID_ARGUMENTS > ExitCode.SUCCESS

    def test_exit_code_in_range(self):
        """Test exit codes are in valid range (0-255)."""
        for code in ExitCode:
            assert 0 <= code <= 255


class TestCorporateSuffixes:
    """Tests for CORPORATE_SUFFIXES configuration."""

    def test_corporate_suffixes_is_list(self):
        """Test CORPORATE_SUFFIXES is a list."""
        assert isinstance(CORPORATE_SUFFIXES, list)

    def test_corporate_suffixes_not_empty(self):
        """Test CORPORATE_SUFFIXES is not empty."""
        assert len(CORPORATE_SUFFIXES) > 0

    def test_corporate_suffixes_are_lowercase(self):
        """Test all suffixes are lowercase (for case-insensitive matching)."""
        for suffix in CORPORATE_SUFFIXES:
            assert suffix == suffix.lower(), f"{suffix} is not lowercase"

    def test_corporate_suffixes_are_strings(self):
        """Test all suffixes are strings."""
        for suffix in CORPORATE_SUFFIXES:
            assert isinstance(suffix, str)

    def test_common_suffixes_present(self):
        """Test common corporate suffixes are present."""
        assert "corp" in CORPORATE_SUFFIXES
        assert "inc" in CORPORATE_SUFFIXES
        assert "ltd" in CORPORATE_SUFFIXES
        assert "llc" in CORPORATE_SUFFIXES
        assert "corporation" in CORPORATE_SUFFIXES


class TestDeviceTechnicalTerms:
    """Tests for DEVICE_TECHNICAL_TERMS configuration."""

    def test_device_terms_is_list(self):
        """Test DEVICE_TECHNICAL_TERMS is a list."""
        assert isinstance(DEVICE_TECHNICAL_TERMS, list)

    def test_device_terms_not_empty(self):
        """Test DEVICE_TECHNICAL_TERMS is not empty."""
        assert len(DEVICE_TECHNICAL_TERMS) > 0

    def test_device_terms_are_lowercase(self):
        """Test all terms are lowercase (for case-insensitive matching)."""
        for term in DEVICE_TECHNICAL_TERMS:
            assert term == term.lower(), f"{term} is not lowercase"

    def test_device_terms_are_strings(self):
        """Test all terms are strings."""
        for term in DEVICE_TECHNICAL_TERMS:
            assert isinstance(term, str)

    def test_common_terms_present(self):
        """Test common device terms are present."""
        assert "controller" in DEVICE_TECHNICAL_TERMS
        assert "adapter" in DEVICE_TECHNICAL_TERMS
        assert "ethernet" in DEVICE_TECHNICAL_TERMS
        assert "wireless" in DEVICE_TECHNICAL_TERMS
        assert "802.11ac" in DEVICE_TECHNICAL_TERMS


class TestTableConfiguration:
    """Tests for table configuration."""

    def test_table_columns_is_list(self):
        """Test TABLE_COLUMNS is a list."""
        assert isinstance(TABLE_COLUMNS, list)

    def test_table_columns_not_empty(self):
        """Test TABLE_COLUMNS has entries."""
        assert len(TABLE_COLUMNS) > 0

    def test_table_columns_structure(self):
        """Test each column is a tuple of (name, width)."""
        for column in TABLE_COLUMNS:
            assert isinstance(column, tuple)
            assert len(column) == 2
            name, width = column
            assert isinstance(name, str)
            assert isinstance(width, int)
            assert width > 0

    def test_expected_columns_present(self):
        """Test expected columns are defined."""
        column_names = [col[0] for col in TABLE_COLUMNS]
        assert "INTERFACE" in column_names
        assert "TYPE" in column_names
        assert "DEVICE" in column_names
        assert "INTERNAL_IPv4" in column_names
        assert "EXTERNAL_IPv4" in column_names
        assert "DNS_SERVER" in column_names
        assert "GATEWAY" in column_names

    def test_column_separator_is_string(self):
        """Test COLUMN_SEPARATOR is a string."""
        assert isinstance(COLUMN_SEPARATOR, str)

    def test_column_separator_length(self):
        """Test COLUMN_SEPARATOR has reasonable length."""
        assert len(COLUMN_SEPARATOR) > 0
        assert len(COLUMN_SEPARATOR) < 10


class TestToolMetadata:
    """Tests for tool metadata."""

    def test_tool_name_is_string(self):
        """Test TOOL_NAME is a string."""
        assert isinstance(TOOL_NAME, str)

    def test_tool_name_not_empty(self):
        """Test TOOL_NAME is not empty."""
        assert len(TOOL_NAME) > 0

    def test_tool_name_lowercase(self):
        """Test TOOL_NAME is lowercase."""
        assert TOOL_NAME == TOOL_NAME.lower()

    def test_version_is_string(self):
        """Test VERSION is a string."""
        assert isinstance(VERSION, str)

    def test_version_format(self):
        """Test VERSION follows semantic versioning format."""
        parts = VERSION.split(".")
        assert len(parts) == 3
        for part in parts:
            assert part.isdigit()

    def test_version_not_empty(self):
        """Test VERSION is not empty."""
        assert len(VERSION) > 0


class TestConfigurationIntegrity:
    """Tests for overall configuration integrity."""

    def test_no_duplicate_corporate_suffixes(self):
        """Test no duplicate corporate suffixes."""
        assert len(CORPORATE_SUFFIXES) == len(set(CORPORATE_SUFFIXES))

    def test_no_duplicate_device_terms(self):
        """Test no duplicate device terms."""
        assert len(DEVICE_TECHNICAL_TERMS) == len(set(DEVICE_TECHNICAL_TERMS))

    def test_no_duplicate_column_names(self):
        """Test no duplicate column names."""
        column_names = [col[0] for col in TABLE_COLUMNS]
        assert len(column_names) == len(set(column_names))

    def test_no_whitespace_in_corporate_suffixes(self):
        """Test corporate suffixes don't have leading/trailing whitespace."""
        for suffix in CORPORATE_SUFFIXES:
            assert suffix == suffix.strip()

    def test_no_whitespace_in_device_terms(self):
        """Test device terms don't have leading/trailing whitespace."""
        for term in DEVICE_TECHNICAL_TERMS:
            assert term == term.strip()

    def test_column_widths_reasonable(self):
        """Test column widths are in reasonable range."""
        for name, width in TABLE_COLUMNS:
            assert 5 <= width <= 50, f"{name} width {width} out of range"
