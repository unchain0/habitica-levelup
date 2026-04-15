import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from habiticalib.exceptions import NotAuthorizedError, TooManyRequestsError
from habiticalib.typedefs import HabiticaErrorResponse
from multidict import CIMultiDict

from src.domain_models.user_status import UserStatus
from src.services.levelup_service import LevelUpService


class TestLevelUpService:
    @pytest.fixture
    def service(self):
        return LevelUpService()

    @pytest.mark.asyncio
    async def test_get_current_level_success(self, service):
        mock_gateway = MagicMock()
        mock_gateway.get_user_status = AsyncMock(
            return_value=UserStatus(level=42, available_points=0)
        )

        level = await service.get_current_level(mock_gateway)

        assert level == 42

    @pytest.mark.asyncio
    async def test_get_current_level_none_level(self, service):
        mock_gateway = MagicMock()
        mock_gateway.get_user_status = AsyncMock(
            return_value=UserStatus(level=None, available_points=0)
        )

        with pytest.raises(ValueError, match="Level is None"):
            await service.get_current_level(mock_gateway)

    @pytest.mark.asyncio
    async def test_farm_quest(self, service):
        mock_gateway = MagicMock()
        mock_gateway.score_task_up = AsyncMock(return_value=None)
        service._farm_task_id = "task-123"

        await service.farm_quest(mock_gateway)

        mock_gateway.score_task_up.assert_awaited_once_with("task-123")

    @pytest.mark.asyncio
    async def test_allocate_points(self, service):
        mock_gateway = MagicMock()
        mock_gateway.get_user_status = AsyncMock(
            return_value=UserStatus(level=1, available_points=5)
        )
        mock_gateway.allocate_strength_point = AsyncMock(return_value=None)

        await service.allocate_points(mock_gateway)

        mock_gateway.allocate_strength_point.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_allocate_points_no_points_available(self, service):
        mock_gateway = MagicMock()
        mock_gateway.get_user_status = AsyncMock(
            return_value=UserStatus(level=1, available_points=0)
        )

        await service.allocate_points(mock_gateway)

        mock_gateway.allocate_strength_point.assert_not_called()

    @pytest.mark.asyncio
    async def test_allocate_points_skips_when_stats_missing(self, service):
        mock_gateway = MagicMock()
        mock_gateway.get_user_status = AsyncMock(
            return_value=UserStatus(level=None, available_points=0)
        )

        await service.allocate_points(mock_gateway)

        mock_gateway.allocate_strength_point.assert_not_called()

    @pytest.mark.asyncio
    async def test_allocate_points_ignores_stat_point_error(self, service):
        mock_gateway = MagicMock()
        mock_gateway.get_user_status = AsyncMock(
            return_value=UserStatus(level=1, available_points=5)
        )
        error_response = HabiticaErrorResponse(
            success=False,
            error="Unauthorized",
            message="Not enough stat points to allocate",
        )
        mock_gateway.allocate_strength_point = AsyncMock(
            side_effect=NotAuthorizedError(error=error_response, headers=CIMultiDict())
        )

        await service.allocate_points(mock_gateway)

        mock_gateway.allocate_strength_point.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_allocate_points_reraises_other_auth_errors(self, service):
        mock_gateway = MagicMock()
        mock_gateway.get_user_status = AsyncMock(
            return_value=UserStatus(level=1, available_points=5)
        )
        error_response = HabiticaErrorResponse(
            success=False,
            error="Unauthorized",
            message="Credential mismatch",
        )
        mock_gateway.allocate_strength_point = AsyncMock(
            side_effect=NotAuthorizedError(error=error_response, headers=CIMultiDict())
        )

        with pytest.raises(NotAuthorizedError):
            await service.allocate_points(mock_gateway)

    @pytest.mark.asyncio
    async def test_initialize_sets_level_and_task_id(self, service):
        mock_gateway = MagicMock()
        mock_gateway.get_user_status = AsyncMock(
            return_value=UserStatus(level=7, available_points=0)
        )
        mock_gateway.get_or_create_farm_task = AsyncMock(return_value="task-xyz")

        await service.initialize(mock_gateway)

        assert service.current_level == 7
        assert service._farm_task_id == "task-xyz"

    @pytest.mark.asyncio
    async def test_run_iteration_success(self, service):
        mock_gateway = MagicMock()
        service.circuit_breaker.is_open = MagicMock(return_value=False)
        service.circuit_breaker.record_success = MagicMock()

        with patch.object(service, "farm_quest", new_callable=AsyncMock):
            with patch.object(service, "allocate_points", new_callable=AsyncMock):
                success = await service.run_iteration(mock_gateway)

        assert success is True
        service.circuit_breaker.record_success.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_iteration_circuit_open(self, service):
        mock_gateway = MagicMock()
        service.circuit_breaker.is_open = MagicMock(return_value=True)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            success = await service.run_iteration(mock_gateway)

        assert success is False

    @pytest.mark.asyncio
    async def test_run_iteration_timeout(self, service):
        mock_gateway = MagicMock()
        service.circuit_breaker.is_open = MagicMock(return_value=False)
        service.circuit_breaker.record_failure = MagicMock()

        with patch.object(service, "farm_quest", side_effect=TimeoutError()):
            success = await service.run_iteration(mock_gateway)

        assert success is False
        service.circuit_breaker.record_failure.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_iteration_rate_limited(self, service):
        mock_gateway = MagicMock()
        service.circuit_breaker.is_open = MagicMock(return_value=False)
        service.circuit_breaker.record_failure = MagicMock()

        error_response = HabiticaErrorResponse(
            success=False, error="Rate limited", message="Too many requests"
        )
        error = TooManyRequestsError(error=error_response, headers=CIMultiDict())
        with patch.object(service, "farm_quest", side_effect=error):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                success = await service.run_iteration(mock_gateway)

        assert success is False
        service.circuit_breaker.record_failure.assert_called_once()


