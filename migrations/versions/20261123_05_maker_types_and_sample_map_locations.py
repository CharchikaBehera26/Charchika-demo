"""Add maker types and approximate sample-map locations.

Revision ID: 20261123_05
Revises: 20261122_04
Create Date: 2026-11-23
"""
from alembic import op
import sqlalchemy as sa


revision = "20261123_05"
down_revision = "20261122_04"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("artisans") as batch_op:
        batch_op.add_column(
            sa.Column(
                "maker_type",
                sa.String(length=40),
                nullable=False,
                server_default="Artisan",
            )
        )
        batch_op.add_column(
            sa.Column(
                "approximate_location",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


def downgrade():
    with op.batch_alter_table("artisans") as batch_op:
        batch_op.drop_column("approximate_location")
        batch_op.drop_column("maker_type")
