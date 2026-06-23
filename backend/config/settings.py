from pathlib import Path
import os

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = Path("/data") if Path("/data").is_dir() else BASE_DIR / "database"


def _hf_space_url() -> str:
    """Hugging Face Docker Space: SPACE_ID=owner/name -> https://owner-name.hf.space"""
    space_id = os.environ.get("SPACE_ID", "").strip()
    if not space_id or "/" not in space_id:
        return ""
    owner, name = space_id.split("/", 1)
    slug = name.lower().replace("_", "-")
    return f"https://{owner.lower()}-{slug}.hf.space"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str
    admin_id: int = 0
    webapp_url: str = ""
    # Отдельный секрет webhook (если пусто — выводится из BOT_TOKEN).
    webhook_secret: str = ""

    # Cloud: webhook вместо polling (Render/Railway ставят USE_WEBHOOK=1).
    use_webhook: bool = False
    # Render.com подставляет сам; Railway — задайте WEBAPP_URL или PUBLIC_URL.
    render_external_url: str = Field(default="", validation_alias="RENDER_EXTERNAL_URL")
    koyeb_public_url: str = Field(default="", validation_alias="KOYEB_PUBLIC_URL")
    vercel_url: str = Field(default="", validation_alias="VERCEL_URL")
    public_url_override: str = Field(default="", validation_alias="PUBLIC_URL")
    keep_alive_interval_minutes: int = 10

    database_url: str = Field(
        default_factory=lambda: f"sqlite+aiosqlite:///{(DATA_DIR / 'food_mafia.db').as_posix()}"
    )

    host: str = "0.0.0.0"
    port: int = Field(default=8000, validation_alias="PORT")

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        if isinstance(value, str):
            if value.startswith("postgres://"):
                return "postgresql+asyncpg://" + value[len("postgres://") :]
            if value.startswith("postgresql://"):
                return "postgresql+asyncpg://" + value[len("postgresql://") :]
        return value

    @property
    def public_url(self) -> str:
        for candidate in (
            self.webapp_url,
            self.public_url_override,
            self.koyeb_public_url,
            self.render_external_url,
            self.vercel_url,
            _hf_space_url(),
        ):
            if candidate:
                return candidate.rstrip("/")
        return ""

    # Active-Passive cluster (Koyeb primary + Vercel standby)
    cluster_role: str = Field(default="primary", validation_alias="CLUSTER_ROLE")
    cluster_peer_url: str = Field(default="", validation_alias="CLUSTER_PEER_URL")
    redis_url: str = Field(default="", validation_alias="REDIS_URL")
    instance_id: str = Field(default="", validation_alias="INSTANCE_ID")
    lock_key: str = "food-mafia:bot-leader"
    lock_ttl_seconds: int = 45
    cron_secret: str = Field(default="", validation_alias="CRON_SECRET")
    watchdog_enabled: bool = True
    watchdog_max_memory_mb: int = 480
    watchdog_max_critical_errors: int = 8
    watchdog_interval_seconds: int = 30

    upload_dir: Path = BASE_DIR / "uploads"
    max_upload_size: int = 5 * 1024 * 1024  # 5 MB

    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    init_data_max_age_seconds: int = 86400

    # Comma-separated fallback URLs for health checks (optional).
    fallback_urls: str = Field(default="", validation_alias="BACKEND_URLS")
    platform_commission_rate: float = 0.01

    referral_referrer_bonus: float = 50.0  # Stars
    referral_referee_bonus: float = 30.0  # Stars
    referral_max_discount_rate: float = 0.15
    ton_per_star: float = 0.004  # Display / TON payment conversion hint

    ai_refresh_interval_minutes: int = 360
    ai_market_radius_m: float = 10_000

    log_level: str = "INFO"


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
