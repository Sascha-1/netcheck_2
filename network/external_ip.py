"""External IP and ISP information.

Queries ipinfo.io API for public IP addresses and ISP information.
"""

import json
import time
from typing import Any

import requests

import config
from logging_config import get_logger
from models import EgressInfo

logger = get_logger(__name__)


def get_egress_info() -> EgressInfo:
    """Query external IP and ISP information.

    IPv4: 3 attempts, exponential backoff
    IPv6: 1 attempt (fail-fast, optional data)
    Timeout: 10 seconds

    Returns:
        EgressInfo object (or error object on failure)
    """
    # Query IPv4 (with retries)
    logger.debug("Querying IPv4 egress...")
    ipv4_response = get_with_retry(config.IPINFO_URL, config.TIMEOUT_SECONDS)

    if not ipv4_response:
        logger.error("IPv4 egress query failed after %d attempts", config.RETRY_ATTEMPTS)
        return EgressInfo.create_error()

    try:
        data = ipv4_response.json()
    except json.JSONDecodeError:
        logger.error("Invalid JSON from ipinfo.io")
        return EgressInfo.create_error()

    # Validate response
    if not validate_api_response(data, "IPv4"):
        return EgressInfo.create_error()

    # Extract IPv4 data
    external_ip = data["ip"]
    isp = data["org"]  # Raw format (with AS number)
    country = data["country"]

    # Query IPv6 (single attempt, optional)
    logger.debug("Querying IPv6 egress...")
    ipv6_response = get_ipv6_single_attempt(config.IPINFO_IPv6_URL, config.TIMEOUT_SECONDS)

    if ipv6_response:
        try:
            ipv6_data = ipv6_response.json()
            external_ipv6 = ipv6_data.get("ip", "N/A")
        except json.JSONDecodeError:
            external_ipv6 = "N/A"
    else:
        external_ipv6 = "N/A"

    return EgressInfo(
        external_ip=external_ip,
        external_ipv6=external_ipv6,
        isp=isp,
        country=country,
    )


def get_with_retry(url: str, timeout: int) -> requests.Response | None:
    """Request with exponential backoff retry.

    Args:
        url: URL to request
        timeout: Request timeout in seconds

    Returns:
        Response object or None if all attempts fail.
    """
    for attempt in range(config.RETRY_ATTEMPTS):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            if attempt < config.RETRY_ATTEMPTS - 1:
                sleep_time = config.RETRY_BACKOFF_FACTOR * (2**attempt)
                logger.debug("Request attempt %d failed, retrying in %ds", attempt + 1, sleep_time)
                time.sleep(sleep_time)
            else:
                logger.debug(
                    "Request failed after %d attempts: %s",
                    config.RETRY_ATTEMPTS,
                    str(e),
                )
    return None


def get_ipv6_single_attempt(url: str, timeout: int) -> requests.Response | None:
    """Single attempt IPv6 request (fail-fast).

    IPv6 is optional data, so we don't retry on failure.

    Args:
        url: URL to request
        timeout: Request timeout in seconds

    Returns:
        Response object or None if request fails.
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.RequestException:
        return None


def validate_api_response(data: dict[str, Any], _ip_version: str) -> bool:
    """Validate ipinfo.io response.

    Args:
        data: JSON response data
        _ip_version: "IPv4" or "IPv6" (unused, kept for future logging)

    Returns:
        True if response contains all required fields, False otherwise.
    """
    required = ["ip", "org", "country"]
    for field in required:
        if field not in data or not data[field]:
            logger.error("API response missing required field: %s", field)
            return False
    return True
