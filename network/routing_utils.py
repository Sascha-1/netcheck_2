"""Routing utilities for metric sorting and route analysis.

Provides common routing logic used across network modules for deterministic
route selection based on metric values.

DESIGN DECISION: Why DEFAULT is category 1 (after numeric, before NONE)

When a metric is not explicitly shown in the routing table, we return "DEFAULT"
rather than querying the effective value via 'ip route get <destination>'.

This is intentional and follows netcheck's core design principles:

1. HONESTY: "DEFAULT" accurately means "kernel's default, we don't know the value"
   - We never guess or assume values
   - The user sees exactly what we know vs. don't know

2. DETERMINISTIC BEHAVIOR: Querying effective metric is ambiguous
   - Which destination to query? (8.8.8.8, 1.1.1.1, gateway?)
   - Results may vary by destination
   - Creates non-deterministic behavior

3. SORTABLE: DEFAULT sorts correctly for routing decisions
   - Category 0: Explicit metrics (0-999) - highest priority
   - Category 1: DEFAULT - kernel decides priority
   - Category 2: NONE - no route exists
   - This matches actual routing behavior

4. USER CLARITY: Explicit vs implicit is clear
   - Metric "100" → User explicitly set this
   - Metric "DEFAULT" → Kernel using default (investigate if needed)
   - Clear distinction aids troubleshooting

If you need the effective metric for a specific destination:
    $ ip route get 8.8.8.8 | grep -o 'metric [0-9]*'

For netcheck's purpose (showing interface configuration), "DEFAULT" is
more honest than a potentially misleading queried value.
"""


def get_metric_sort_key(metric: str) -> tuple[int, int]:
    """Get sort key for route metric values.

    Sorts metrics deterministically for route priority ordering:
        - Numeric metrics: category 0, sorted by value (ascending)
        - DEFAULT: category 1 (kernel's default, never assume numeric value)
        - NONE or other: category 2 (no route exists)

    This sorting mirrors actual kernel routing behavior where explicit
    metrics take priority, followed by default routes, followed by
    interfaces with no default route.

    Args:
        metric: Metric value (number string, "DEFAULT", or "NONE")

    Returns:
        Tuple of (category, value) for sorting.
            category 0: Numeric metrics (sorted ascending by value)
            category 1: DEFAULT (one entry, kernel decides)
            category 2: NONE or unknown (lowest priority)

    Examples:
        >>> get_metric_sort_key("50")
        (0, 50)
        >>> get_metric_sort_key("DEFAULT")
        (1, 0)
        >>> get_metric_sort_key("NONE")
        (2, 0)

        # Sorting behavior
        >>> metrics = ["DEFAULT", "100", "50", "NONE"]
        >>> sorted(metrics, key=get_metric_sort_key)
        ['50', '100', 'DEFAULT', 'NONE']
    """
    if metric.isdigit():
        return (0, int(metric))  # Numeric: category 0, sorted ascending
    if metric == "DEFAULT":
        return (1, 0)  # DEFAULT: category 1 (never assume numeric value)
    return (2, 0)  # NONE or other: category 2
