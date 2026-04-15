import asyncio
from collections.abc import Callable, Coroutine
from typing import TypeVar

from aiohttp import ClientSession, ClientTimeout, TCPConnector
from habiticalib.exceptions import NotAuthorizedError, TooManyRequestsError
from loguru import logger

from src.core import RetryConfig

T = TypeVar("T")


class OptimizedClientSession:
    def __init__(
        self,
        max_connections: int = 100,
        max_per_host: int = 30,
        timeout_total: float = 30.0,
    ):
        self.max_connections = max_connections
        self.max_per_host = max_per_host
        self.timeout_total = timeout_total
        self._session: ClientSession | None = None

    async def __aenter__(self) -> ClientSession:
        connector = TCPConnector(
            limit=self.max_connections,
            limit_per_host=self.max_per_host,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
        )

        timeout = ClientTimeout(
            total=self.timeout_total,
            connect=10,
            sock_read=20,
        )

        self._session = ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "User-Agent": "habitica-levelup/1.0.0",
                "Content-Type": "application/json",
            },
        )
        return self._session

    async def __aexit__(self, *_) -> None:
        if self._session:
            await self._session.close()


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
        except TooManyRequestsError as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = min(
                    base_delay * (RetryConfig.EXPONENTIAL_BASE**attempt),
                    max_delay,
                )
                logger.warning(
                    f"Rate limited (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
        except NotAuthorizedError as e:
            error_msg = str(e).lower()
            if "stat points" in error_msg:
                # Not enough stat points - not a credential error, just skip allocation
                logger.debug("No stat points available to allocate")
                raise
            logger.error("Authorization failed - check API credentials")
            raise

    if last_exception:
        raise last_exception

    raise RuntimeError("Unexpected end of retry loop")
