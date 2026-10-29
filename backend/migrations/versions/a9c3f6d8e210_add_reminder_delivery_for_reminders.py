"""Support delivery tracking for both tasks and reminders.

Revision ID: a9c3f6d8e210
Revises: 8ef70a9b1869
"""
from alembic import op
import sqlalchemy as sa


revision = "a9c3f6d8e210"
down_revision = "8ef70a9b1869"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Older revisions in this project's history dropped these tables during
    # autogeneration. Restore their schema if that already happened locally.
    if not inspector.has_table("reminders"):
        op.create_table(
            "reminders",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
            sa.Column("priority", sa.String(length=16), nullable=False, server_default="medium"),
            sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
            sa.Column("recurrence", sa.String(length=16), nullable=False, server_default="none"),
            sa.Column("natural_language_input", sa.Text(), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint(
                "priority IN ('low', 'medium', 'high', 'urgent')",
                name="ck_reminders_priority",
            ),
            sa.CheckConstraint(
                "status IN ('pending', 'completed', 'paused', 'cancelled')",
                name="ck_reminders_status",
            ),
            sa.CheckConstraint(
                "recurrence IN ('none', 'daily', 'weekly', 'monthly')",
                name="ck_reminders_recurrence",
            ),
        )
        op.create_index("ix_reminders_id", "reminders", ["id"])
        op.create_index("ix_reminders_user_id", "reminders", ["user_id"])
        op.create_index("ix_reminders_user_due_at", "reminders", ["user_id", "due_at"])

    if not inspector.has_table("assistant_messages"):
        op.create_table(
            "assistant_messages",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("role", sa.String(length=20), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.CheckConstraint(
                "role IN ('user', 'assistant')",
                name="ck_assistant_messages_role",
            ),
        )
        op.create_index(
            "ix_assistant_messages_user_id",
            "assistant_messages",
            ["user_id"],
        )

    op.alter_column(
        "reminder_deliveries",
        "task_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.alter_column(
        "reminder_deliveries",
        "task_due_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )
    op.add_column(
        "reminder_deliveries",
        sa.Column("reminder_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "reminder_deliveries",
        sa.Column("reminder_due_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "reminder_deliveries",
        sa.Column("item_title", sa.String(length=200), nullable=True),
    )
    op.create_foreign_key(
        "fk_reminder_deliveries_reminder_id_reminders",
        "reminder_deliveries",
        "reminders",
        ["reminder_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_reminder_deliveries_reminder_id",
        "reminder_deliveries",
        ["reminder_id"],
    )
    op.create_unique_constraint(
        "uq_reminder_delivery_reminder_due",
        "reminder_deliveries",
        ["reminder_id", "reminder_due_at"],
    )
    op.create_check_constraint(
        "ck_reminder_delivery_one_source",
        "reminder_deliveries",
        "(task_id IS NOT NULL AND reminder_id IS NULL "
        "AND task_due_at IS NOT NULL AND reminder_due_at IS NULL) OR "
        "(task_id IS NULL AND reminder_id IS NOT NULL "
        "AND task_due_at IS NULL AND reminder_due_at IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_reminder_delivery_status",
        "reminder_deliveries",
        "status IN ('pending', 'sending', 'sent', 'failed', 'cancelled')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_reminder_delivery_status",
        "reminder_deliveries",
        type_="check",
    )
    op.drop_constraint(
        "ck_reminder_delivery_one_source",
        "reminder_deliveries",
        type_="check",
    )
    op.drop_constraint(
        "uq_reminder_delivery_reminder_due",
        "reminder_deliveries",
        type_="unique",
    )
    op.drop_index(
        "ix_reminder_deliveries_reminder_id",
        table_name="reminder_deliveries",
    )
    op.drop_constraint(
        "fk_reminder_deliveries_reminder_id_reminders",
        "reminder_deliveries",
        type_="foreignkey",
    )
    op.drop_column("reminder_deliveries", "item_title")
    op.drop_column("reminder_deliveries", "reminder_due_at")
    op.drop_column("reminder_deliveries", "reminder_id")
    op.alter_column(
        "reminder_deliveries",
        "task_id",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "reminder_deliveries",
        "task_due_at",
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
