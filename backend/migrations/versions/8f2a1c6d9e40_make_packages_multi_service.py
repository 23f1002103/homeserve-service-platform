"""make packages combine multiple service types

Revision ID: 8f2a1c6d9e40
Revises: 4c9f0e12a7b3
Create Date: 2026-11-16 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "8f2a1c6d9e40"
down_revision = "4c9f0e12a7b3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "service_package_services",
        sa.Column("service_package_id", sa.Integer(), nullable=False),
        sa.Column("service_type_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["service_package_id"], ["service_packages.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["service_type_id"], ["service_types.id"]),
        sa.PrimaryKeyConstraint("service_package_id", "service_type_id"),
    )
    op.execute(
        sa.text(
            "INSERT INTO service_package_services (service_package_id, service_type_id) "
            "SELECT id, service_type_id FROM service_packages"
        )
    )
    with op.batch_alter_table("service_packages", schema=None) as batch_op:
        batch_op.drop_column("included_items")
        batch_op.drop_column("service_type_id")
    with op.batch_alter_table("service_requests", schema=None) as batch_op:
        batch_op.add_column(sa.Column("package_group_id", sa.String(length=36), nullable=True))
        batch_op.create_index("ix_service_requests_package_group_id", ["package_group_id"])


def downgrade():
    with op.batch_alter_table("service_requests", schema=None) as batch_op:
        batch_op.drop_index("ix_service_requests_package_group_id")
        batch_op.drop_column("package_group_id")
    with op.batch_alter_table("service_packages", schema=None) as batch_op:
        batch_op.add_column(sa.Column("service_type_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("included_items", sa.JSON(), nullable=True))
    op.execute(
        sa.text(
            "UPDATE service_packages SET service_type_id = ("
            "SELECT MIN(service_type_id) FROM service_package_services "
            "WHERE service_package_id = service_packages.id)"
        )
    )
    op.drop_table("service_package_services")
