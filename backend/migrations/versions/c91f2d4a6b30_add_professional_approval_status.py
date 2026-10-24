"""add professional approval status

Revision ID: c91f2d4a6b30
Revises: a2a675245ae8
Create Date: 2026-10-25

"""
from alembic import op
import sqlalchemy as sa


revision = "c91f2d4a6b30"
down_revision = "a2a675245ae8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "professionals",
        sa.Column(
            "approval_status",
            sa.String(length=20),
            nullable=True,
            server_default="pending",
        ),
    )
    op.add_column(
        "professionals",
        sa.Column("block_reason", sa.Text(), nullable=True),
    )

    # Preserve the meaning of existing approved professional accounts.
    op.execute(
        "UPDATE professionals SET approval_status = "
        "CASE WHEN is_approved = true THEN 'approved' ELSE 'pending' END"
    )
    op.alter_column(
        "professionals",
        "approval_status",
        existing_type=sa.String(length=20),
        nullable=False,
        server_default=None,
    )
    op.drop_column("professionals", "is_approved")


def downgrade():
    op.add_column(
        "professionals",
        sa.Column(
            "is_approved",
            sa.Boolean(),
            nullable=True,
            server_default=sa.false(),
        ),
    )
    op.execute(
        "UPDATE professionals SET is_approved = "
        "CASE WHEN approval_status = 'approved' THEN true ELSE false END"
    )
    op.alter_column(
        "professionals",
        "is_approved",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=None,
    )
    op.drop_column("professionals", "block_reason")
    op.drop_column("professionals", "approval_status")
