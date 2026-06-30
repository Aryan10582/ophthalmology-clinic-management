"""polishing templates inventory

Revision ID: 20260629_0007
Revises: 20260629_0006
Create Date: 2026-06-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260629_0007"
down_revision: str | None = "20260629_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "prescription_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("template_name", sa.String(length=80), nullable=False),
        sa.Column("clinic_logo", sa.Text(), nullable=True),
        sa.Column("doctor_name", sa.String(length=160), nullable=True),
        sa.Column("doctor_qualifications", sa.String(length=255), nullable=True),
        sa.Column("doctor_registration_number", sa.String(length=120), nullable=True),
        sa.Column("clinic_name", sa.String(length=160), nullable=True),
        sa.Column("clinic_address", sa.Text(), nullable=True),
        sa.Column("clinic_phone", sa.String(length=80), nullable=True),
        sa.Column("clinic_timings", sa.String(length=160), nullable=True),
        sa.Column("website", sa.String(length=160), nullable=True),
        sa.Column("email", sa.String(length=160), nullable=True),
        sa.Column("footer_text", sa.Text(), nullable=True),
        sa.Column("header_background_color", sa.String(length=20), nullable=False),
        sa.Column("header_font_color", sa.String(length=20), nullable=False),
        sa.Column("footer_background_color", sa.String(length=20), nullable=False),
        sa.Column("footer_font_color", sa.String(length=20), nullable=False),
        sa.Column("accent_color", sa.String(length=20), nullable=False),
        sa.Column("border_color", sa.String(length=20), nullable=False),
        sa.Column("font_style", sa.String(length=80), nullable=False),
        sa.Column("header_alignment", sa.String(length=20), nullable=False),
        sa.Column("logo_position", sa.String(length=20), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["doctor_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("doctor_id", name="uq_prescription_template_doctor"),
    )
    op.create_index(op.f("ix_prescription_templates_id"), "prescription_templates", ["id"], unique=False)
    op.create_index(op.f("ix_prescription_templates_doctor_id"), "prescription_templates", ["doctor_id"], unique=False)

    op.create_table(
        "medical_supply_batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("supply_id", sa.Integer(), nullable=False),
        sa.Column("batch_code", sa.String(length=80), nullable=False),
        sa.Column("quantity_initial", sa.Integer(), nullable=False),
        sa.Column("quantity_remaining", sa.Integer(), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=False),
        sa.Column("purchase_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["supply_id"], ["medical_supplies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_medical_supply_batches_id"), "medical_supply_batches", ["id"], unique=False)
    op.create_index(op.f("ix_medical_supply_batches_supply_id"), "medical_supply_batches", ["supply_id"], unique=False)
    op.create_index(op.f("ix_medical_supply_batches_batch_code"), "medical_supply_batches", ["batch_code"], unique=False)
    op.create_index(op.f("ix_medical_supply_batches_expiry_date"), "medical_supply_batches", ["expiry_date"], unique=False)
    op.create_index(op.f("ix_medical_supply_batches_purchase_date"), "medical_supply_batches", ["purchase_date"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_medical_supply_batches_purchase_date"), table_name="medical_supply_batches")
    op.drop_index(op.f("ix_medical_supply_batches_expiry_date"), table_name="medical_supply_batches")
    op.drop_index(op.f("ix_medical_supply_batches_batch_code"), table_name="medical_supply_batches")
    op.drop_index(op.f("ix_medical_supply_batches_supply_id"), table_name="medical_supply_batches")
    op.drop_index(op.f("ix_medical_supply_batches_id"), table_name="medical_supply_batches")
    op.drop_table("medical_supply_batches")

    op.drop_index(op.f("ix_prescription_templates_doctor_id"), table_name="prescription_templates")
    op.drop_index(op.f("ix_prescription_templates_id"), table_name="prescription_templates")
    op.drop_table("prescription_templates")
