import os

import pytest
from pydantic import ValidationError

from src.config import Settings


@pytest.fixture(autouse=True)
def clean_env():
    os.environ.pop("USER_ID", None)
    os.environ.pop("API_TOKEN", None)
    os.environ.pop("LOG_LEVEL", None)
    os.environ.pop("EXTRA_FIELD", None)
    yield


class TestSettings:
    def test_settings_valid(self, clean_env):
        settings = Settings(
            USER_ID="valid-user-id-123",
            API_TOKEN="valid-api-token-456",
            LOG_LEVEL="DEBUG",
            _env_file=None,
        )
        assert settings.USER_ID == "valid-user-id-123"
        assert settings.API_TOKEN == "valid-api-token-456"
        assert settings.LOG_LEVEL == "DEBUG"

    def test_settings_defaults(self, clean_env):
        settings = Settings(
            USER_ID="user123",
            API_TOKEN="token456",
            _env_file=None,
        )
        assert settings.LOG_LEVEL == "INFO"

    def test_settings_missing_user_id(self, clean_env):
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                API_TOKEN="token456",
                _env_file=None,
            )

        assert "USER_ID" in str(exc_info.value)

    def test_settings_missing_api_token(self, clean_env):
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                USER_ID="user123",
                _env_file=None,
            )

        assert "API_TOKEN" in str(exc_info.value)

    def test_settings_empty_user_id(self, clean_env):
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                USER_ID="",
                API_TOKEN="token456",
                _env_file=None,
            )

        assert "USER_ID" in str(exc_info.value)

    def test_settings_empty_api_token(self, clean_env):
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                USER_ID="user123",
                API_TOKEN="",
                _env_file=None,
            )

        assert "API_TOKEN" in str(exc_info.value)

    def test_settings_placeholder_changeme(self, clean_env):
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                USER_ID="changeme",
                API_TOKEN="token456",
                _env_file=None,
            )

        assert "placeholder" in str(exc_info.value).lower()

    def test_settings_placeholder_placeholder(self, clean_env):
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                USER_ID="user123",
                API_TOKEN="placeholder",
                _env_file=None,
            )

        assert "placeholder" in str(exc_info.value).lower()

    def test_settings_placeholder_your_user_id(self, clean_env):
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                USER_ID="your-user-id",
                API_TOKEN="token456",
                _env_file=None,
            )

        assert "placeholder" in str(exc_info.value).lower()

    def test_settings_forbid_extra_fields(self, clean_env):
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                USER_ID="user123",
                API_TOKEN="token456",
                EXTRA_FIELD="should_fail",
                _env_file=None,
            )

        assert "EXTRA_FIELD" in str(exc_info.value)
