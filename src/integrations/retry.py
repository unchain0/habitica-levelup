"""Retry helpers for external calls."""

import asyncio
from collections.abc import Callable, Coroutine
from typing import TypeVar

from habiticalib.exceptions import NotAuthorizedError, TooManyRequestsError
from loguru import logger

from src.domain_models.resilience import RetryConfig

T = TypeVar("T")


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
                delay = min(base_delay * (RetryConfig.EXPONENTIAL_BASE**attempt), max_delay)
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
