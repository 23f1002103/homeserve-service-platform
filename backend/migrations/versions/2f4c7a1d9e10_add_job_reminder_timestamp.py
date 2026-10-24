"""add job reminder timestamp

Revision ID: 2f4c7a1d9e10
Revises: 0b0cc12bb98e
"""
from alembic import op
import sqlalchemy as sa


revision = "2f4c7a1d9e10"
down_revision = "0b0cc12bb98e"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "service_requests",
        sa.Column("reminder_sent_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_column("service_requests", "reminder_sent_at")
