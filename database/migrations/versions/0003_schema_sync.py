"""Sync schema: payments, referral, wellness, AI tables

Revision ID: 0003
Revises: 0002
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return column in {c["name"] for c in insp.get_columns(table)}


def _has_table(table: str) -> bool:
    bind = op.get_bind()
    return table in sa.inspect(bind).get_table_names()


def upgrade() -> None:
    if not _has_column("users", "referral_code"):
        op.add_column("users", sa.Column("referral_code", sa.String(length=16), nullable=True))
    if not _has_column("users", "referred_by_id"):
        op.add_column("users", sa.Column("referred_by_id", sa.Integer(), nullable=True))
    if not _has_column("users", "referral_balance"):
        op.add_column(
            "users",
            sa.Column("referral_balance", sa.Float(), nullable=False, server_default="0"),
        )
    if not _has_column("users", "referral_welcome_claimed"):
        op.add_column(
            "users",
            sa.Column("referral_welcome_claimed", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if not _has_column("users", "ton_wallet_address"):
        op.add_column("users", sa.Column("ton_wallet_address", sa.String(length=128), nullable=True))
    if not _has_column("users", "wellness_consent"):
        op.add_column(
            "users",
            sa.Column("wellness_consent", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if not _has_column("users", "wellness_consent_at"):
        op.add_column("users", sa.Column("wellness_consent_at", sa.DateTime(timezone=True), nullable=True))
    if not _has_column("users", "diet_preference"):
        op.add_column("users", sa.Column("diet_preference", sa.String(length=256), nullable=True))

    if not _has_column("orders", "payment_method"):
        op.add_column(
            "orders",
            sa.Column("payment_method", sa.String(length=16), nullable=False, server_default="CASH"),
        )
    if not _has_column("orders", "payment_status"):
        op.add_column(
            "orders",
            sa.Column("payment_status", sa.String(length=16), nullable=False, server_default="PENDING"),
        )
    if not _has_column("orders", "referral_discount"):
        op.add_column(
            "orders",
            sa.Column("referral_discount", sa.Float(), nullable=False, server_default="0"),
        )

    if not _has_column("foods", "ingredients"):
        op.add_column("foods", sa.Column("ingredients", sa.Text(), nullable=False, server_default=""))

    if not _has_table("market_snapshots"):
        op.create_table(
            "market_snapshots",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("category", sa.String(length=64), nullable=False),
            sa.Column("region_key", sa.String(length=32), nullable=False, server_default="global"),
            sa.Column("dish_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("order_volume", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("avg_price", sa.Float(), nullable=False, server_default="0"),
            sa.Column("median_price", sa.Float(), nullable=False, server_default="0"),
            sa.Column("min_price", sa.Float(), nullable=False, server_default="0"),
            sa.Column("max_price", sa.Float(), nullable=False, server_default="0"),
            sa.Column("avg_rating", sa.Float(), nullable=False, server_default="0"),
            sa.Column("demand_index", sa.Float(), nullable=False, server_default="0"),
            sa.Column("competition_index", sa.Float(), nullable=False, server_default="0"),
            sa.Column("summary", sa.Text(), nullable=False, server_default=""),
            sa.Column("trend", sa.String(length=16), nullable=False, server_default="stable"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_market_snapshots_category", "market_snapshots", ["category"])
        op.create_index("ix_market_snapshots_region_key", "market_snapshots", ["region_key"])

    if not _has_table("food_evaluations"):
        op.create_table(
            "food_evaluations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("food_id", sa.Integer(), sa.ForeignKey("foods.id", ondelete="CASCADE"), nullable=False, unique=True),
            sa.Column("price_score", sa.Integer(), nullable=False, server_default="50"),
            sa.Column("quality_score", sa.Integer(), nullable=False, server_default="50"),
            sa.Column("demand_score", sa.Integer(), nullable=False, server_default="50"),
            sa.Column("overall_score", sa.Integer(), nullable=False, server_default="50"),
            sa.Column("verdict", sa.String(length=24), nullable=False, server_default="fair"),
            sa.Column("fair_price", sa.Float(), nullable=False, server_default="0"),
            sa.Column("suggested_price_min", sa.Float(), nullable=False, server_default="0"),
            sa.Column("suggested_price_max", sa.Float(), nullable=False, server_default="0"),
            sa.Column("summary", sa.Text(), nullable=False, server_default=""),
            sa.Column("buyer_tip", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_food_evaluations_food_id", "food_evaluations", ["food_id"])


def downgrade() -> None:
    if _has_table("food_evaluations"):
        op.drop_table("food_evaluations")
    if _has_table("market_snapshots"):
        op.drop_table("market_snapshots")
