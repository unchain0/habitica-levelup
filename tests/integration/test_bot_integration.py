from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bot import LevelUpBot
from src.config import Settings


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
        return LevelUpBot(settings)

    @pytest.mark.asyncio
    async def test_bot_uses_optimized_session(self, bot):
        with patch("src.bot.OptimizedClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch.object(bot, "get_current_level", new_callable=AsyncMock, return_value=1):
                with patch("src.bot.get_or_create_farm_task", new_callable=AsyncMock):
                    bot.shutdown_event.set()
                    await bot.run()

            mock_session_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_to_end_flow(self, bot):
        with patch("src.bot.OptimizedClientSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value.__aexit__ = AsyncMock(return_value=None)

            MagicMock()

            with patch.object(bot, "get_current_level", new_callable=AsyncMock, return_value=1):
                with patch(
                    "src.bot.get_or_create_farm_task",
                    new_callable=AsyncMock,
                    return_value="farm-task-id",
                ) as mock_get_task:
                    bot.shutdown_event.set()
                    await bot.run()

                    mock_get_task.assert_called_once()


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
        bot.circuit_breaker.max_failures = 3

        for _ in range(3):
            bot.circuit_breaker.record_failure()

        assert bot.circuit_breaker.is_open() is True

    @pytest.mark.asyncio
    async def test_circuit_breaker_closes_after_timeout(self, bot):
        from datetime import timedelta

        bot.circuit_breaker.max_failures = 3
        bot.circuit_breaker.reset_timeout = timedelta(seconds=0)

        for _ in range(3):
            bot.circuit_breaker.record_failure()

        assert bot.circuit_breaker.is_open() is False


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
        bot = LevelUpBot(settings)

        with patch("src.bot.OptimizedClientSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch.object(bot, "get_current_level", new_callable=AsyncMock, return_value=1):
                with patch(
                    "src.bot.get_or_create_farm_task",
                    new_callable=AsyncMock,
                    return_value="new-task-id",
                ) as mock_get_task:
                    bot.shutdown_event.set()
                    await bot.run()

                    mock_get_task.assert_called_once()
