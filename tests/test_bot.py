import asyncio
import signal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from habiticalib import Attributes
from habiticalib.exceptions import TooManyRequestsError
from habiticalib.typedefs import HabiticaErrorResponse
from multidict import CIMultiDict

from src.bot import LevelUpBot
from src.config import Settings


class TestLevelUpBot:
    @pytest.fixture
    def mock_settings(self):
        return Settings(
            USER_ID="test-user",
            API_TOKEN="test-token",
            LOG_LEVEL="INFO",
            _env_file=None,
        )

    @pytest.fixture
    def bot(self, mock_settings):
        return LevelUpBot(mock_settings)

    @pytest.mark.asyncio
    async def test_setup_signal_handlers(self, bot):
        loop = asyncio.get_running_loop()

        with patch.object(loop, "add_signal_handler") as mock_add_handler:
            bot.setup_signal_handlers()

            assert mock_add_handler.call_count == 2

    @pytest.mark.asyncio
    async def test_setup_signal_handlers_windows(self, bot):
        loop = asyncio.get_running_loop()

        with patch.object(loop, "add_signal_handler", side_effect=NotImplementedError()):
            bot.setup_signal_handlers()

    @pytest.mark.asyncio
    async def test_get_current_level_success(self, bot):
        mock_client = MagicMock()
        mock_user = MagicMock()
        mock_user.data.stats.lvl = 42

        with patch("src.bot.with_retry") as mock_retry:
            mock_retry.return_value = mock_user
            level = await bot.get_current_level(mock_client)

        assert level == 42

    @pytest.mark.asyncio
    async def test_get_current_level_none_user(self, bot):
        mock_client = MagicMock()

        with patch("src.bot.with_retry") as mock_retry:
            mock_retry.return_value = None
            with pytest.raises(ValueError, match="User is None"):
                await bot.get_current_level(mock_client)

    @pytest.mark.asyncio
    async def test_get_current_level_none_level(self, bot):
        mock_client = MagicMock()
        mock_user = MagicMock()
        mock_user.data.stats.lvl = None

        with patch("src.bot.with_retry") as mock_retry:
            mock_retry.return_value = mock_user
            with pytest.raises(ValueError, match="Level is None"):
                await bot.get_current_level(mock_client)

    @pytest.mark.asyncio
    async def test_farm_quest(self, bot):
        mock_client = MagicMock()
        bot._farm_task_id = "task-123"

        with patch("src.bot.with_retry") as mock_retry:
            await bot.farm_quest(mock_client)
            mock_retry.assert_called_once()

    @pytest.mark.asyncio
    async def test_allocate_points(self, bot):
        mock_client = MagicMock()

        with patch("src.bot.with_retry") as mock_retry:
            await bot.allocate_points(mock_client, Attributes.STR)
            mock_retry.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_iteration_success(self, bot):
        mock_client = MagicMock()
        bot.circuit_breaker.is_open = MagicMock(return_value=False)
        bot.circuit_breaker.record_success = MagicMock()

        with patch.object(bot, "farm_quest", new_callable=AsyncMock):
            with patch.object(bot, "allocate_points", new_callable=AsyncMock):
                success = await bot.run_iteration(mock_client, Attributes.STR)

        assert success is True
        bot.circuit_breaker.record_success.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_iteration_circuit_open(self, bot):
        mock_client = MagicMock()
        bot.circuit_breaker.is_open = MagicMock(return_value=True)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            success = await bot.run_iteration(mock_client, Attributes.STR)

        assert success is False

    @pytest.mark.asyncio
    async def test_run_iteration_timeout(self, bot):
        mock_client = MagicMock()
        bot.circuit_breaker.is_open = MagicMock(return_value=False)
        bot.circuit_breaker.record_failure = MagicMock()

        with patch.object(bot, "farm_quest", side_effect=asyncio.TimeoutError()):
            success = await bot.run_iteration(mock_client, Attributes.STR)

        assert success is False
        bot.circuit_breaker.record_failure.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_iteration_rate_limited(self, bot):
        mock_client = MagicMock()
        bot.circuit_breaker.is_open = MagicMock(return_value=False)
        bot.circuit_breaker.record_failure = MagicMock()

        error_response = HabiticaErrorResponse(
            success=False, error="Rate limited", message="Too many requests"
        )
        error = TooManyRequestsError(error=error_response, headers=CIMultiDict())
        with patch.object(bot, "farm_quest", side_effect=error):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                success = await bot.run_iteration(mock_client, Attributes.STR)

        assert success is False
        bot.circuit_breaker.record_failure.assert_called_once()


