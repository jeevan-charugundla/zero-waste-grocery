from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    groq_api_key: str = ""
    groq_model: str = "qwen/qwen3.8-27b"

    # Telegram Bot & Reminders Configuration
    telegram_bot_token: str = ""
    telegram_allowed_user_ids: str = ""
    telegram_default_store_id: str = ""
    telegram_data_mode: str = "demo"  # "demo" or "supabase"
    telegram_reminders_enabled: bool = True
    telegram_reminder_interval_minutes: int = 60
    telegram_briefing_hour: int = 8
    telegram_evening_hour: int = 19
    telegram_quiet_hours_start: int = 22
    telegram_quiet_hours_end: int = 7

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]

    @property
    def allowed_telegram_user_ids(self) -> set[int]:
        ids: set[int] = set()
        for item in self.telegram_allowed_user_ids.split(","):
            cleaned = item.strip()
            if cleaned and cleaned.isdigit():
                ids.add(int(cleaned))
        return ids

@lru_cache
def get_settings() -> Settings:
    return Settings()
