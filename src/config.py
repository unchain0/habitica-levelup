"""Habitica Level Up Bot - Configuration Module.

Environment variable validation and settings management.
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated application configuration.

    All environment variables are validated at startup.
    The app will fail fast with a clear error message if any required
    variable is missing or invalid.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    USER_ID: str = Field(..., min_length=1, description="Habitica user ID")
    API_TOKEN: str = Field(..., min_length=1, description="Habitica API token")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    @field_validator("USER_ID", "API_TOKEN")
    @classmethod
    def validate_not_placeholder(cls, v: str) -> str:
        placeholders = {"changeme", "placeholder", "your-user-id", "your-api-token", ""}
        if v.lower() in placeholders:
            raise ValueError(f"Value cannot be a placeholder: {v}")
        return v
