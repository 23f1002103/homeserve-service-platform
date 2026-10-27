"""add service area geo zones

Revision ID: c4e2f8a91d07
Revises: b61e27a84902
Create Date: 2026-10-27 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "c4e2f8a91d07"
down_revision = "b61e27a84902"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("service_areas", schema=None) as batch_op:
        batch_op.add_column(sa.Column("center_latitude", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("center_longitude", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("radius_km", sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table("service_areas", schema=None) as batch_op:
        batch_op.drop_column("radius_km")
        batch_op.drop_column("center_longitude")
        batch_op.drop_column("center_latitude")
