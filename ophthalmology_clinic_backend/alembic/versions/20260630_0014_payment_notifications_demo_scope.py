"""Add demo scoping to payment settings and notifications.

Revision ID: 20260630_0014
Revises: 20260630_0013
Create Date: 2026-06-30 00:14:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260630_0014"
down_revision = "20260630_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("payment_settings", sa.Column("is_demo_data", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("notifications", sa.Column("is_demo_data", sa.Boolean(), nullable=False, server_default=sa.false()))

    op.execute(
        """
        UPDATE payment_settings
        SET is_demo_data = true
        WHERE EXISTS (SELECT 1 FROM users WHERE is_demo_account = true)
          AND NOT EXISTS (
              SELECT 1
              FROM users
              WHERE role = 'DOCTOR'
                AND is_demo_account = false
          )
        """
    )
    op.execute(
        """
        UPDATE notifications
        SET is_demo_data = true
        WHERE EXISTS (SELECT 1 FROM users WHERE is_demo_account = true)
          AND NOT EXISTS (
              SELECT 1
              FROM users
              WHERE role = 'DOCTOR'
                AND is_demo_account = false
          )
        """
    )

    op.alter_column("payment_settings", "is_demo_data", server_default=None)
    op.alter_column("notifications", "is_demo_data", server_default=None)

    op.drop_index(op.f("ix_payment_settings_setting_key"), table_name="payment_settings")
    op.create_index(op.f("ix_payment_settings_setting_key"), "payment_settings", ["setting_key"], unique=False)
    op.create_unique_constraint("uq_payment_settings_key_demo", "payment_settings", ["setting_key", "is_demo_data"])


def downgrade() -> None:
    op.drop_constraint("uq_payment_settings_key_demo", "payment_settings", type_="unique")
    op.drop_index(op.f("ix_payment_settings_setting_key"), table_name="payment_settings")

    op.execute(
        """
        DELETE FROM payment_settings AS demo_setting
        USING payment_settings AS real_setting
        WHERE demo_setting.setting_key = real_setting.setting_key
          AND demo_setting.is_demo_data = true
          AND real_setting.is_demo_data = false
        """
    )
    op.execute("UPDATE payment_settings SET is_demo_data = false")

    op.create_index(op.f("ix_payment_settings_setting_key"), "payment_settings", ["setting_key"], unique=True)

    op.drop_column("notifications", "is_demo_data")
    op.drop_column("payment_settings", "is_demo_data")
