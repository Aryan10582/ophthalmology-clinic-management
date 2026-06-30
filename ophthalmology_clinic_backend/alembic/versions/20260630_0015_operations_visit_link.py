"""Link operations to consultations.

Revision ID: 20260630_0015
Revises: 20260630_0014
Create Date: 2026-06-30 00:15:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260630_0015"
down_revision = "20260630_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("operations", sa.Column("visit_id", sa.Integer(), nullable=True))

    bind = op.get_bind()
    operations = bind.execute(
        sa.text("SELECT id, patient_id, doctor_id, operation_date, remarks FROM operations WHERE visit_id IS NULL ORDER BY id")
    ).mappings()
    for operation in operations:
        visit_id = bind.execute(
            sa.text(
                """
                INSERT INTO visits (
                    patient_id,
                    doctor_id,
                    visit_date,
                    chief_complaint,
                    diagnosis,
                    notes,
                    payment_status
                )
                VALUES (
                    :patient_id,
                    :doctor_id,
                    :visit_date,
                    'Operation planning consultation',
                    'Surgical case planned',
                    :notes,
                    'NOT_PAID'
                )
                RETURNING id
                """
            ),
            {
                "patient_id": operation["patient_id"],
                "doctor_id": operation["doctor_id"],
                "visit_date": operation["operation_date"],
                "notes": operation["remarks"] or "Migrated operation consultation",
            },
        ).scalar_one()
        bind.execute(sa.text("UPDATE operations SET visit_id = :visit_id WHERE id = :operation_id"), {"visit_id": visit_id, "operation_id": operation["id"]})

    op.alter_column("operations", "visit_id", nullable=False)
    op.create_index(op.f("ix_operations_visit_id"), "operations", ["visit_id"], unique=True)
    op.create_foreign_key("fk_operations_visit_id_visits", "operations", "visits", ["visit_id"], ["id"], ondelete="CASCADE")


def downgrade() -> None:
    op.drop_constraint("fk_operations_visit_id_visits", "operations", type_="foreignkey")
    op.drop_index(op.f("ix_operations_visit_id"), table_name="operations")
    op.drop_column("operations", "visit_id")
