"""Wellness: activity level + daily nutrition state

Revision ID: 0005
Revises: 0004
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return column in {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    if not _has_column("users", "activity_level"):
        op.add_column(
            "users",
            sa.Column("activity_level", sa.String(length=16), nullable=False, server_default="moderate"),
        )
    if not _has_column("user_memory", "wellness_state"):
        op.add_column(
            "user_memory",
            sa.Column("wellness_state", sa.Text(), nullable=False, server_default="{}"),
        )


def downgrade() -> None:
    pass
