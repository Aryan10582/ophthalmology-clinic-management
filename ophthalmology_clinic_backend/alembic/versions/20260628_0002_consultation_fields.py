"""consultation fields

Revision ID: 20260628_0002
Revises: 20260628_0001
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260628_0002"
down_revision: str | None = "20260628_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("visits", sa.Column("right_eye_sph", sa.String(length=20), nullable=True))
    op.add_column("visits", sa.Column("right_eye_cyl", sa.String(length=20), nullable=True))
    op.add_column("visits", sa.Column("right_eye_axis", sa.Integer(), nullable=True))
    op.add_column("visits", sa.Column("right_eye_va", sa.String(length=20), nullable=True))
    op.add_column("visits", sa.Column("left_eye_sph", sa.String(length=20), nullable=True))
    op.add_column("visits", sa.Column("left_eye_cyl", sa.String(length=20), nullable=True))
    op.add_column("visits", sa.Column("left_eye_axis", sa.Integer(), nullable=True))
    op.add_column("visits", sa.Column("left_eye_va", sa.String(length=20), nullable=True))
    op.add_column("visits", sa.Column("slit_lamp_enabled", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("visits", sa.Column("slit_lamp_findings", sa.Text(), nullable=True))
    op.add_column("visits", sa.Column("fundus_enabled", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("visits", sa.Column("fundus_findings", sa.Text(), nullable=True))
    op.add_column("visits", sa.Column("general_findings_enabled", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("visits", sa.Column("general_findings", sa.Text(), nullable=True))
    op.add_column("visits", sa.Column("iop_enabled", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("visits", sa.Column("iop_right", sa.Integer(), nullable=True))
    op.add_column("visits", sa.Column("iop_left", sa.Integer(), nullable=True))
    op.add_column("visits", sa.Column("additional_notes", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("visits", "additional_notes")
    op.drop_column("visits", "iop_left")
    op.drop_column("visits", "iop_right")
    op.drop_column("visits", "iop_enabled")
    op.drop_column("visits", "general_findings")
    op.drop_column("visits", "general_findings_enabled")
    op.drop_column("visits", "fundus_findings")
    op.drop_column("visits", "fundus_enabled")
    op.drop_column("visits", "slit_lamp_findings")
    op.drop_column("visits", "slit_lamp_enabled")
    op.drop_column("visits", "left_eye_va")
    op.drop_column("visits", "left_eye_axis")
    op.drop_column("visits", "left_eye_cyl")
    op.drop_column("visits", "left_eye_sph")
    op.drop_column("visits", "right_eye_va")
    op.drop_column("visits", "right_eye_axis")
    op.drop_column("visits", "right_eye_cyl")
    op.drop_column("visits", "right_eye_sph")
