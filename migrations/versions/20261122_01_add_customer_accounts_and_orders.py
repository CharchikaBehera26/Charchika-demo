"""Add customer accounts and marketplace orders.

Revision ID: 20261122_01
Revises: 4267cc26d40e
Create Date: 2026-11-22
"""
from alembic import op
import sqlalchemy as sa


revision = "20261122_01"
down_revision = "4267cc26d40e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "customer_accounts",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_customer_accounts_email",
        "customer_accounts",
        ["email"],
        unique=True,
    )
    op.create_table(
        "customer_orders",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("customer_name", sa.String(length=160), nullable=False),
        sa.Column("phone", sa.String(length=40), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("items_json", sa.Text(), nullable=False),
        sa.Column("total_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_customer_orders_customer_id",
        "customer_orders",
        ["customer_id"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_customer_orders_customer_id", table_name="customer_orders")
    op.drop_table("customer_orders")
    op.drop_index("ix_customer_accounts_email", table_name="customer_accounts")
    op.drop_table("customer_accounts")
