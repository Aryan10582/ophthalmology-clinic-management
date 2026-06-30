"""patient ids and consultation sheet

Revision ID: 20260628_0003
Revises: 20260628_0002
Create Date: 2026-06-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260628_0003"
down_revision: str | None = "20260628_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("patients", sa.Column("date_of_birth", sa.Date(), nullable=True))

    op.add_column("visits", sa.Column("distance_prescription_enabled", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("visits", sa.Column("distance_right_sphere", sa.String(length=20), nullable=True))
    op.add_column("visits", sa.Column("distance_right_cylinder", sa.String(length=20), nullable=True))
    op.add_column("visits", sa.Column("distance_right_axis", sa.Integer(), nullable=True))
    op.add_column("visits", sa.Column("distance_right_va", sa.String(length=20), nullable=True))
    op.add_column("visits", sa.Column("distance_left_sphere", sa.String(length=20), nullable=True))
    op.add_column("visits", sa.Column("distance_left_cylinder", sa.String(length=20), nullable=True))
    op.add_column("visits", sa.Column("distance_left_axis", sa.Integer(), nullable=True))
    op.add_column("visits", sa.Column("distance_left_va", sa.String(length=20), nullable=True))
    op.add_column("visits", sa.Column("distance_add", sa.String(length=20), nullable=True))

    op.add_column("visits", sa.Column("near_prescription_enabled", sa.Boolean(), server_default=sa.false(), nullable=False))
    op.add_column("visits", sa.Column("near_right_sphere", sa.String(length=20), nullable=True))
    op.add_column("visits", sa.Column("near_right_cylinder", sa.String(length=20), nullable=True))
    op.add_column("visits", sa.Column("near_right_axis", sa.Integer(), nullable=True))
    op.add_column("visits", sa.Column("near_right_va", sa.String(length=20), nullable=True))
    op.add_column("visits", sa.Column("near_left_sphere", sa.String(length=20), nullable=True))
    op.add_column("visits", sa.Column("near_left_cylinder", sa.String(length=20), nullable=True))
    op.add_column("visits", sa.Column("near_left_axis", sa.Integer(), nullable=True))
    op.add_column("visits", sa.Column("near_left_va", sa.String(length=20), nullable=True))
    op.add_column("visits", sa.Column("near_add", sa.String(length=20), nullable=True))

    op.add_column("visits", sa.Column("eyelids_adnexa_right", sa.Text(), nullable=True))
    op.add_column("visits", sa.Column("eyelids_adnexa_left", sa.Text(), nullable=True))
    op.add_column("visits", sa.Column("extra_ocular_movements_right", sa.Text(), nullable=True))
    op.add_column("visits", sa.Column("extra_ocular_movements_left", sa.Text(), nullable=True))
    op.add_column("visits", sa.Column("cornea_right", sa.Text(), nullable=True))
    op.add_column("visits", sa.Column("cornea_left", sa.Text(), nullable=True))
    op.add_column("visits", sa.Column("anterior_chamber_right", sa.Text(), nullable=True))
    op.add_column("visits", sa.Column("anterior_chamber_left", sa.Text(), nullable=True))
    op.add_column("visits", sa.Column("conjunctiva_right", sa.Text(), nullable=True))
    op.add_column("visits", sa.Column("conjunctiva_left", sa.Text(), nullable=True))
    op.add_column("visits", sa.Column("pupil_right", sa.Text(), nullable=True))
    op.add_column("visits", sa.Column("pupil_left", sa.Text(), nullable=True))
    op.add_column("visits", sa.Column("lens_right", sa.Text(), nullable=True))
    op.add_column("visits", sa.Column("lens_left", sa.Text(), nullable=True))
    op.add_column("visits", sa.Column("fundus_right", sa.Text(), nullable=True))
    op.add_column("visits", sa.Column("fundus_left", sa.Text(), nullable=True))

    op.add_column("visits", sa.Column("advice", sa.Text(), nullable=True))
    op.add_column("visits", sa.Column("tests_prescribed", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("visits", "tests_prescribed")
    op.drop_column("visits", "advice")
    op.drop_column("visits", "fundus_left")
    op.drop_column("visits", "fundus_right")
    op.drop_column("visits", "lens_left")
    op.drop_column("visits", "lens_right")
    op.drop_column("visits", "pupil_left")
    op.drop_column("visits", "pupil_right")
    op.drop_column("visits", "conjunctiva_left")
    op.drop_column("visits", "conjunctiva_right")
    op.drop_column("visits", "anterior_chamber_left")
    op.drop_column("visits", "anterior_chamber_right")
    op.drop_column("visits", "cornea_left")
    op.drop_column("visits", "cornea_right")
    op.drop_column("visits", "extra_ocular_movements_left")
    op.drop_column("visits", "extra_ocular_movements_right")
    op.drop_column("visits", "eyelids_adnexa_left")
    op.drop_column("visits", "eyelids_adnexa_right")
    op.drop_column("visits", "near_add")
    op.drop_column("visits", "near_left_va")
    op.drop_column("visits", "near_left_axis")
    op.drop_column("visits", "near_left_cylinder")
    op.drop_column("visits", "near_left_sphere")
    op.drop_column("visits", "near_right_va")
    op.drop_column("visits", "near_right_axis")
    op.drop_column("visits", "near_right_cylinder")
    op.drop_column("visits", "near_right_sphere")
    op.drop_column("visits", "near_prescription_enabled")
    op.drop_column("visits", "distance_add")
    op.drop_column("visits", "distance_left_va")
    op.drop_column("visits", "distance_left_axis")
    op.drop_column("visits", "distance_left_cylinder")
    op.drop_column("visits", "distance_left_sphere")
    op.drop_column("visits", "distance_right_va")
    op.drop_column("visits", "distance_right_axis")
    op.drop_column("visits", "distance_right_cylinder")
    op.drop_column("visits", "distance_right_sphere")
    op.drop_column("visits", "distance_prescription_enabled")
    op.drop_column("patients", "date_of_birth")
