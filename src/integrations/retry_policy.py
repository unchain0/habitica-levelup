"""Retry policy constants for integration calls."""


class RetryConfig:
    """Configuration for retry behavior."""

    MAX_RETRIES = 3
    BASE_DELAY = 1.0
    MAX_DELAY = 60.0
    EXPONENTIAL_BASE = 2.0
