"""add review prompt timestamp

Revision ID: 6c42f9a8d1e3
Revises: a91d72c438b1
Create Date: 2026-10-26 00:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "6c42f9a8d1e3"
down_revision = "a91d72c438b1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("service_requests", schema=None) as batch_op:
        batch_op.add_column(sa.Column("review_prompted_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("service_requests", schema=None) as batch_op:
        batch_op.drop_column("review_prompted_at")
