"""demo reference data flags

Revision ID: 20260630_0013
Revises: 20260630_0012
Create Date: 2026-06-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260630_0013"
down_revision: str | None = "20260630_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("operation_types", sa.Column("is_demo_data", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("medical_supplies", sa.Column("is_demo_data", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.execute(
        """
        UPDATE operation_types
        SET is_demo_data = true
        WHERE name IN ('Cataract', 'Cataract Surgery', 'LASIK', 'Retina Surgery', 'Glaucoma Surgery', 'Pterygium', 'Intravitreal Injection')
          AND EXISTS (SELECT 1 FROM users WHERE is_demo_account = true)
        """
    )
    op.execute(
        """
        UPDATE medical_supplies
        SET is_demo_data = true
        WHERE name IN ('Emergency Eye Wash', '2cc Syringe', 'Sterile Eye Drapes', 'Cotton Swabs', 'IOL Cartridge', 'Lubricant Eye Drops')
          AND EXISTS (SELECT 1 FROM users WHERE is_demo_account = true)
        """
    )
    op.alter_column("operation_types", "is_demo_data", server_default=None)
    op.alter_column("medical_supplies", "is_demo_data", server_default=None)
    op.drop_index(op.f("ix_operation_types_name"), table_name="operation_types")
    op.create_index(op.f("ix_operation_types_name"), "operation_types", ["name"], unique=False)
    op.create_unique_constraint("uq_operation_types_name_demo", "operation_types", ["name", "is_demo_data"])


def downgrade() -> None:
    op.drop_constraint("uq_operation_types_name_demo", "operation_types", type_="unique")
    op.drop_index(op.f("ix_operation_types_name"), table_name="operation_types")
    op.create_index(op.f("ix_operation_types_name"), "operation_types", ["name"], unique=True)
    op.drop_column("medical_supplies", "is_demo_data")
    op.drop_column("operation_types", "is_demo_data")
