"""Add product categories and marketplace promotions.

Revision ID: 20261122_03
Revises: 20261122_02
Create Date: 2026-11-22
"""
from alembic import op
import sqlalchemy as sa


revision = "20261122_03"
down_revision = "20261122_02"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("products") as batch_op:
        batch_op.add_column(
            sa.Column("category", sa.String(length=160), nullable=False, server_default="")
        )
        batch_op.add_column(
            sa.Column("deal_price", sa.String(length=80), nullable=False, server_default="")
        )
        batch_op.add_column(
            sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.false())
        )


def downgrade():
    with op.batch_alter_table("products") as batch_op:
        batch_op.drop_column("is_featured")
        batch_op.drop_column("deal_price")
        batch_op.drop_column("category")
