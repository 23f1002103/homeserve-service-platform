"""add Google identity to users

Revision ID: 7bd51a2f09c4
Revises: 2f4c7a1d9e10
"""
from alembic import op
import sqlalchemy as sa


revision = "7bd51a2f09c4"
down_revision = "2f4c7a1d9e10"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("google_subject", sa.String(length=255), nullable=True),
    )
    op.create_unique_constraint(
        "uq_users_google_subject",
        "users",
        ["google_subject"],
    )


def downgrade():
    op.drop_constraint(
        "uq_users_google_subject",
        "users",
        type_="unique",
    )
    op.drop_column("users", "google_subject")
