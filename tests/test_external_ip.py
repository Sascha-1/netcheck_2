"""Tests for network/external_ip.py.

Tests external IP queries with mocked HTTP requests.
FIXED: Added MagicMock type annotations to all mock parameters
"""

import json
from unittest.mock import Mock, patch, MagicMock

import pytest
import requests

from network.external_ip import (
    get_egress_info,
    get_ipv6_single_attempt,
    get_with_retry,
    validate_api_response,
)


class TestValidateApiResponse:
    """Tests for validate_api_response function."""

    def test_valid_response(self) -> None:
        """Test valid response passes validation."""
        data = {
            "ip": "203.0.113.1",
            "org": "AS12345 Example ISP",
            "country": "US",
        }
        assert validate_api_response(data, "IPv4") is True

    def test_missing_ip(self) -> None:
        """Test missing IP field fails validation."""
        data = {
            "org": "AS12345 Example ISP",
            "country": "US",
        }
        assert validate_api_response(data, "IPv4") is False

    def test_missing_org(self) -> None:
        """Test missing org field fails validation."""
        data = {
            "ip": "203.0.113.1",
            "country": "US",
        }
        assert validate_api_response(data, "IPv4") is False

    def test_missing_country(self) -> None:
        """Test missing country field fails validation."""
        data = {
            "ip": "203.0.113.1",
            "org": "AS12345 Example ISP",
        }
        assert validate_api_response(data, "IPv4") is False

    def test_empty_values(self) -> None:
        """Test empty values fail validation."""
        data = {
            "ip": "",
            "org": "AS12345 Example ISP",
            "country": "US",
        }
        assert validate_api_response(data, "IPv4") is False


class TestGetWithRetry:
    """Tests for get_with_retry function."""

    @patch("requests.get")
    def test_successful_first_attempt(self, mock_get: MagicMock) -> None:
        """Test successful request on first attempt."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_with_retry("http://example.com", 10)

        assert result == mock_response
        assert mock_get.call_count == 1

    @patch("time.sleep")
    @patch("requests.get")
    def test_retry_on_failure(self, mock_get: MagicMock, mock_sleep: MagicMock) -> None:
        """Test retry on failure."""
        # Fail twice, succeed on third
        mock_get.side_effect = [
            requests.RequestException("error"),
            requests.RequestException("error"),
            Mock(status_code=200),
        ]

        result = get_with_retry("http://example.com", 10)

        assert result is not None
        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2  # Sleep between attempts

    @patch("time.sleep")
    @patch("requests.get")
    def test_all_attempts_fail(self, mock_get: MagicMock, mock_sleep: MagicMock) -> None:
        """Test returns None when all attempts fail."""
        mock_get.side_effect = requests.RequestException("error")

        result = get_with_retry("http://example.com", 10)

        assert result is None
        assert mock_get.call_count == 3  # Default retry count

    @patch("requests.get")
    def test_http_error_raises(self, mock_get: MagicMock) -> None:
        """Test HTTP errors trigger retry."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError()
        mock_get.return_value = mock_response

        result = get_with_retry("http://example.com", 10)

        assert result is None


