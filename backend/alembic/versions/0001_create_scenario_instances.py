"""create scenario_instances

Revision ID: 0001
Revises:
Create Date: 2026-09-17

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    scenario_status = sa.Enum("not_started", "active", "closed", name="scenario_status")
    scenario_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "scenario_instances",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("cohort_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("status", scenario_status, nullable=False, server_default=sa.text("'not_started'")),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scenario_instances_cohort_id", "scenario_instances", ["cohort_id"])
    op.create_index("ix_scenario_instances_student_id", "scenario_instances", ["student_id"])


def downgrade() -> None:
    op.drop_index("ix_scenario_instances_student_id", table_name="scenario_instances")
    op.drop_index("ix_scenario_instances_cohort_id", table_name="scenario_instances")
    op.drop_table("scenario_instances")
    sa.Enum(name="scenario_status").drop(op.get_bind(), checkfirst=True)
