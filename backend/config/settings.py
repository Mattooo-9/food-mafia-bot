from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str
    admin_id: int = 0
    webapp_url: str = ""

    # Cloud mode: receive Telegram updates via webhook instead of polling.
    use_webhook: bool = False
    # Render.com injects this automatically with the public service URL.
    render_external_url: str = ""
    # Self-ping to prevent free-tier hosting from sleeping (minutes, 0 = off).
    keep_alive_interval_minutes: int = 10

    database_url: str = f"sqlite+aiosqlite:///{(BASE_DIR / 'database' / 'food_mafia.db').as_posix()}"

    host: str = "0.0.0.0"
    port: int = 8000

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        """Accept plain postgres:// URLs (as provided by cloud hosts) for asyncpg."""
        if isinstance(value, str):
            if value.startswith("postgres://"):
                return "postgresql+asyncpg://" + value[len("postgres://"):]
            if value.startswith("postgresql://"):
                return "postgresql+asyncpg://" + value[len("postgresql://"):]
        return value

    @property
    def public_url(self) -> str:
        return (self.webapp_url or self.render_external_url).rstrip("/")

    upload_dir: Path = BASE_DIR / "uploads"
    max_upload_size: int = 5 * 1024 * 1024  # 5 MB

    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60

    init_data_max_age_seconds: int = 86400
    platform_commission_rate: float = 0.01

    log_level: str = "INFO"


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
