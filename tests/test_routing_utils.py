"""Tests for network/routing_utils.py.

Tests metric sorting for route priority determination.
"""

import pytest

from network.routing_utils import get_metric_sort_key


class TestGetMetricSortKey:
    """Tests for get_metric_sort_key function."""

    def test_numeric_metrics(self):
        """Test numeric metrics return category 0 with value."""
        assert get_metric_sort_key("0") == (0, 0)
        assert get_metric_sort_key("50") == (0, 50)
        assert get_metric_sort_key("100") == (0, 100)
        assert get_metric_sort_key("999") == (0, 999)

    def test_default_metric(self):
        """Test DEFAULT returns category 1."""
        assert get_metric_sort_key("DEFAULT") == (1, 0)

    def test_none_metric(self):
        """Test NONE returns category 2."""
        assert get_metric_sort_key("NONE") == (2, 0)

    def test_unknown_metric(self):
        """Test unknown values return category 2."""
        assert get_metric_sort_key("unknown") == (2, 0)
        assert get_metric_sort_key("invalid") == (2, 0)
        assert get_metric_sort_key("") == (2, 0)

    def test_sorting_order(self):
        """Test actual sorting behavior."""
        metrics = ["DEFAULT", "100", "50", "NONE", "200"]
        sorted_metrics = sorted(metrics, key=get_metric_sort_key)
        assert sorted_metrics == ["50", "100", "200", "DEFAULT", "NONE"]

    def test_sorting_with_multiple_defaults(self):
        """Test sorting with multiple routes."""
        metrics = ["DEFAULT", "98", "100", "NONE", "DEFAULT"]
        sorted_metrics = sorted(metrics, key=get_metric_sort_key)
        # Numeric first (ascending), then DEFAULT, then NONE
        assert sorted_metrics[0] == "98"
        assert sorted_metrics[1] == "100"
        assert sorted_metrics[2:4] == ["DEFAULT", "DEFAULT"]
        assert sorted_metrics[4] == "NONE"

    def test_edge_case_zero_metric(self):
        """Test zero metric is valid and sorts first."""
        metrics = ["50", "0", "100"]
        sorted_metrics = sorted(metrics, key=get_metric_sort_key)
        assert sorted_metrics == ["0", "50", "100"]

    def test_large_numeric_values(self):
        """Test large numeric values are handled correctly."""
        assert get_metric_sort_key("10000") == (0, 10000)
        assert get_metric_sort_key("999999") == (0, 999999)
