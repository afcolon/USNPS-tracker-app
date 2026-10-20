"""add max_difficulty and max_hours_per_day to trips

Revision ID: 8c1f2e9a4b3d
Revises: 34bacf04e5fc
Create Date: 2026-10-20 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8c1f2e9a4b3d"
down_revision: str | Sequence[str] | None = "34bacf04e5fc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("trips", sa.Column("max_difficulty", sa.String(), nullable=True))
    op.add_column(
        "trips",
        sa.Column("max_hours_per_day", sa.Float(), nullable=False, server_default=sa.text("8.0")),
    )
    op.alter_column("trips", "max_hours_per_day", server_default=None)


def downgrade() -> None:
    op.drop_column("trips", "max_hours_per_day")
    op.drop_column("trips", "max_difficulty")
