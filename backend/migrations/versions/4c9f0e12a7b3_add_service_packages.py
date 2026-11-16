"""add service packages

Revision ID: 4c9f0e12a7b3
Revises: d7f31a0e4b62
Create Date: 2026-11-16 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "4c9f0e12a7b3"
down_revision = "d7f31a0e4b62"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "service_packages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_type_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("included_items", sa.JSON(), nullable=False),
        sa.Column("regular_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("package_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["service_type_id"], ["service_types.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    with op.batch_alter_table("service_requests", schema=None) as batch_op:
        batch_op.add_column(sa.Column("service_package_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_service_requests_service_package_id",
            "service_packages",
            ["service_package_id"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table("service_requests", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_service_requests_service_package_id",
            type_="foreignkey",
        )
        batch_op.drop_column("service_package_id")
    op.drop_table("service_packages")
