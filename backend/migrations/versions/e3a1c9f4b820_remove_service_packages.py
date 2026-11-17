"""remove service packages

Revision ID: e3a1c9f4b820
Revises: d4f7a2c91b60
Create Date: 2026-11-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "e3a1c9f4b820"
down_revision = "d4f7a2c91b60"
branch_labels = None
depends_on = None


def upgrade():
    # Package child jobs remain as ordinary service requests, preserving their
    # customer, professional, payment, and completion history.
    with op.batch_alter_table("service_requests", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_service_requests_package_order_id",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_service_requests_service_package_id",
            type_="foreignkey",
        )
        batch_op.drop_column("package_order_id")
        batch_op.drop_column("service_package_id")

    op.drop_table("package_orders")
    op.drop_table("service_package_services")
    op.drop_table("service_packages")


def downgrade():
    op.create_table(
        "service_packages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("regular_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("package_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
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
    op.create_table(
        "package_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("service_package_id", sa.Integer(), nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["service_package_id"], ["service_packages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("service_requests", schema=None) as batch_op:
        batch_op.add_column(sa.Column("service_package_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("package_order_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_service_requests_service_package_id",
            "service_packages",
            ["service_package_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_service_requests_package_order_id",
            "package_orders",
            ["package_order_id"],
            ["id"],
        )
