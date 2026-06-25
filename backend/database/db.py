import asyncio
import logging
import subprocess
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


def _ensure_sqlite_dir(url: str) -> None:
    if url.startswith("sqlite"):
        path_part = url.split("///", maxsplit=1)[-1]
        Path(path_part).parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_dir(settings.database_url)

_engine_kwargs: dict = {"echo": False, "pool_pre_ping": True}
if settings.database_url.startswith("postgresql"):
    _engine_kwargs.update(pool_size=5, max_overflow=10)

engine = create_async_engine(settings.database_url, **_engine_kwargs)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def _migrate_sqlite(conn) -> None:
    """Add columns to existing SQLite tables (create_all skips alters)."""
    if not settings.database_url.startswith("sqlite"):
        return

    def column_names(table: str) -> set[str]:
        rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
        return {row[1] for row in rows}

    orders_cols = column_names("orders")
    if "payment_method" not in orders_cols:
        conn.execute(
            text("ALTER TABLE orders ADD COLUMN payment_method VARCHAR(16) NOT NULL DEFAULT 'CASH'")
        )
        logger.info("Added orders.payment_method")
    if "payment_status" not in orders_cols:
        conn.execute(
            text("ALTER TABLE orders ADD COLUMN payment_status VARCHAR(16) NOT NULL DEFAULT 'PENDING'")
        )
        logger.info("Added orders.payment_status")
    if "referral_discount" not in orders_cols:
        conn.execute(
            text("ALTER TABLE orders ADD COLUMN referral_discount FLOAT NOT NULL DEFAULT 0.0")
        )
        logger.info("Added orders.referral_discount")

    users_cols = column_names("users")
    if "referral_code" not in users_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN referral_code VARCHAR(16)"))
        logger.info("Added users.referral_code")
    if "referred_by_id" not in users_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN referred_by_id INTEGER"))
        logger.info("Added users.referred_by_id")
    if "referral_balance" not in users_cols:
        conn.execute(
            text("ALTER TABLE users ADD COLUMN referral_balance FLOAT NOT NULL DEFAULT 0.0")
        )
        logger.info("Added users.referral_balance")
    if "referral_welcome_claimed" not in users_cols:
        conn.execute(
            text("ALTER TABLE users ADD COLUMN referral_welcome_claimed BOOLEAN NOT NULL DEFAULT 0")
        )
        logger.info("Added users.referral_welcome_claimed")
    if "ton_wallet_address" not in users_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN ton_wallet_address VARCHAR(128)"))
        logger.info("Added users.ton_wallet_address")
    if "wellness_consent" not in users_cols:
        conn.execute(
            text("ALTER TABLE users ADD COLUMN wellness_consent BOOLEAN NOT NULL DEFAULT 0")
        )
        logger.info("Added users.wellness_consent")
    if "wellness_consent_at" not in users_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN wellness_consent_at DATETIME"))
        logger.info("Added users.wellness_consent_at")
    if "diet_preference" not in users_cols:
        conn.execute(text("ALTER TABLE users ADD COLUMN diet_preference VARCHAR(256)"))
        logger.info("Added users.diet_preference")
    if "activity_level" not in users_cols:
        conn.execute(
            text("ALTER TABLE users ADD COLUMN activity_level VARCHAR(16) NOT NULL DEFAULT 'moderate'")
        )
        logger.info("Added users.activity_level")

    mem_cols = column_names("user_memory")
    if "wellness_state" not in mem_cols:
        conn.execute(text("ALTER TABLE user_memory ADD COLUMN wellness_state TEXT NOT NULL DEFAULT '{}'"))
        logger.info("Added user_memory.wellness_state")

    foods_cols = column_names("foods")
    if "ingredients" not in foods_cols:
        conn.execute(text("ALTER TABLE foods ADD COLUMN ingredients TEXT NOT NULL DEFAULT ''"))
        logger.info("Added foods.ingredients")

    # Users with deliveries before referral rollout should not get retroactive welcome bonus.
    conn.execute(
        text(
            """
            UPDATE users SET referral_welcome_claimed = 1
            WHERE referral_welcome_claimed = 0 AND id IN (
                SELECT DISTINCT buyer_id FROM orders WHERE status = 'DELIVERED'
            )
            """
        )
    )


async def run_migrations() -> None:
    """Apply Alembic migrations (Postgres prod + dev parity)."""
    root = Path(__file__).resolve().parents[2]

    def _upgrade() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )

    proc = await asyncio.to_thread(_upgrade)
    if proc.returncode != 0:
        logger.warning("Alembic upgrade skipped or failed: %s", (proc.stderr or proc.stdout).strip())
    else:
        logger.info("Alembic migrations at head")


async def init_db() -> None:
    from backend import models  # noqa: F401  (register all models in metadata)

    await run_migrations()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate_sqlite)
    logger.info("Database initialized (%s)", settings.database_url.split("@")[-1])
