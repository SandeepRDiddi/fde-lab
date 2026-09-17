"""create conversations and messages

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
    message_role = sa.Enum("student", "persona", name="message_role")

    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scenario_instance_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scenario_instance_id", "student_id", name="uq_conversation_scenario_student"),
    )
    op.create_index("ix_conversations_scenario_instance_id", "conversations", ["scenario_instance_id"])
    op.create_index("ix_conversations_student_id", "conversations", ["student_id"])

    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("role", message_role, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])


def downgrade() -> None:
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")
    sa.Enum(name="message_role").drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_conversations_student_id", table_name="conversations")
    op.drop_index("ix_conversations_scenario_instance_id", table_name="conversations")
    op.drop_table("conversations")
