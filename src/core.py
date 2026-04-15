"""Habitica Level Up Bot - Core Utilities.

Circuit breaker pattern and retry logic for fault tolerance.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from loguru import logger


@dataclass
class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance.

    Prevents hammering the API when it's experiencing issues.
    Opens after max_failures consecutive failures, then waits
    reset_timeout before allowing retries.
    """

    max_failures: int = 5
    reset_timeout: timedelta = field(default_factory=lambda: timedelta(minutes=1))
    failure_count: int = field(default=0, init=False)
    last_failure: datetime | None = field(default=None, init=False)

    def record_success(self) -> None:
        """Reset failure count on success."""
        self.failure_count = 0
        self.last_failure = None

    def record_failure(self) -> None:
        """Increment failure count and timestamp."""
        self.failure_count += 1
        self.last_failure = datetime.now()
        logger.warning(f"Circuit breaker: {self.failure_count}/{self.max_failures} failures")

    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        if self.failure_count < self.max_failures:
            return False

        if self.last_failure is None:
            return False

        elapsed = datetime.now() - self.last_failure
        if elapsed < self.reset_timeout:
            return True

        self.failure_count = 0
        self.last_failure = None
        return False


class RetryConfig:
    """Configuration for retry behavior."""

    MAX_RETRIES = 3
    BASE_DELAY = 1.0
    MAX_DELAY = 60.0
    EXPONENTIAL_BASE = 2.0
