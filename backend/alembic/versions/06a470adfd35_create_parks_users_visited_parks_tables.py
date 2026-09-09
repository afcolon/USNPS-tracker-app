"""create parks, users, visited_parks tables

Revision ID: 06a470adfd35
Revises:
Create Date: 2026-09-09 16:40:38.038373

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "06a470adfd35"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "parks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nps_park_code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("states", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
    )
    op.create_index("ix_parks_nps_park_code", "parks", ["nps_park_code"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False, unique=True),
    )

    op.create_table(
        "visited_parks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("park_id", sa.Integer(), sa.ForeignKey("parks.id"), nullable=False),
        sa.Column("visited_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("user_id", "park_id", name="uq_visited_parks_user_park"),
    )

    # Single implicit user for this solo/personal-use app (see docs/phase1-notes.md).
    # Deliberately a placeholder, not a real identity, so it's safe to commit.
    op.execute("INSERT INTO users (name, email) VALUES ('Park Explorer', 'owner@example.com')")


def downgrade() -> None:
    op.drop_table("visited_parks")
    op.drop_table("users")
    op.drop_index("ix_parks_nps_park_code", table_name="parks")
    op.drop_table("parks")