class TestLevelUpServiceRun:
    @pytest.fixture
    def service(self):
        return LevelUpService()

    @pytest.mark.asyncio
    async def test_run_reaches_max_level(self, service):
        mock_gateway = MagicMock()
        service.MAX_LEVEL = 999
        service.shutdown_event.set()

        async def seed_initialize(_gateway):
            await self._seed_level(service, 998)

        with patch.object(service, "initialize", new_callable=AsyncMock) as mock_initialize:
            mock_initialize.side_effect = seed_initialize
            await service.run(mock_gateway)

    @pytest.mark.asyncio
    async def test_run_cancelled_error(self, service):
        mock_gateway = MagicMock()

        async def seed_initialize(_gateway):
            await self._seed_level(service, 1)

        with patch.object(service, "initialize", new_callable=AsyncMock) as mock_initialize:
            mock_initialize.side_effect = seed_initialize
            with patch.object(service, "run_iteration", side_effect=asyncio.CancelledError()):
                with pytest.raises(asyncio.CancelledError):
                    await service.run(mock_gateway)

    @pytest.mark.asyncio
    async def test_run_already_at_max_level(self, service):
        mock_gateway = MagicMock()

        async def seed_initialize(_gateway):
            await self._seed_level(service, 999)

        with patch.object(service, "initialize", new_callable=AsyncMock) as mock_initialize:
            mock_initialize.side_effect = seed_initialize
            await service.run(mock_gateway)

    @pytest.mark.asyncio
    async def test_run_initialize_fails(self, service):
        mock_gateway = MagicMock()

        with patch.object(service, "initialize", side_effect=Exception("API Error")):
            await service.run(mock_gateway)

    @pytest.mark.asyncio
    async def test_run_completes_all_levels(self, service):
        mock_gateway = MagicMock()
        service.MAX_LEVEL = 2
        call_count = 0

        async def seed_initialize(_gateway):
            await self._seed_level(service, 0)

        async def mock_run_iteration(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                service.shutdown_event.set()
            return True

        async def refresh_level(*args, **kwargs):
            return call_count

        with patch.object(service, "initialize", new_callable=AsyncMock) as mock_initialize:
            mock_initialize.side_effect = seed_initialize
            with patch.object(service, "run_iteration", mock_run_iteration):
                with patch.object(service, "get_current_level", side_effect=refresh_level):
                    await service.run(mock_gateway)

        assert service.current_level >= 1

    @pytest.mark.asyncio
    async def test_run_reaches_max_level_in_loop(self, service):
        mock_gateway = MagicMock()
        service.MAX_LEVEL = 3

        async def seed_initialize(_gateway):
            await self._seed_level(service, 2)

        with patch.object(service, "initialize", new_callable=AsyncMock) as mock_initialize:
            mock_initialize.side_effect = seed_initialize
            with patch.object(service, "run_iteration", new_callable=AsyncMock, return_value=True):
                with patch.object(
                    service, "get_current_level", new_callable=AsyncMock, return_value=3
                ):
                    await service.run(mock_gateway)

        assert service.current_level == 3

    @pytest.mark.asyncio
    async def test_run_logs_progress_at_interval(self, service):
        mock_gateway = MagicMock()
        service.MAX_LEVEL = 20
        service.PROGRESS_INTERVAL = 10
        call_count = 0

        async def seed_initialize(_gateway):
            await self._seed_level(service, 0)

        async def mock_run_iteration(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 11:
                service.shutdown_event.set()
            return True

        async def refresh_level(*args, **kwargs):
            return call_count

        with patch.object(service, "initialize", new_callable=AsyncMock) as mock_initialize:
            mock_initialize.side_effect = seed_initialize
            with patch.object(service, "run_iteration", mock_run_iteration):
                with patch("src.services.levelup_service.logger") as mock_logger:
                    with patch.object(service, "get_current_level", side_effect=refresh_level):
                        await service.run(mock_gateway)

        progress_calls = [
            call for call in mock_logger.info.call_args_list if "Progress" in str(call)
        ]
        assert len(progress_calls) >= 1

    @pytest.mark.asyncio
    async def test_run_sleeps_on_iteration_failure(self, service):
        mock_gateway = MagicMock()
        service.MAX_LEVEL = 5
        call_count = 0

        async def seed_initialize(_gateway):
            await self._seed_level(service, 1)

        async def mock_run_iteration(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                service.shutdown_event.set()
            return False

        with patch.object(service, "initialize", new_callable=AsyncMock) as mock_initialize:
            mock_initialize.side_effect = seed_initialize
            with patch.object(service, "run_iteration", mock_run_iteration):
                with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                    await service.run(mock_gateway)

        short_sleep_calls = [
            call
            for call in mock_sleep.call_args_list
            if call.args == (0.5,) or (len(call.args) > 0 and call.args[0] == 0.5)
        ]
        assert len(short_sleep_calls) >= 1

    @pytest.mark.asyncio
    async def test_run_refreshes_level_from_api_after_success(self, service):
        mock_gateway = MagicMock()
        service.MAX_LEVEL = 10

        async def seed_initialize(_gateway):
            await self._seed_level(service, 1)

        async def stop_after_success(*args, **kwargs):
            service.shutdown_event.set()
            return True

        with patch.object(service, "initialize", new_callable=AsyncMock) as mock_initialize:
            mock_initialize.side_effect = seed_initialize
            with patch.object(service, "run_iteration", side_effect=stop_after_success):
                with patch.object(
                    service, "get_current_level", new_callable=AsyncMock, return_value=4
                ):
                    await service.run(mock_gateway)

        assert service.current_level == 4

    async def _seed_level(self, service: LevelUpService, level: int) -> None:
        service._current_level = level
        service._farm_task_id = "task-id"
