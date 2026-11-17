"""add city services and expansion demand

Revision ID: f6b2d8a90c31
Revises: e3a1c9f4b820
Create Date: 2026-11-17 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f6b2d8a90c31"
down_revision = "e3a1c9f4b820"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "service_area_services",
        sa.Column("service_area_id", sa.Integer(), nullable=False),
        sa.Column("service_type_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["service_area_id"], ["service_areas.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["service_type_id"], ["service_types.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("service_area_id", "service_type_id"),
    )
    # Preserve current behaviour by enabling every existing service in every
    # existing area. Admins can narrow each catalogue after deployment.
    op.execute(
        sa.text(
            "INSERT INTO service_area_services (service_area_id, service_type_id) "
            "SELECT service_areas.id, service_types.id "
            "FROM service_areas CROSS JOIN service_types"
        )
    )
    op.create_table(
        "service_demands",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("service_type_id", sa.Integer(), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("state", sa.String(length=100), nullable=False),
        sa.Column("city_key", sa.String(length=100), nullable=False),
        sa.Column("state_key", sa.String(length=100), nullable=False),
        sa.Column("request_count", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "last_requested_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["service_type_id"], ["service_types.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "service_type_id",
            "city_key",
            "state_key",
            name="uq_service_demand_user_service_location",
        ),
    )


def downgrade():
    op.drop_table("service_demands")
    op.drop_table("service_area_services")
