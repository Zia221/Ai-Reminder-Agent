"""repair missing reminders table

Revision ID: f7f95d2e706d
Revises: 7c8ff4c45cac
"""

from alembic import op
import sqlalchemy as sa


revision = "f7f95d2e706d"
down_revision = "7c8ff4c45cac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if sa.inspect(op.get_bind()).has_table('reminders'):
        return
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
        sa.Column(
            "timezone",
            sa.String(length=64),
            nullable=False,
            server_default="UTC",
        ),
        sa.Column(
            "priority",
            sa.String(length=16),
            nullable=False,
            server_default="medium",
        ),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "recurrence",
            sa.String(length=16),
            nullable=False,
            server_default="none",
        ),
        sa.Column("natural_language_input", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
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
    op.create_index(
        "ix_reminders_user_due_at",
        "reminders",
        ["user_id", "due_at"],
    )


def downgrade() -> None:
    # This repair revision is intentionally non-destructive. Its upgrade may have
    # been a no-op when the table already existed, so dropping it here could
    # remove data that predates this revision.
    pass
