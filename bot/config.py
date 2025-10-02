"""Bot configuration using pydantic-settings"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram Bot
    telegram_bot_token: str = Field(..., description="Telegram Bot API token from @BotFather")
    telegram_admin_ids: str = Field(
        default="",
        description="Comma-separated list of initial admin Telegram IDs",
    )

    # Marzban API
    marzban_api_url: str = Field(
        default="https://marzban.gezzy.ru",
        description="Marzban API base URL",
    )
    marzban_admin_username: str = Field(..., description="Marzban admin username")
    marzban_admin_password: str = Field(..., description="Marzban admin password")

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://marzban_bot:password@localhost:5432/marzban_bot",
        description="PostgreSQL database URL",
    )

    # Application
    log_level: str = Field(default="INFO", description="Logging level")
    subscription_base_url: str = Field(
        default="https://marzban.gezzy.ru/sub",
        description="Base URL for subscription links",
    )

    @field_validator("telegram_admin_ids")
    @classmethod
    def parse_admin_ids(cls, v: str) -> list[int]:
        """Parse comma-separated admin IDs"""
        if not v:
            return []
        return [int(x.strip()) for x in v.split(",") if x.strip()]

    @property
    def admin_ids(self) -> list[int]:
        """Get list of admin Telegram IDs"""
        if isinstance(self.telegram_admin_ids, str):
            return self.parse_admin_ids(self.telegram_admin_ids)
        return self.telegram_admin_ids


settings = Settings()
