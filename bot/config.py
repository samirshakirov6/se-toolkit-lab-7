"""Configuration loader for the Telegram bot."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    """Bot configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env.bot.secret",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Telegram bot token
    bot_token: str = Field(default="", alias="BOT_TOKEN")

    # LMS API configuration
    lms_api_base_url: str = Field(default="http://localhost:42002", alias="LMS_API_BASE_URL")
    lms_api_key: str = Field(default="", alias="LMS_API_KEY")

    # LLM API configuration (for Task 3)
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_api_base_url: str = Field(default="", alias="LLM_API_BASE_URL")
    llm_api_model: str = Field(default="coder-model", alias="LLM_API_MODEL")


# Global settings instance
settings = BotSettings()
