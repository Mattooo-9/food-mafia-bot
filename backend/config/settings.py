from pathlib import Path

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

    database_url: str = f"sqlite+aiosqlite:///{(BASE_DIR / 'database' / 'food_mafia.db').as_posix()}"

    host: str = "0.0.0.0"
    port: int = 8000

    upload_dir: Path = BASE_DIR / "uploads"
    max_upload_size: int = 5 * 1024 * 1024  # 5 MB

    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60

    init_data_max_age_seconds: int = 86400
    platform_commission_rate: float = 0.01

    log_level: str = "INFO"


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
