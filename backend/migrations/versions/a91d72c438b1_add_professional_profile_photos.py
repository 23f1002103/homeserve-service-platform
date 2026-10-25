"""add professional profile photos

Revision ID: a91d72c438b1
Revises: 7bd51a2f09c4
Create Date: 2026-10-25 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "a91d72c438b1"
down_revision = "7bd51a2f09c4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "professional_photos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("professional_id", sa.Integer(), nullable=False),
        sa.Column("image_data", sa.LargeBinary(), nullable=False),
        sa.Column("mime_type", sa.String(length=50), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["professional_id"],
            ["professionals.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("professional_id"),
    )


def downgrade():
    op.drop_table("professional_photos")
