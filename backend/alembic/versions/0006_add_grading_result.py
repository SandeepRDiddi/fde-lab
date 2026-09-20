"""add grading_result to submissions

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-20

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "submissions",
        sa.Column("grading_result", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("submissions", "grading_result")
