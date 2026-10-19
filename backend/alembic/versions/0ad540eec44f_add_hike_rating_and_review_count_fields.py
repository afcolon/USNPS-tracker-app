"""add hike rating and review count fields

Revision ID: 0ad540eec44f
Revises: 5f62f923cfa5
Create Date: 2026-10-19 19:50:12.383540

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0ad540eec44f"
down_revision: str | Sequence[str] | None = "5f62f923cfa5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("hikes", sa.Column("avg_rating", sa.Float(), nullable=True))
    op.add_column("hikes", sa.Column("reviews_count", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("hikes", "reviews_count")
    op.drop_column("hikes", "avg_rating")
