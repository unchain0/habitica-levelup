from datetime import datetime, timedelta
from unittest.mock import patch

from src.domain_models.resilience import CircuitBreaker, RetryConfig


class TestCircuitBreaker:
    def test_initial_state(self):
        cb = CircuitBreaker()

        assert cb.is_open() is False
        assert cb.failure_count == 0
        assert cb.last_failure is None

    def test_record_success(self):
        cb = CircuitBreaker()
        cb.failure_count = 3
        cb.last_failure = datetime.now()

        cb.record_success()

        assert cb.failure_count == 0
        assert cb.last_failure is None

    def test_record_failure_increments_count(self):
        cb = CircuitBreaker()

        cb.record_failure()

        assert cb.failure_count == 1
        assert cb.last_failure is not None

    def test_is_open_under_threshold(self):
        cb = CircuitBreaker(max_failures=5)

        for _ in range(4):
            cb.record_failure()

        assert cb.is_open() is False

    def test_is_open_at_threshold(self):
        cb = CircuitBreaker(max_failures=5)

        for _ in range(5):
            cb.record_failure()

        assert cb.is_open() is True

    def test_is_open_resets_after_timeout(self):
        cb = CircuitBreaker(max_failures=5, reset_timeout=timedelta(seconds=1))

        for _ in range(5):
            cb.record_failure()

        assert cb.is_open() is True

        with patch("src.domain_models.resilience.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime.now() + timedelta(seconds=2)

            assert cb.is_open() is False
            assert cb.failure_count == 0

    def test_custom_max_failures(self):
        cb = CircuitBreaker(max_failures=3)

        for _ in range(3):
            cb.record_failure()

        assert cb.is_open() is True

    def test_custom_reset_timeout(self):
        cb = CircuitBreaker(max_failures=5, reset_timeout=timedelta(minutes=5))

        for _ in range(5):
            cb.record_failure()

        assert cb.is_open() is True


class TestRetryConfig:
    def test_default_values(self):
        assert RetryConfig.MAX_RETRIES == 3
        assert RetryConfig.BASE_DELAY == 1.0
        assert RetryConfig.MAX_DELAY == 60.0
        assert RetryConfig.EXPONENTIAL_BASE == 2.0

    def test_is_open_with_no_last_failure(self):
        cb = CircuitBreaker(max_failures=5)
        cb.failure_count = 5
        cb.last_failure = None

        assert cb.is_open() is False
