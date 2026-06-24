"""user memory + order wishes

Revision ID: 0002
Revises: 0001
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_memory",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("group_counts", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("recent_queries", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("last_group", sa.String(length=64), nullable=True),
        sa.Column("last_category_path", sa.String(length=256), nullable=True),
        sa.Column("searches_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("orders_delivered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_order_stars", sa.Float(), nullable=False, server_default="0"),
        sa.Column("prefers_cheap", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("companion_note", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "order_wishes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("buyer_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("details", sa.Text(), nullable=False, server_default=""),
        sa.Column("category_path", sa.String(length=256), nullable=True),
        sa.Column("budget_max", sa.Float(), nullable=True),
        sa.Column("portions", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="OPEN"),
        sa.Column("cook_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_order_wishes_buyer_id", "order_wishes", ["buyer_id"])
    op.create_index("ix_order_wishes_status", "order_wishes", ["status"])

    op.create_table(
        "search_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("query", sa.String(length=256), nullable=False),
        sa.Column("scope", sa.String(length=16), nullable=False, server_default="feed"),
        sa.Column("results_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_search_history_user_id", "search_history", ["user_id"])


def downgrade() -> None:
    op.drop_table("search_history")
    op.drop_table("order_wishes")
    op.drop_table("user_memory")
