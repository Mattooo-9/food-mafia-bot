"""User locale, timezone, onboarding; feed indexes

Revision ID: 0004
Revises: 0003
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return column in {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    if not _has_column("users", "language_code"):
        op.add_column("users", sa.Column("language_code", sa.String(length=16), nullable=True))
    if not _has_column("users", "locale"):
        op.add_column(
            "users",
            sa.Column("locale", sa.String(length=8), nullable=False, server_default="ru"),
        )
    if not _has_column("users", "timezone"):
        op.add_column("users", sa.Column("timezone", sa.String(length=64), nullable=True))
    if not _has_column("users", "onboarding_done"):
        op.add_column(
            "users",
            sa.Column("onboarding_done", sa.Boolean(), nullable=False, server_default=sa.false()),
        )

    try:
        op.create_index("ix_foods_active_portions", "foods", ["is_active", "portions"])
    except Exception:
        pass
    try:
        op.create_index("ix_users_cook_online", "users", ["is_cook", "is_online"])
    except Exception:
        pass
    try:
        op.create_index("ix_orders_created", "orders", ["created_at"])
    except Exception:
        pass


def downgrade() -> None:
    pass
