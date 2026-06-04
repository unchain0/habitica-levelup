from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from main import main


class TestMain:
    @pytest.mark.asyncio
    async def test_main_success(self):
        with patch("src.delivery.cli.load_dotenv"), patch("src.delivery.cli.Settings"):
            with patch("src.delivery.cli.LevelUpBot") as mock_bot_class:
                mock_bot = MagicMock()
                mock_bot.run = AsyncMock()
                mock_bot_class.return_value = mock_bot

                await main()

                mock_bot.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_config_error(self):
        with patch("src.delivery.cli.load_dotenv"):
            with patch("src.delivery.cli.Settings", side_effect=Exception("Config error")):
                with patch("src.delivery.cli.logger") as mock_logger:
                    with pytest.raises(SystemExit) as exc_info:
                        await main()

                    assert exc_info.value.code == 1
                    mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_runtime_error(self):
        with patch("src.delivery.cli.load_dotenv"), patch("src.delivery.cli.Settings"):
            with patch("src.delivery.cli.LevelUpBot") as mock_bot_class:
                mock_bot = MagicMock()
                mock_bot.run = AsyncMock(side_effect=Exception("Runtime error"))
                mock_bot_class.return_value = mock_bot

                with patch("src.delivery.cli.logger"):
                    with pytest.raises(SystemExit) as exc_info:
                        await main()

                    assert exc_info.value.code == 1
