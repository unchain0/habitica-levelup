"""Retry helpers for external calls."""

import asyncio
from collections.abc import Callable, Coroutine
from typing import TypeVar

from habiticalib.exceptions import NotAuthorizedError, TooManyRequestsError
from loguru import logger

from src.integrations.retry_policy import RetryConfig

T = TypeVar("T")


def _get_retry_delay(error: TooManyRequestsError, attempt: int) -> float:
    """Extract retry delay from Retry-After header or use exponential backoff."""
    retry_after = getattr(error, "retry_after", None)
    if retry_after is not None:
        return float(retry_after)

    return min(
        RetryConfig.BASE_DELAY * (RetryConfig.EXPONENTIAL_BASE**attempt),
        RetryConfig.MAX_DELAY,
    )


async def with_retry(
    coro_factory: Callable[[], Coroutine[None, None, T]],
    max_retries: int = RetryConfig.MAX_RETRIES,
    base_delay: float = RetryConfig.BASE_DELAY,
    max_delay: float = RetryConfig.MAX_DELAY,
) -> T:
    last_exception: Exception | None = None

    for attempt in range(max_retries):
        try:
            return await coro_factory()
        except TooManyRequestsError as error:
            last_exception = error
            if attempt < max_retries - 1:
                delay = _get_retry_delay(error, attempt)
                logger.warning(
                    f"Rate limited (attempt {attempt + 1}/{max_retries}), retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
        except NotAuthorizedError:
            logger.error("Authorization failed - check API credentials")
            raise

    if last_exception:
        raise last_exception

    raise RuntimeError("Unexpected end of retry loop")
