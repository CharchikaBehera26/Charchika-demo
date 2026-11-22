"""Add Supabase identities to artisan accounts.

Revision ID: 20261122_04
Revises: 20261122_03
Create Date: 2026-11-22
"""
from alembic import op
import sqlalchemy as sa


revision = "20261122_04"
down_revision = "20261122_03"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("artisan_accounts") as batch_op:
        batch_op.alter_column(
            "password_hash",
            existing_type=sa.String(length=255),
            nullable=True,
        )
        batch_op.add_column(sa.Column("supabase_user_id", sa.String(length=64)))
        batch_op.create_index(
            "ix_artisan_accounts_supabase_user_id",
            ["supabase_user_id"],
            unique=True,
        )


def downgrade():
    with op.batch_alter_table("artisan_accounts") as batch_op:
        batch_op.drop_index("ix_artisan_accounts_supabase_user_id")
        batch_op.drop_column("supabase_user_id")
        batch_op.alter_column(
            "password_hash",
            existing_type=sa.String(length=255),
            nullable=False,
        )
