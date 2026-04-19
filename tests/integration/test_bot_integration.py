import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.delivery.bot_runner import LevelUpBot
from src.delivery.settings import Settings


class TestBotInfrastructureIntegration:
    @pytest.fixture
    def settings(self):
        return Settings(
            USER_ID="test-user-id",
            API_TOKEN="test-api-token",
            LOG_LEVEL="DEBUG",
            _env_file=None,
        )

    @pytest.fixture
    def bot(self, settings):
        service = MagicMock()
        service.shutdown_event = asyncio.Event()

        async def run_once(_gateway):
            service.shutdown_event.set()

        service.run = AsyncMock(side_effect=run_once)
        return LevelUpBot(settings, service=service)

    @pytest.mark.asyncio
    async def test_bot_uses_optimized_session(self, bot):
        mock_session_manager = MagicMock()
        mock_session_manager.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_session_manager.__aexit__ = AsyncMock(return_value=None)
        bot._session_factory = MagicMock(return_value=mock_session_manager)
        bot._gateway_factory = MagicMock(return_value=MagicMock())

        await bot.run()

        bot._session_factory.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_to_end_flow(self, bot):
        gateway = MagicMock()
        mock_session_manager = MagicMock()
        mock_session_manager.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_session_manager.__aexit__ = AsyncMock(return_value=None)
        bot._session_factory = MagicMock(return_value=mock_session_manager)
        bot._gateway_factory = MagicMock(return_value=gateway)

        await bot.run()

        bot.service.run.assert_awaited_once_with(gateway)

    @pytest.mark.asyncio
    async def test_bot_retries_after_unexpected_service_return(self, settings):
        service = MagicMock()
        service.shutdown_event = asyncio.Event()

        async def first_then_stop(_gateway):
            if service.run.await_count >= 2:
                service.shutdown_event.set()

        service.run = AsyncMock(side_effect=first_then_stop)
        bot = LevelUpBot(settings, service=service)

        gateway = MagicMock()
        mock_session_manager = MagicMock()
        mock_session_manager.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_session_manager.__aexit__ = AsyncMock(return_value=None)
        bot._session_factory = MagicMock(return_value=mock_session_manager)
        bot._gateway_factory = MagicMock(return_value=gateway)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await bot.run()

        assert service.run.await_count == 2
        mock_sleep.assert_awaited_once_with(bot.RESTART_DELAY)

    @pytest.mark.asyncio
    async def test_bot_does_not_run_when_shutdown_already_requested(self, settings):
        service = MagicMock()
        service.shutdown_event = asyncio.Event()
        service.shutdown_event.set()
        service.run = AsyncMock(return_value=None)
        bot = LevelUpBot(settings, service=service)

        mock_session_manager = MagicMock()
        mock_session_manager.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_session_manager.__aexit__ = AsyncMock(return_value=None)
        bot._session_factory = MagicMock(return_value=mock_session_manager)
        bot._gateway_factory = MagicMock(return_value=MagicMock())

        await bot.run()

        service.run.assert_not_called()

    @pytest.mark.asyncio
    async def test_setup_signal_handlers_windows(self, bot):
        loop = asyncio.get_running_loop()

        with patch.object(loop, "add_signal_handler", side_effect=NotImplementedError()):
            bot.setup_signal_handlers()

    @pytest.mark.asyncio
    async def test_signal_handler_sets_shutdown_event(self, settings):
        service = MagicMock()
        service.run = AsyncMock(return_value=None)
        service.shutdown_event = asyncio.Event()
        bot = LevelUpBot(settings, service=service)

        bot.setup_signal_handlers()
        assert service.shutdown_event.is_set() is False

        loop = asyncio.get_running_loop()
        for handler in [registered for registered in loop._signal_handlers.values() if registered]:
            if hasattr(handler, "_callback"):
                handler._callback()
                break

        assert service.shutdown_event.is_set() is True


class TestCircuitBreakerIntegration:
    @pytest.fixture
    def settings(self):
        return Settings(
            USER_ID="test-user",
            API_TOKEN="test-token",
            LOG_LEVEL="INFO",
            _env_file=None,
        )

    @pytest.fixture
    def bot(self, settings):
        return LevelUpBot(settings)

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self, bot):
        bot.service.circuit_breaker.max_failures = 3

        for _ in range(3):
            bot.service.circuit_breaker.record_failure()

        assert bot.service.circuit_breaker.is_open() is True

    @pytest.mark.asyncio
    async def test_circuit_breaker_closes_after_timeout(self, bot):
        bot.service.circuit_breaker.max_failures = 3
        bot.service.circuit_breaker.reset_timeout = timedelta(seconds=0)

        for _ in range(3):
            bot.service.circuit_breaker.record_failure()

        assert bot.service.circuit_breaker.is_open() is False


class TestTaskCreationIntegration:
    @pytest.fixture
    def settings(self):
        return Settings(
            USER_ID="test-user",
            API_TOKEN="test-token",
            LOG_LEVEL="INFO",
            _env_file=None,
        )

    @pytest.mark.asyncio
    async def test_task_created_before_farming(self, settings):
        service = MagicMock()
        service.shutdown_event = asyncio.Event()

        async def run_once(_gateway):
            service.shutdown_event.set()

        service.run = AsyncMock(side_effect=run_once)
        bot = LevelUpBot(settings, service=service)

        gateway = MagicMock()
        mock_session_manager = MagicMock()
        mock_session_manager.__aenter__ = AsyncMock(return_value=MagicMock())
        mock_session_manager.__aexit__ = AsyncMock(return_value=None)
        bot._session_factory = MagicMock(return_value=mock_session_manager)
        bot._gateway_factory = MagicMock(return_value=gateway)

        with patch("src.delivery.bot_runner.setup_logging"):
            await bot.run()

        service.run.assert_awaited_once_with(gateway)
