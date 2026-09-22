"""create engagements + link scenario_instances (FDE-017)

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-22

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "engagements",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("cohort_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("student_id", sa.Uuid(), nullable=False, index=True),
        sa.Column(
            "status",
            sa.Enum("active", "completed", name="engagement_status"),
            nullable=False,
        ),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "scenario_instances",
        sa.Column("engagement_id", sa.Uuid(), sa.ForeignKey("engagements.id"), nullable=True),
    )
    op.create_index(
        "ix_scenario_instances_engagement_id", "scenario_instances", ["engagement_id"]
    )
    op.add_column(
        "scenario_instances",
        sa.Column("stage_order", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("scenario_instances", "stage_order")
    op.drop_index("ix_scenario_instances_engagement_id", table_name="scenario_instances")
    op.drop_column("scenario_instances", "engagement_id")
    op.drop_table("engagements")
    sa.Enum(name="engagement_status").drop(op.get_bind(), checkfirst=True)
