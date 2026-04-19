"""Runtime configuration for delivery layer."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    USER_ID: str = Field(
        default="",
        min_length=1,
        description="Habitica user ID",
        validate_default=True,
    )
    API_TOKEN: str = Field(
        default="",
        min_length=1,
        description="Habitica API token",
        validate_default=True,
    )
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    @field_validator("USER_ID", "API_TOKEN")
    @classmethod
    def validate_not_placeholder(cls, value: str) -> str:
        placeholders = {"changeme", "placeholder", "your-user-id", "your-api-token", ""}
        if value.lower() in placeholders:
            raise ValueError(f"Value cannot be a placeholder: {value}")
        return value
