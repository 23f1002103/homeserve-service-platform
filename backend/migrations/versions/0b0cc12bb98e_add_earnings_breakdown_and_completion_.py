"""add earnings breakdown and completion time

Revision ID: 0b0cc12bb98e
Revises: 13bf54b7c378
Create Date: 2026-10-25 04:10:37.308040

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0b0cc12bb98e'
down_revision = '13bf54b7c378'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('commission_rate', sa.Numeric(precision=5, scale=2), nullable=True))
        batch_op.add_column(sa.Column('platform_fee', sa.Numeric(precision=10, scale=2), nullable=True))
        batch_op.add_column(sa.Column('professional_earning', sa.Numeric(precision=10, scale=2), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE payments
            SET commission_rate = 15.00,
                platform_fee = ROUND(amount * 0.15, 2),
                professional_earning = amount - ROUND(amount * 0.15, 2)
            """
        )
    )

    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.alter_column('commission_rate', nullable=False)
        batch_op.alter_column('platform_fee', nullable=False)
        batch_op.alter_column('professional_earning', nullable=False)

    with op.batch_alter_table('service_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('completed_at', sa.DateTime(), nullable=True))

    op.execute(
        sa.text(
            """
            UPDATE service_requests
            SET completed_at = updated_at
            WHERE status = 'completed' AND completed_at IS NULL
            """
        )
    )


def downgrade():
    with op.batch_alter_table('service_requests', schema=None) as batch_op:
        batch_op.drop_column('completed_at')

    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.drop_column('professional_earning')
        batch_op.drop_column('platform_fee')
        batch_op.drop_column('commission_rate')

