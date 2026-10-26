"""use one GPS-verified active service area per professional

Revision ID: 9d3b70c2e411
Revises: 6c42f9a8d1e3
Create Date: 2026-10-26 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "9d3b70c2e411"
down_revision = "6c42f9a8d1e3"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("professionals", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("active_service_area_id", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("location_verified_at", sa.DateTime(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_professionals_active_service_area_id",
            "service_areas",
            ["active_service_area_id"],
            ["id"],
        )

def downgrade():
    with op.batch_alter_table("professionals", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_professionals_active_service_area_id", type_="foreignkey"
        )
        batch_op.drop_column("location_verified_at")
        batch_op.drop_column("active_service_area_id")
