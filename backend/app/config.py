"""Runtime configuration, loaded from environment / .env."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings for all backend jobs.

    Values come from environment variables (GitHub Actions secrets in CI) or a local
    ``.env`` file during development.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Supabase
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # Telegram
    telegram_bot_token: str = ""

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # CIN encryption (Fernet key)
    cin_encryption_key: str = ""

    # Scraping
    http_user_agent: str = "ConcoursWatcher/0.1"
    request_timeout_seconds: int = 30

    # Telethon (optional, later phase)
    telethon_api_id: str = ""
    telethon_api_hash: str = ""
    telethon_session: str = ""

    @property
    def supabase_rest_url(self) -> str:
        return f"{self.supabase_url.rstrip('/')}/rest/v1"


@lru_cache
def get_settings() -> Settings:
    """Cached singleton so we parse the environment only once per process."""
    return Settings()
