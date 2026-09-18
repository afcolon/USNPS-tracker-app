"""create hikes and hike_highlights tables

Revision ID: 5f62f923cfa5
Revises: 06a470adfd35
Create Date: 2026-09-18 16:16:55.279004

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5f62f923cfa5"
down_revision: str | Sequence[str] | None = "06a470adfd35"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "hikes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("park_id", sa.Integer(), sa.ForeignKey("parks.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("distance_miles", sa.Float(), nullable=False),
        sa.Column("elevation_gain_ft", sa.Float(), nullable=False),
        sa.Column("difficulty", sa.String(), nullable=False),
        sa.Column("difficulty_score", sa.Float(), nullable=False),
        sa.Column("difficulty_override", sa.String(), nullable=True),
        sa.Column("difficulty_override_reason", sa.Text(), nullable=True),
        sa.Column("hike_type", sa.String(), nullable=False),
        sa.Column("trailhead_lat", sa.Float(), nullable=False),
        sa.Column("trailhead_lng", sa.Float(), nullable=False),
        sa.Column("estimated_duration_min", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=True),
        sa.UniqueConstraint("source", "source_id", name="uq_hikes_source_source_id"),
    )

    op.create_table(
        "hike_highlights",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hike_id", sa.Integer(), sa.ForeignKey("hikes.id"), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("hike_highlights")
    op.drop_table("hikes")
