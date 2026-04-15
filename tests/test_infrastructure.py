from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import ClientSession
from habiticalib.exceptions import NotAuthorizedError, TooManyRequestsError
from habiticalib.typedefs import HabiticaErrorResponse
from multidict import CIMultiDict

from src.infrastructure import OptimizedClientSession, with_retry


class TestOptimizedClientSession:
    @pytest.mark.asyncio
    async def test_aenter_creates_session(self):
        async with OptimizedClientSession() as session:
            assert isinstance(session, ClientSession)

    @pytest.mark.asyncio
    async def test_aexit_closes_session(self):
        session_manager = OptimizedClientSession()
        async with session_manager:
            pass

    @pytest.mark.asyncio
    async def test_custom_connection_limits(self):
        async with OptimizedClientSession(max_connections=50, max_per_host=10) as session:
            assert session._connector is not None

    @pytest.mark.asyncio
    async def test_custom_timeout(self):
        async with OptimizedClientSession(timeout_total=60.0) as session:
            assert session._timeout.total == 60.0

    @pytest.mark.asyncio
    async def test_session_headers(self):
        async with OptimizedClientSession() as session:
            headers = session._default_headers
            assert headers["User-Agent"] == "habitica-levelup/1.0.0"
            assert headers["Content-Type"] == "application/json"


class TestWithRetry:
    @pytest.mark.asyncio
    async def test_successful_call_no_retry(self):
        async def success_coro():
            return "success"

        result = await with_retry(success_coro)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_on_too_many_requests(self):
        error_response = HabiticaErrorResponse(
            success=False, error="Rate limited", message="Too many requests"
        )
        error = TooManyRequestsError(error=error_response, headers=CIMultiDict())
        call_count = 0

        async def failing_coro():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise error
            return "success"

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await with_retry(failing_coro, max_retries=3)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_not_authorized(self):
        error_response = HabiticaErrorResponse(
            success=False, error="Unauthorized", message="Not authorized"
        )
        error = NotAuthorizedError(error=error_response, headers=CIMultiDict())

        async def failing_coro():
            raise error

        with pytest.raises(NotAuthorizedError):
            await with_retry(failing_coro)

    @pytest.mark.asyncio
    async def test_no_retry_on_not_authorized_stat_points(self):
        error_response = HabiticaErrorResponse(
            success=False,
            error="Unauthorized",
            message="Not enough stat points to allocate",
        )
        error = NotAuthorizedError(error=error_response, headers=CIMultiDict())

        async def failing_coro():
            raise error

        with pytest.raises(NotAuthorizedError):
            await with_retry(failing_coro)

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        error_response = HabiticaErrorResponse(
            success=False, error="Rate limited", message="Too many requests"
        )
        error = TooManyRequestsError(error=error_response, headers=CIMultiDict())
        call_count = 0

        async def failing_coro():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise error
            return "success"

        sleep_calls = []

        async def mock_sleep(delay):
            sleep_calls.append(delay)

        with patch("asyncio.sleep", mock_sleep):
            await with_retry(failing_coro, max_retries=3, base_delay=1.0)
        assert sleep_calls == [1.0, 2.0]

    @pytest.mark.asyncio
    async def test_max_delay_cap(self):
        error_response = HabiticaErrorResponse(
            success=False, error="Rate limited", message="Too many requests"
        )
        error = TooManyRequestsError(error=error_response, headers=CIMultiDict())
        call_count = 0

        async def failing_coro():
            nonlocal call_count
            call_count += 1
            if call_count < 4:
                raise error
            return "success"

        sleep_calls = []

        async def mock_sleep(delay):
            sleep_calls.append(delay)

        with patch("asyncio.sleep", mock_sleep):
            await with_retry(failing_coro, max_retries=4, base_delay=10.0, max_delay=15.0)
        assert all(d <= 15.0 for d in sleep_calls)

    @pytest.mark.asyncio
    async def test_all_retries_exhausted(self):
        error_response = HabiticaErrorResponse(
            success=False, error="Rate limited", message="Too many requests"
        )
        error = TooManyRequestsError(error=error_response, headers=CIMultiDict())

        async def failing_coro():
            raise error

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(TooManyRequestsError):
                await with_retry(failing_coro, max_retries=2)


class TestOptimizedClientSessionEdgeCases:
    @pytest.mark.asyncio
    async def test_aexit_with_none_session(self):
        session_manager = OptimizedClientSession()
        session_manager._session = None

        await session_manager.__aexit__(None, None, None)


class TestWithRetryEdgeCases:
    @pytest.mark.asyncio
    async def test_success_on_first_try(self):
        async def success_coro():
            return "immediate"

        result = await with_retry(success_coro, max_retries=1)
        assert result == "immediate"

    @pytest.mark.asyncio
    async def test_with_retry_reaches_end(self):

        error_response = HabiticaErrorResponse(
            success=False, error="Rate limited", message="Too many requests"
        )
        error = TooManyRequestsError(error=error_response, headers=CIMultiDict())

        async def always_fails():
            raise error

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(TooManyRequestsError):
                await with_retry(always_fails, max_retries=1)

    @pytest.mark.asyncio
    async def test_with_retry_zero_retries_raises_runtime_error(self):
        async def never_called():
            return "should not reach"

        with pytest.raises(RuntimeError, match="Unexpected end of retry loop"):
            await with_retry(never_called, max_retries=0)
