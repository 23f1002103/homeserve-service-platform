"""add service area availability and remove legacy links

Revision ID: d7f31a0e4b62
Revises: c4e2f8a91d07
Create Date: 2026-10-27 12:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "d7f31a0e4b62"
down_revision = "c4e2f8a91d07"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("service_areas", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_active",
                sa.Boolean(),
                server_default=sa.true(),
                nullable=False,
            )
        )

    # This many-to-many table belonged to the pre-GPS workflow. The current
    # application uses professionals.active_service_area_id instead.
    op.drop_table("professional_service_areas")


def downgrade():
    op.create_table(
        "professional_service_areas",
        sa.Column("professional_id", sa.Integer(), nullable=False),
        sa.Column("service_area_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["professional_id"], ["professionals.id"]),
        sa.ForeignKeyConstraint(["service_area_id"], ["service_areas.id"]),
        sa.PrimaryKeyConstraint("professional_id", "service_area_id"),
    )
    with op.batch_alter_table("service_areas", schema=None) as batch_op:
        batch_op.drop_column("is_active")
