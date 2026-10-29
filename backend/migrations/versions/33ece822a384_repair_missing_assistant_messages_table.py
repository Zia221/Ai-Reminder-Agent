"""repair missing assistant messages table

Revision ID: 33ece822a384
Revises: f7f95d2e706d
"""

from alembic import op
import sqlalchemy as sa


revision = "33ece822a384"
down_revision = "f7f95d2e706d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if sa.inspect(op.get_bind()).has_table('assistant_messages'):
        return
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
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
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


def downgrade() -> None:
    # This repair revision is intentionally non-destructive. Its upgrade may have
    # been a no-op when the table already existed, so dropping it here could
    # remove data that predates this revision.
    pass
