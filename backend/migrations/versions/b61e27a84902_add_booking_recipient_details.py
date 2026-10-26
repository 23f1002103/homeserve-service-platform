"""add booking recipient details

Revision ID: b61e27a84902
Revises: 9d3b70c2e411
Create Date: 2026-10-26 08:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b61e27a84902"
down_revision = "9d3b70c2e411"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("service_requests", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "booking_for",
                sa.String(length=20),
                server_default="self",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column("recipient_name", sa.String(length=100), nullable=True)
        )
        batch_op.add_column(
            sa.Column("recipient_phone", sa.String(length=20), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("service_requests", schema=None) as batch_op:
        batch_op.drop_column("recipient_phone")
        batch_op.drop_column("recipient_name")
        batch_op.drop_column("booking_for")
