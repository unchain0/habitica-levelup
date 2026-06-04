"""Retry helpers for external calls."""

import asyncio
from collections.abc import Callable, Coroutine
from typing import TypeVar

from habiticalib.exceptions import NotAuthorizedError, TooManyRequestsError
from loguru import logger

from src.integrations.retry_policy import RetryConfig

T = TypeVar("T")


def _get_retry_delay(error: TooManyRequestsError, attempt: int) -> float:
    retry_after = getattr(error, "retry_after", None)
    if retry_after is not None:
        return float(retry_after)

    return min(
        RetryConfig.BASE_DELAY * (RetryConfig.EXPONENTIAL_BASE**attempt),
        RetryConfig.MAX_DELAY,
    )


async def _handle_rate_limit(
    error: TooManyRequestsError,
    attempt: int,
    max_retries: int,
) -> None:
    delay = _get_retry_delay(error, attempt)
    logger.warning(
        f"Rate limited (attempt {attempt + 1}/{max_retries}), retrying in {delay:.1f}s..."
    )
    await asyncio.sleep(delay)


def _should_retry(attempt: int, max_retries: int) -> bool:
    return attempt < max_retries - 1


async def _execute_with_retry(
    coro_factory: Callable[[], Coroutine[None, None, T]],
    attempt: int,
    max_retries: int,
) -> tuple[T | None, Exception | None]:
    try:
        return await coro_factory(), None
    except TooManyRequestsError as error:
        if _should_retry(attempt, max_retries):
            await _handle_rate_limit(error, attempt, max_retries)
        return None, error
    except NotAuthorizedError:
        logger.error("Authorization failed - check API credentials")
        raise


async def with_retry(
    coro_factory: Callable[[], Coroutine[None, None, T]],
    max_retries: int = RetryConfig.MAX_RETRIES,
    base_delay: float = RetryConfig.BASE_DELAY,
    max_delay: float = RetryConfig.MAX_DELAY,
) -> T:
    last_exception: Exception | None = None

    for attempt in range(max_retries):
        result, error = await _execute_with_retry(coro_factory, attempt, max_retries)
        if error is None:
            return result  # type: ignore[return-value]
        last_exception = error

    if last_exception:
        raise last_exception

    raise RuntimeError("Unexpected end of retry loop")
