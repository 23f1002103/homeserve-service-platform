"""add parent package orders

Revision ID: b7d3e4f1a820
Revises: 8f2a1c6d9e40
Create Date: 2026-11-16 22:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b7d3e4f1a820"
down_revision = "8f2a1c6d9e40"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "package_orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("service_package_id", sa.Integer(), nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "status",
            sa.String(length=30),
            server_default="payment_pending",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["service_package_id"], ["service_packages.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("service_requests", schema=None) as batch_op:
        batch_op.add_column(sa.Column("package_order_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_service_requests_package_order_id",
            "package_orders",
            ["package_order_id"],
            ["id"],
        )
        batch_op.drop_index("ix_service_requests_package_group_id")
        batch_op.drop_column("package_group_id")


def downgrade():
    with op.batch_alter_table("service_requests", schema=None) as batch_op:
        batch_op.add_column(sa.Column("package_group_id", sa.String(length=36), nullable=True))
        batch_op.create_index("ix_service_requests_package_group_id", ["package_group_id"])
        batch_op.drop_constraint(
            "fk_service_requests_package_order_id",
            type_="foreignkey",
        )
        batch_op.drop_column("package_order_id")
    op.drop_table("package_orders")
