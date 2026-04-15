from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from main import main


class TestMain:
    @pytest.mark.asyncio
    async def test_main_success(self):
        with patch("main.load_dotenv"), patch("main.Settings"):
            with patch("main.LevelUpBot") as mock_bot_class:
                mock_bot = MagicMock()
                mock_bot.run = AsyncMock()
                mock_bot_class.return_value = mock_bot

                await main()

                mock_bot.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_config_error(self):
        with patch("main.load_dotenv"):
            with patch("main.Settings", side_effect=Exception("Config error")):
                with patch("main.logger") as mock_logger:
                    with pytest.raises(SystemExit) as exc_info:
                        await main()

                    assert exc_info.value.code == 1
                    mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_runtime_error(self):
        with patch("main.load_dotenv"), patch("main.Settings"):
            with patch("main.LevelUpBot") as mock_bot_class:
                mock_bot = MagicMock()
                mock_bot.run = AsyncMock(side_effect=Exception("Runtime error"))
                mock_bot_class.return_value = mock_bot

                with patch("main.logger"):
                    with pytest.raises(SystemExit) as exc_info:
                        await main()

                    assert exc_info.value.code == 1
