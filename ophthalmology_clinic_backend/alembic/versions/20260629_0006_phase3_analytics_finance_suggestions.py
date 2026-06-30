"""phase3 analytics finance suggestions

Revision ID: 20260629_0006
Revises: 20260629_0005
Create Date: 2026-06-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260629_0006"
down_revision: str | None = "20260629_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("medical_supplies", sa.Column("expiry_date", sa.Date(), nullable=True))

    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("expense_name", sa.String(length=160), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_expenses_id"), "expenses", ["id"], unique=False)
    op.create_index(op.f("ix_expenses_category"), "expenses", ["category"], unique=False)
    op.create_index(op.f("ix_expenses_expense_date"), "expenses", ["expense_date"], unique=False)

    op.create_table(
        "consultation_suggestions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("field_name", sa.String(length=60), nullable=False),
        sa.Column("suggestion_text", sa.Text(), nullable=False),
        sa.Column("usage_count", sa.Integer(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["doctor_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("doctor_id", "field_name", "suggestion_text", name="uq_suggestion_doctor_field_text"),
    )
    op.create_index(op.f("ix_consultation_suggestions_id"), "consultation_suggestions", ["id"], unique=False)
    op.create_index(op.f("ix_consultation_suggestions_doctor_id"), "consultation_suggestions", ["doctor_id"], unique=False)
    op.create_index(op.f("ix_consultation_suggestions_field_name"), "consultation_suggestions", ["field_name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_consultation_suggestions_field_name"), table_name="consultation_suggestions")
    op.drop_index(op.f("ix_consultation_suggestions_doctor_id"), table_name="consultation_suggestions")
    op.drop_index(op.f("ix_consultation_suggestions_id"), table_name="consultation_suggestions")
    op.drop_table("consultation_suggestions")

    op.drop_index(op.f("ix_expenses_expense_date"), table_name="expenses")
    op.drop_index(op.f("ix_expenses_category"), table_name="expenses")
    op.drop_index(op.f("ix_expenses_id"), table_name="expenses")
    op.drop_table("expenses")

    op.drop_column("medical_supplies", "expiry_date")