class TestLevelUpBotRun:
    @pytest.fixture
    def mock_settings(self):
        return Settings(
            USER_ID="test-user",
            API_TOKEN="test-token",
            LOG_LEVEL="INFO",
            _env_file=None,
        )

    @pytest.fixture
    def bot(self, mock_settings):
        return LevelUpBot(mock_settings)

    @pytest.mark.asyncio
    async def test_run_reaches_max_level(self, bot):
        with patch("src.bot.OptimizedClientSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch.object(bot, "get_current_level", new_callable=AsyncMock, return_value=998):
                with patch("src.bot.get_or_create_farm_task", new_callable=AsyncMock, return_value="task-id"):
                    with patch.object(bot, "run_iteration", new_callable=AsyncMock, return_value=True):
                        bot._current_level = 998
                        bot.MAX_LEVEL = 999
                        bot.shutdown_event.set()
                        await bot.run()

    @pytest.mark.asyncio
    async def test_run_cancelled_error(self, bot):
        with patch("src.bot.OptimizedClientSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch.object(bot, "get_current_level", new_callable=AsyncMock, return_value=1):
                with patch("src.bot.get_or_create_farm_task", new_callable=AsyncMock, return_value="task-id"):
                    with patch.object(bot, "run_iteration", side_effect=asyncio.CancelledError()):
                        with pytest.raises(asyncio.CancelledError):
                            await bot.run()

    @pytest.mark.asyncio
    async def test_run_already_at_max_level(self, bot):
        with patch("src.bot.OptimizedClientSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch.object(bot, "get_current_level", new_callable=AsyncMock, return_value=999):
                await bot.run()

    @pytest.mark.asyncio
    async def test_run_get_level_fails(self, bot):
        with patch("src.bot.OptimizedClientSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch.object(bot, "get_current_level", side_effect=Exception("API Error")):
                await bot.run()

    @pytest.mark.asyncio
    async def test_run_get_task_fails(self, bot):
        with patch("src.bot.OptimizedClientSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch.object(bot, "get_current_level", new_callable=AsyncMock, return_value=1):
                with patch("src.bot.get_or_create_farm_task", side_effect=Exception("API Error")):
                    await bot.run()


class TestLevelUpBotSignalHandler:
    @pytest.fixture
    def mock_settings(self):
        return Settings(
            USER_ID="test-user",
            API_TOKEN="test-token",
            LOG_LEVEL="INFO",
            _env_file=None,
        )

    @pytest.fixture
    def bot(self, mock_settings):
        return LevelUpBot(mock_settings)

    @pytest.mark.asyncio
    async def test_signal_handler_sets_shutdown_event(self, bot):
        bot.setup_signal_handlers()
        assert bot.shutdown_event.is_set() is False

        loop = asyncio.get_running_loop()

        for handler in [h for h in loop._signal_handlers.values() if h is not None]:
            if hasattr(handler, '_callback'):
                handler._callback()


class TestLevelUpBotRunComplete:
    @pytest.fixture
    def mock_settings(self):
        return Settings(
            USER_ID="test-user",
            API_TOKEN="test-token",
            LOG_LEVEL="INFO",
            _env_file=None,
        )

    @pytest.fixture
    def bot(self, mock_settings):
        return LevelUpBot(mock_settings)

    @pytest.mark.asyncio
    async def test_run_completes_all_levels(self, bot):
        with patch("src.bot.OptimizedClientSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value.__aexit__ = AsyncMock(return_value=None)

            bot.MAX_LEVEL = 2
            call_count = 0

            async def mock_run_iteration(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                bot._current_level = call_count
                if call_count >= 2:
                    bot.shutdown_event.set()
                return True

            with patch.object(bot, "get_current_level", new_callable=AsyncMock, return_value=0):
                with patch("src.bot.get_or_create_farm_task", new_callable=AsyncMock, return_value="task-id"):
                    with patch.object(bot, "run_iteration", mock_run_iteration):
                        await bot.run()

            assert bot._current_level >= 1

    @pytest.mark.asyncio
    async def test_run_reaches_max_level_in_loop(self, bot):
        with patch("src.bot.OptimizedClientSession") as mock_session_class:
            mock_session = MagicMock()
            mock_session_class.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_class.return_value.__aexit__ = AsyncMock(return_value=None)

            bot.MAX_LEVEL = 3

            with patch.object(bot, "get_current_level", new_callable=AsyncMock, return_value=0):
                with patch("src.bot.get_or_create_farm_task", new_callable=AsyncMock, return_value="task-id"):
                    with patch.object(bot, "run_iteration", new_callable=AsyncMock, return_value=True):
                        bot._current_level = 2
                        await bot.run()

            assert bot._current_level == 3
