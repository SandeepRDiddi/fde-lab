"""track celery task ids for reschedule cancellation

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-17

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scenario_instances", sa.Column("unlock_task_id", sa.String(), nullable=True))
    op.add_column("scenario_instances", sa.Column("close_task_id", sa.String(), nullable=True))
    op.add_column("scenario_instances", sa.Column("pivot_task_id", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("scenario_instances", "pivot_task_id")
    op.drop_column("scenario_instances", "close_task_id")
    op.drop_column("scenario_instances", "unlock_task_id")
