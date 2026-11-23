"""Add name_local (bilingual Odia name) to products table.

Revision ID: 20261123_06
Revises: 20261123_05
Create Date: 2026-11-23
"""
from alembic import op
import sqlalchemy as sa


revision = "20261123_06"
down_revision = "20261123_05"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("products") as batch_op:
        batch_op.add_column(
            sa.Column(
                "name_local",
                sa.String(300),
                nullable=False,
                server_default="",
            )
        )


def downgrade():
    with op.batch_alter_table("products") as batch_op:
        batch_op.drop_column("name_local")
