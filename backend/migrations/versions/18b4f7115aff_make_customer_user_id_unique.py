"""make customer user id unique

Revision ID: 18b4f7115aff
Revises: d44002b338ea
Create Date: 2026-10-20 03:04:16.889166

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '18b4f7115aff'
down_revision = 'd44002b338ea'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("customers", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_customers_user_id",
            ["user_id"],
        )


def downgrade():
    with op.batch_alter_table("customers", schema=None) as batch_op:
        batch_op.drop_constraint(
            "uq_customers_user_id",
            type_="unique",
        )