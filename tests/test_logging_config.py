from pathlib import Path
from unittest.mock import patch

from src.logging_config import setup_logging


class TestSetupLogging:
    def test_setup_logging_removes_default_handler(self):
        with patch("src.logging_config.logger") as mock_logger:
            setup_logging("INFO")
            mock_logger.remove.assert_called_once()

    def test_setup_logging_adds_stderr_handler(self):
        with patch("src.logging_config.logger") as mock_logger:
            with patch("src.logging_config.sys.stderr"):
                setup_logging("INFO")

                calls = mock_logger.add.call_args_list
                assert len(calls) == 2

    def test_setup_logging_adds_file_handler(self):
        with patch("src.logging_config.logger") as mock_logger:
            with patch("src.logging_config.sys.stderr"):
                with patch("pathlib.Path.mkdir"):
                    setup_logging("INFO")

                    calls = mock_logger.add.call_args_list
                    assert len(calls) == 2

    def test_setup_logging_creates_log_directory(self):
        with patch("src.logging_config.logger"), patch("src.logging_config.sys.stderr"):
            with patch.object(Path, "mkdir") as mock_mkdir:
                setup_logging("INFO")
                mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_setup_logging_with_different_levels(self):
        levels = ["DEBUG", "INFO", "WARNING", "ERROR"]

        for level in levels:
            with patch("src.logging_config.logger") as mock_logger:
                with patch("src.logging_config.sys.stderr"):
                    with patch("pathlib.Path.mkdir"):
                        setup_logging(level)

                        calls = mock_logger.add.call_args_list
                        stderr_call = calls[0]
                        assert stderr_call[1]["level"] == level
