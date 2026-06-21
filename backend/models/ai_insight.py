from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


class MarketSnapshot(Base):
    """Cached market statistics per category (and optional geo region)."""

    __tablename__ = "market_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    region_key: Mapped[str] = mapped_column(String(32), index=True, default="global", nullable=False)

    dish_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    order_volume: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    median_price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    min_price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    demand_index: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    competition_index: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    trend: Mapped[str] = mapped_column(String(16), default="stable", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class FoodEvaluation(Base):
    """AI price/quality evaluation for a dish."""

    __tablename__ = "food_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    food_id: Mapped[int] = mapped_column(
        ForeignKey("foods.id", ondelete="CASCADE"), index=True, unique=True, nullable=False
    )

    price_score: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    quality_score: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    demand_score: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    overall_score: Mapped[int] = mapped_column(Integer, default=50, nullable=False)

    verdict: Mapped[str] = mapped_column(String(24), default="fair", nullable=False)
    fair_price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    suggested_price_min: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    suggested_price_max: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    buyer_tip: Mapped[str] = mapped_column(Text, default="", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
