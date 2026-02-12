"""Metric sorting utilities.

Provides common metric sorting logic used across modules.
"""


def get_metric_sort_key(metric: str) -> tuple[int, int]:
    """Get sort key for route metric values.

    Sorts metrics deterministically:
        - Numeric metrics: category 0, sorted by value (ascending)
        - DEFAULT: category 1 (never assume numeric value)
        - NONE or other: category 2

    Args:
        metric: Metric value (number string, "DEFAULT", or "NONE")

    Returns:
        Tuple of (category, value) for sorting.
    """
    if metric.isdigit():
        return (0, int(metric))  # Numeric: category 0, sorted ascending
    if metric == "DEFAULT":
        return (1, 0)  # DEFAULT: category 1 (never assume numeric value)
    return (2, 0)  # NONE or other: category 2
