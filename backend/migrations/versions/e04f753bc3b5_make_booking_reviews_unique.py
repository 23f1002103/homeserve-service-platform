"""make booking reviews unique

Revision ID: e04f753bc3b5
Revises: 7591c8c86969
Create Date: 2026-10-25 03:51:51.488877

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e04f753bc3b5'
down_revision = '7591c8c86969'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('reviews', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            'uq_reviews_service_request_id',
            ['service_request_id'],
        )


def downgrade():
    with op.batch_alter_table('reviews', schema=None) as batch_op:
        batch_op.drop_constraint(
            'uq_reviews_service_request_id',
            type_='unique',
        )
