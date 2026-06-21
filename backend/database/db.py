import logging
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

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
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


async def init_db() -> None:
    from backend import models  # noqa: F401  (register all models in metadata)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate_sqlite)
    logger.info("Database initialized (%s)", settings.database_url)
