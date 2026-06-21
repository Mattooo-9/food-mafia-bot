from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base
from backend.models.enums import OrderStatus, PaymentMethod, PaymentStatus


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buyer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    cook_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    food_id: Mapped[int] = mapped_column(
        ForeignKey("foods.id", ondelete="CASCADE"), index=True, nullable=False
    )

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(
        String(16), default=OrderStatus.NEW.value, index=True, nullable=False
    )
    comment: Mapped[str] = mapped_column(String(512), default="", nullable=False)
    payment_method: Mapped[str] = mapped_column(
        String(16), default=PaymentMethod.CASH.value, nullable=False
    )
    payment_status: Mapped[str] = mapped_column(
        String(16), default=PaymentStatus.PENDING.value, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    buyer: Mapped["User"] = relationship(foreign_keys=[buyer_id])  # noqa: F821
    cook: Mapped["User"] = relationship(foreign_keys=[cook_id])  # noqa: F821
    food: Mapped["Food"] = relationship()  # noqa: F821
