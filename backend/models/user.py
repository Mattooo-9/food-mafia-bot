from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Cook profile
    is_cook: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cook_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cook_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cook_photo: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rating_avg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    rating_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    referral_code: Mapped[str | None] = mapped_column(String(16), unique=True, nullable=True)
    referred_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    referral_balance: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    referral_welcome_claimed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ton_wallet_address: Mapped[str | None] = mapped_column(String(128), nullable=True)

    wellness_consent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    wellness_consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    diet_preference: Mapped[str | None] = mapped_column(String(256), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    foods: Mapped[list["Food"]] = relationship(  # noqa: F821
        back_populates="cook", cascade="all, delete-orphan"
    )
