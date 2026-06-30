"""payments reports supplies

Revision ID: 20260629_0005
Revises: 20260628_0004
Create Date: 2026-06-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260629_0005"
down_revision: str | None = "20260628_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

payment_status = postgresql.ENUM("NOT_PAID", "PAID", name="payment_status", create_type=False)
payment_method = postgresql.ENUM("CASH", "UPI_QR", name="payment_method", create_type=False)
supply_category = postgresql.ENUM("EMERGENCY", "OPERATION", "GENERAL", name="supply_category", create_type=False)
notification_type = postgresql.ENUM("LOW_STOCK", name="notification_type", create_type=False)
all_enums = (payment_status, payment_method, supply_category, notification_type)


def upgrade() -> None:
    bind = op.get_bind()
    for enum_type in all_enums:
        enum_type.create(bind, checkfirst=True)

    op.add_column("patients", sa.Column("last_visit_at", sa.DateTime(timezone=True), nullable=True))

    op.add_column("visits", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("visits", sa.Column("payment_status", payment_status, server_default="NOT_PAID", nullable=False))
    op.add_column("visits", sa.Column("payment_method", payment_method, nullable=True))
    op.add_column("visits", sa.Column("consultation_fee", sa.Numeric(12, 2), nullable=True))
    op.alter_column("visits", "payment_status", server_default=None)

    op.add_column("operation_types", sa.Column("price", sa.Numeric(12, 2), server_default="0", nullable=False))
    op.alter_column("operation_types", "price", server_default=None)

    op.add_column("operations", sa.Column("payment_status", payment_status, server_default="NOT_PAID", nullable=False))
    op.add_column("operations", sa.Column("payment_method", payment_method, nullable=True))
    op.add_column("operations", sa.Column("operation_charge", sa.Numeric(12, 2), nullable=True))
    op.alter_column("operations", "payment_status", server_default=None)

    op.create_table(
        "payment_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("setting_key", sa.String(length=120), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payment_settings_id"), "payment_settings", ["id"], unique=False)
    op.create_index(op.f("ix_payment_settings_setting_key"), "payment_settings", ["setting_key"], unique=True)

    op.create_table(
        "operation_test_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("operation_test_id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["operation_test_id"], ["operation_tests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_operation_test_reports_id"), "operation_test_reports", ["id"], unique=False)
    op.create_index(op.f("ix_operation_test_reports_operation_test_id"), "operation_test_reports", ["operation_test_id"], unique=False)

    op.create_table(
        "medical_supplies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("category", supply_category, nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("current_stock", sa.Integer(), nullable=False),
        sa.Column("unit", sa.String(length=40), nullable=False),
        sa.Column("minimum_stock", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_medical_supplies_id"), "medical_supplies", ["id"], unique=False)
    op.create_index(op.f("ix_medical_supplies_category"), "medical_supplies", ["category"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("notification_type", notification_type, nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notifications_id"), "notifications", ["id"], unique=False)
    op.create_index(op.f("ix_notifications_notification_type"), "notifications", ["notification_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notifications_notification_type"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_id"), table_name="notifications")
    op.drop_table("notifications")

    op.drop_index(op.f("ix_medical_supplies_category"), table_name="medical_supplies")
    op.drop_index(op.f("ix_medical_supplies_id"), table_name="medical_supplies")
    op.drop_table("medical_supplies")

    op.drop_index(op.f("ix_operation_test_reports_operation_test_id"), table_name="operation_test_reports")
    op.drop_index(op.f("ix_operation_test_reports_id"), table_name="operation_test_reports")
    op.drop_table("operation_test_reports")

    op.drop_index(op.f("ix_payment_settings_setting_key"), table_name="payment_settings")
    op.drop_index(op.f("ix_payment_settings_id"), table_name="payment_settings")
    op.drop_table("payment_settings")

    op.drop_column("operations", "operation_charge")
    op.drop_column("operations", "payment_method")
    op.drop_column("operations", "payment_status")
    op.drop_column("operation_types", "price")
    op.drop_column("visits", "consultation_fee")
    op.drop_column("visits", "payment_method")
    op.drop_column("visits", "payment_status")
    op.drop_column("visits", "completed_at")
    op.drop_column("patients", "last_visit_at")

    for enum_type in reversed(all_enums):
        enum_type.drop(op.get_bind(), checkfirst=True)
