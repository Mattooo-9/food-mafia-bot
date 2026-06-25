"""Сжатый профиль пользователя для быстрых персональных подсказок."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class UserMemory(Base):
    __tablename__ = "user_memory"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    # JSON: {"Горячие блюда": 3, "Супы": 2}
    group_counts: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    # JSON: ["борщ", "салат"]
    recent_queries: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    last_group: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_category_path: Mapped[str | None] = mapped_column(String(256), nullable=True)
    searches_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    orders_delivered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_order_stars: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    prefers_cheap: Mapped[bool] = mapped_column(nullable=False, default=False)
    companion_note: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    wellness_state: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
