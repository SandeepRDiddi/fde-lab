"""create submissions and approval outcome fields

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-18

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Created once up front and reused with create_type=False on every
    # column below — letting each column's own DDL try to create the type
    # (the sa.Enum default) would attempt CREATE TYPE approval_status twice
    # over for the second/third usage.
    approval_status = sa.Enum(
        "submitted", "pending_review", "approved", "rejected", name="approval_status"
    )
    approval_status.create(op.get_bind(), checkfirst=True)
    approval_status_col = sa.Enum(
        "submitted", "pending_review", "approved", "rejected", name="approval_status", create_type=False
    )

    op.create_table(
        "submissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scenario_instance_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("status", approval_status_col, nullable=False, server_default=sa.text("'submitted'")),
        sa.Column("review_deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("auto_decision", approval_status_col, nullable=True),
        sa.Column("auto_decide_task_id", sa.String(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["scenario_instance_id"], ["scenario_instances.id"]),
    )
    op.create_index("ix_submissions_scenario_instance_id", "submissions", ["scenario_instance_id"])

    op.add_column("scenario_instances", sa.Column("approval_outcome", approval_status_col, nullable=True))
    op.add_column(
        "scenario_instances", sa.Column("approval_decided_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("scenario_instances", "approval_decided_at")
    op.drop_column("scenario_instances", "approval_outcome")
    op.drop_index("ix_submissions_scenario_instance_id", table_name="submissions")
    op.drop_table("submissions")
    sa.Enum(name="approval_status").drop(op.get_bind(), checkfirst=True)
