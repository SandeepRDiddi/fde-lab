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
    # A single plain sa.Enum, reused by identity across every column below.
    # (An earlier version of this migration also called .create() explicitly
    # up front and passed create_type=False on the columns to try to avoid a
    # double CREATE TYPE -- that flag doesn't actually suppress create_table's
    # own before_create attempt, so it hit "type already exists" and rolled
    # back the whole migration. create_table's automatic checkfirst-based
    # creation on first use, with no separate pre-create, is what actually
    # works -- same pattern as scenario_status in 0001.)
    approval_status = sa.Enum(
        "submitted", "pending_review", "approved", "rejected", name="approval_status"
    )

    op.create_table(
        "submissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scenario_instance_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("status", approval_status, nullable=False, server_default=sa.text("'submitted'")),
        sa.Column("review_deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("auto_decision", approval_status, nullable=True),
        sa.Column("auto_decide_task_id", sa.String(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["scenario_instance_id"], ["scenario_instances.id"]),
    )
    op.create_index("ix_submissions_scenario_instance_id", "submissions", ["scenario_instance_id"])

    op.add_column("scenario_instances", sa.Column("approval_outcome", approval_status, nullable=True))
    op.add_column(
        "scenario_instances", sa.Column("approval_decided_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("scenario_instances", "approval_decided_at")
    op.drop_column("scenario_instances", "approval_outcome")
    op.drop_index("ix_submissions_scenario_instance_id", table_name="submissions")
    op.drop_table("submissions")
    sa.Enum(name="approval_status").drop(op.get_bind(), checkfirst=True)
