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
    # Public channel the publisher posts to, as an @username (not a secret): @RaqibEmploi
    telegram_channel_id: str = ""

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # CIN encryption (Fernet key)
    cin_encryption_key: str = ""

    # Publisher: false = post every concours (IT ones get a hashtag), true = IT only
    publish_it_only: bool = False

    # WhatsApp digest: the bot sends a ready-to-paste digest to this Telegram chat
    # (the owner's numeric id). Empty = no digest.
    owner_chat_id: str = ""
    whatsapp_channel_url: str = "https://whatsapp.com/channel/0029VbEJN8rIXnlxFgLlea1w"
    website_url: str = "https://raqib-emploi.pages.dev"

    # Scraping
    http_user_agent: str = "RaqibBot/0.1 (+https://t.me/RaqibEmploi; https://github.com/oussama-zbair/raqib)"
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
