from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class OrderWishStatus(str, Enum):
    OPEN = "OPEN"
    CLAIMED = "CLAIMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class OrderWish(Base):
    """Запрос покупателя — повара забирают сами."""

    __tablename__ = "order_wishes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buyer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    details: Mapped[str] = mapped_column(Text, default="", nullable=False)
    category_path: Mapped[str | None] = mapped_column(String(256), nullable=True)
    budget_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    portions: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), default=OrderWishStatus.OPEN.value, index=True, nullable=False
    )
    cook_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    buyer: Mapped["User"] = relationship(foreign_keys=[buyer_id])  # noqa: F821
    cook: Mapped["User | None"] = relationship(foreign_keys=[cook_id])  # noqa: F821