class TestGetIpv6SingleAttempt:
    """Tests for get_ipv6_single_attempt function."""

    @patch("requests.get")
    def test_successful_request(self, mock_get: MagicMock) -> None:
        """Test successful IPv6 request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = get_ipv6_single_attempt("http://example.com", 10)

        assert result == mock_response
        assert mock_get.call_count == 1

    @patch("requests.get")
    def test_single_attempt_only(self, mock_get: MagicMock) -> None:
        """Test only one attempt is made on failure."""
        mock_get.side_effect = requests.RequestException("error")

        result = get_ipv6_single_attempt("http://example.com", 10)

        assert result is None
        assert mock_get.call_count == 1  # Only one attempt


class TestGetEgressInfo:
    """Tests for get_egress_info function."""

    @patch("network.external_ip.get_ipv6_single_attempt")
    @patch("network.external_ip.get_with_retry")
    def test_successful_ipv4_and_ipv6(self, mock_ipv4: MagicMock, mock_ipv6: MagicMock) -> None:
        """Test successful query with both IPv4 and IPv6."""
        # Setup IPv4 response
        ipv4_response = Mock()
        ipv4_response.json.return_value = {
            "ip": "203.0.113.1",
            "org": "AS12345 Example ISP",
            "country": "US",
        }
        mock_ipv4.return_value = ipv4_response

        # Setup IPv6 response
        ipv6_response = Mock()
        ipv6_response.json.return_value = {
            "ip": "2001:db8::1",
        }
        mock_ipv6.return_value = ipv6_response

        result = get_egress_info()

        assert result.external_ip == "203.0.113.1"
        assert result.external_ipv6 == "2001:db8::1"
        assert result.isp == "AS12345 Example ISP"
        assert result.country == "US"

    @patch("network.external_ip.get_ipv6_single_attempt")
    @patch("network.external_ip.get_with_retry")
    def test_ipv4_only(self, mock_ipv4: MagicMock, mock_ipv6: MagicMock) -> None:
        """Test successful IPv4 but no IPv6."""
        ipv4_response = Mock()
        ipv4_response.json.return_value = {
            "ip": "203.0.113.1",
            "org": "AS12345 Example ISP",
            "country": "US",
        }
        mock_ipv4.return_value = ipv4_response
        mock_ipv6.return_value = None

        result = get_egress_info()

        assert result.external_ip == "203.0.113.1"
        assert result.external_ipv6 == "N/A"
        assert result.isp == "AS12345 Example ISP"

    @patch("network.external_ip.get_with_retry")
    def test_ipv4_failure(self, mock_ipv4: MagicMock) -> None:
        """Test IPv4 query failure returns error object."""
        mock_ipv4.return_value = None

        result = get_egress_info()

        assert result.external_ip == "QUERY FAILED"
        assert result.external_ipv6 == "QUERY FAILED"
        assert result.isp == "QUERY FAILED"
        assert result.country == "QUERY FAILED"

    @patch("network.external_ip.get_with_retry")
    def test_invalid_json(self, mock_ipv4: MagicMock) -> None:
        """Test invalid JSON returns error object."""
        ipv4_response = Mock()
        ipv4_response.json.side_effect = json.JSONDecodeError("error", "", 0)
        mock_ipv4.return_value = ipv4_response

        result = get_egress_info()

        assert result.external_ip == "QUERY FAILED"

    @patch("network.external_ip.get_ipv6_single_attempt")
    @patch("network.external_ip.get_with_retry")
    def test_missing_required_fields(self, mock_ipv4: MagicMock, mock_ipv6: MagicMock) -> None:
        """Test missing required fields returns error object."""
        ipv4_response = Mock()
        ipv4_response.json.return_value = {
            "ip": "203.0.113.1",
            # Missing org and country
        }
        mock_ipv4.return_value = ipv4_response

        result = get_egress_info()

        assert result.external_ip == "QUERY FAILED"

    @patch("network.external_ip.get_ipv6_single_attempt")
    @patch("network.external_ip.get_with_retry")
    def test_ipv6_json_decode_error(self, mock_ipv4: MagicMock, mock_ipv6: MagicMock) -> None:
        """Test IPv6 JSON decode error falls back to N/A."""
        ipv4_response = Mock()
        ipv4_response.json.return_value = {
            "ip": "203.0.113.1",
            "org": "AS12345 Example ISP",
            "country": "US",
        }
        mock_ipv4.return_value = ipv4_response

        ipv6_response = Mock()
        ipv6_response.json.side_effect = json.JSONDecodeError("error", "", 0)
        mock_ipv6.return_value = ipv6_response

        result = get_egress_info()

        assert result.external_ip == "203.0.113.1"
        assert result.external_ipv6 == "N/A"
