"""add scheduling fields to scenario_instances

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-17

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scenario_instances", sa.Column("pivot_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("scenario_instances", sa.Column("pivot_config", sa.JSON(), nullable=True))
    op.add_column(
        "scenario_instances", sa.Column("pivot_applied_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("scenario_instances", sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("scenario_instances", "notified_at")
    op.drop_column("scenario_instances", "pivot_applied_at")
    op.drop_column("scenario_instances", "pivot_config")
    op.drop_column("scenario_instances", "pivot_at")
