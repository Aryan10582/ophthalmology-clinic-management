"""queue operations followups

Revision ID: 20260628_0004
Revises: 20260628_0003
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260628_0004"
down_revision: str | None = "20260628_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

queue_status = postgresql.ENUM(
    "WAITING",
    "IN_CONSULTATION",
    "COMPLETED",
    name="queue_status",
    create_type=False,
)

operation_status = postgresql.ENUM(
    "PLANNED",
    "SCHEDULED",
    "COMPLETED",
    "CANCELLED",
    name="operation_status",
    create_type=False,
)

test_status = postgresql.ENUM(
    "PENDING",
    "DONE",
    name="test_status",
    create_type=False,
)

fitness_status = postgresql.ENUM(
    "PENDING",
    "FIT",
    "NOT_FIT",
    name="fitness_status",
    create_type=False,
)

follow_up_type = postgresql.ENUM(
    "NORMAL",
    "OPERATION_NEXT_DAY",
    "OPERATION_ONE_WEEK",
    name="follow_up_type",
    create_type=False,
)

follow_up_status = postgresql.ENUM(
    "SCHEDULED",
    "COMPLETED",
    "CANCELLED",
    name="follow_up_status",
    create_type=False,
)

all_enums = (
    queue_status,
    operation_status,
    test_status,
    fitness_status,
    follow_up_type,
    follow_up_status,
)


def upgrade() -> None:
    bind = op.get_bind()
    for enum_type in all_enums:
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "queue_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("receptionist_id", sa.Integer(), nullable=True),
        sa.Column("doctor_id", sa.Integer(), nullable=True),
        sa.Column("queue_date", sa.Date(), nullable=False),
        sa.Column("status", queue_status, nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["doctor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["receptionist_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_queue_entries_id"), "queue_entries", ["id"], unique=False)
    op.create_index(op.f("ix_queue_entries_patient_id"), "queue_entries", ["patient_id"], unique=False)
    op.create_index(op.f("ix_queue_entries_receptionist_id"), "queue_entries", ["receptionist_id"], unique=False)
    op.create_index(op.f("ix_queue_entries_doctor_id"), "queue_entries", ["doctor_id"], unique=False)
    op.create_index(op.f("ix_queue_entries_queue_date"), "queue_entries", ["queue_date"], unique=False)

    op.create_table(
        "operation_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_operation_types_id"), "operation_types", ["id"], unique=False)
    op.create_index(op.f("ix_operation_types_name"), "operation_types", ["name"], unique=True)

    op.create_table(
        "operations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("operation_type_id", sa.Integer(), nullable=False),
        sa.Column("operation_date", sa.Date(), nullable=False),
        sa.Column("status", operation_status, nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["doctor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["operation_type_id"], ["operation_types.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_operations_id"), "operations", ["id"], unique=False)
    op.create_index(op.f("ix_operations_patient_id"), "operations", ["patient_id"], unique=False)
    op.create_index(op.f("ix_operations_doctor_id"), "operations", ["doctor_id"], unique=False)
    op.create_index(op.f("ix_operations_operation_type_id"), "operations", ["operation_type_id"], unique=False)
    op.create_index(op.f("ix_operations_operation_date"), "operations", ["operation_date"], unique=False)

    op.create_table(
        "operation_tests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("operation_id", sa.Integer(), nullable=False),
        sa.Column("test_name", sa.String(length=160), nullable=False),
        sa.Column("status", test_status, nullable=False),
        sa.Column("test_date", sa.Date(), nullable=True),
        sa.Column("result", sa.String(length=255), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("fitness_status", fitness_status, nullable=True),
        sa.ForeignKeyConstraint(["operation_id"], ["operations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_operation_tests_id"), "operation_tests", ["id"], unique=False)
    op.create_index(op.f("ix_operation_tests_operation_id"), "operation_tests", ["operation_id"], unique=False)

    op.create_table(
        "follow_ups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("doctor_id", sa.Integer(), nullable=True),
        sa.Column("operation_id", sa.Integer(), nullable=True),
        sa.Column("follow_up_date", sa.Date(), nullable=False),
        sa.Column("follow_up_type", follow_up_type, nullable=False),
        sa.Column("status", follow_up_status, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["doctor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["operation_id"], ["operations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_follow_ups_id"), "follow_ups", ["id"], unique=False)
    op.create_index(op.f("ix_follow_ups_patient_id"), "follow_ups", ["patient_id"], unique=False)
    op.create_index(op.f("ix_follow_ups_doctor_id"), "follow_ups", ["doctor_id"], unique=False)
    op.create_index(op.f("ix_follow_ups_operation_id"), "follow_ups", ["operation_id"], unique=False)
    op.create_index(op.f("ix_follow_ups_follow_up_date"), "follow_ups", ["follow_up_date"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_follow_ups_follow_up_date"), table_name="follow_ups")
    op.drop_index(op.f("ix_follow_ups_operation_id"), table_name="follow_ups")
    op.drop_index(op.f("ix_follow_ups_doctor_id"), table_name="follow_ups")
    op.drop_index(op.f("ix_follow_ups_patient_id"), table_name="follow_ups")
    op.drop_index(op.f("ix_follow_ups_id"), table_name="follow_ups")
    op.drop_table("follow_ups")

    op.drop_index(op.f("ix_operation_tests_operation_id"), table_name="operation_tests")
    op.drop_index(op.f("ix_operation_tests_id"), table_name="operation_tests")
    op.drop_table("operation_tests")

    op.drop_index(op.f("ix_operations_operation_date"), table_name="operations")
    op.drop_index(op.f("ix_operations_operation_type_id"), table_name="operations")
    op.drop_index(op.f("ix_operations_doctor_id"), table_name="operations")
    op.drop_index(op.f("ix_operations_patient_id"), table_name="operations")
    op.drop_index(op.f("ix_operations_id"), table_name="operations")
    op.drop_table("operations")

    op.drop_index(op.f("ix_operation_types_name"), table_name="operation_types")
    op.drop_index(op.f("ix_operation_types_id"), table_name="operation_types")
    op.drop_table("operation_types")

    op.drop_index(op.f("ix_queue_entries_queue_date"), table_name="queue_entries")
    op.drop_index(op.f("ix_queue_entries_doctor_id"), table_name="queue_entries")
    op.drop_index(op.f("ix_queue_entries_receptionist_id"), table_name="queue_entries")
    op.drop_index(op.f("ix_queue_entries_patient_id"), table_name="queue_entries")
    op.drop_index(op.f("ix_queue_entries_id"), table_name="queue_entries")
    op.drop_table("queue_entries")

    for enum_type in reversed(all_enums):
        enum_type.drop(op.get_bind(), checkfirst=True)
