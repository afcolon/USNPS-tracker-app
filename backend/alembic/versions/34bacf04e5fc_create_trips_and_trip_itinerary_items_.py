"""create trips and trip_itinerary_items tables

Revision ID: 34bacf04e5fc
Revises: 0ad540eec44f
Create Date: 2026-10-19 20:49:13.830300

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "34bacf04e5fc"
down_revision: str | Sequence[str] | None = "0ad540eec44f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trips",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("park_id", sa.Integer(), sa.ForeignKey("parks.id"), nullable=False),
        sa.Column("num_days", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "trip_itinerary_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id"), nullable=False),
        sa.Column("hike_id", sa.Integer(), sa.ForeignKey("hikes.id"), nullable=False),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("order_in_day", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("trip_itinerary_items")
    op.drop_table("trips")
