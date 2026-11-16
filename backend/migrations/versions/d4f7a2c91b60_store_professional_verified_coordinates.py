"""store professional verified coordinates

Revision ID: d4f7a2c91b60
Revises: c2e8a4d7f930
Create Date: 2026-11-16 23:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "d4f7a2c91b60"
down_revision = "c2e8a4d7f930"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("professionals") as batch_op:
        batch_op.add_column(sa.Column("current_latitude", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("current_longitude", sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table("professionals") as batch_op:
        batch_op.drop_column("current_longitude")
        batch_op.drop_column("current_latitude")
