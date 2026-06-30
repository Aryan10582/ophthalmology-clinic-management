from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.payment import PaymentMethod, PaymentStatus


class Visit(Base):
    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    visit_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    chief_complaint: Mapped[str] = mapped_column(Text, nullable=False)
    diagnosis: Mapped[str | None] = mapped_column(Text, nullable=True)
    prescription: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus, name="payment_status"), default=PaymentStatus.NOT_PAID, nullable=False)
    payment_method: Mapped[PaymentMethod | None] = mapped_column(Enum(PaymentMethod, name="payment_method"), nullable=True)
    consultation_fee: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    right_eye_sph: Mapped[str | None] = mapped_column(String(20), nullable=True)
    right_eye_cyl: Mapped[str | None] = mapped_column(String(20), nullable=True)
    right_eye_axis: Mapped[int | None] = mapped_column(Integer, nullable=True)
    right_eye_va: Mapped[str | None] = mapped_column(String(20), nullable=True)
    left_eye_sph: Mapped[str | None] = mapped_column(String(20), nullable=True)
    left_eye_cyl: Mapped[str | None] = mapped_column(String(20), nullable=True)
    left_eye_axis: Mapped[int | None] = mapped_column(Integer, nullable=True)
    left_eye_va: Mapped[str | None] = mapped_column(String(20), nullable=True)

    slit_lamp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    slit_lamp_findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    fundus_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fundus_findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    general_findings_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    general_findings: Mapped[str | None] = mapped_column(Text, nullable=True)

    iop_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    iop_right: Mapped[int | None] = mapped_column(Integer, nullable=True)
    iop_left: Mapped[int | None] = mapped_column(Integer, nullable=True)
    additional_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    distance_prescription_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    distance_right_sphere: Mapped[str | None] = mapped_column(String(20), nullable=True)
    distance_right_cylinder: Mapped[str | None] = mapped_column(String(20), nullable=True)
    distance_right_axis: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance_right_va: Mapped[str | None] = mapped_column(String(20), nullable=True)
    distance_left_sphere: Mapped[str | None] = mapped_column(String(20), nullable=True)
    distance_left_cylinder: Mapped[str | None] = mapped_column(String(20), nullable=True)
    distance_left_axis: Mapped[int | None] = mapped_column(Integer, nullable=True)
    distance_left_va: Mapped[str | None] = mapped_column(String(20), nullable=True)
    distance_add: Mapped[str | None] = mapped_column(String(20), nullable=True)

    near_prescription_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    near_right_sphere: Mapped[str | None] = mapped_column(String(20), nullable=True)
    near_right_cylinder: Mapped[str | None] = mapped_column(String(20), nullable=True)
    near_right_axis: Mapped[int | None] = mapped_column(Integer, nullable=True)
    near_right_va: Mapped[str | None] = mapped_column(String(20), nullable=True)
    near_left_sphere: Mapped[str | None] = mapped_column(String(20), nullable=True)
    near_left_cylinder: Mapped[str | None] = mapped_column(String(20), nullable=True)
    near_left_axis: Mapped[int | None] = mapped_column(Integer, nullable=True)
    near_left_va: Mapped[str | None] = mapped_column(String(20), nullable=True)
    near_add: Mapped[str | None] = mapped_column(String(20), nullable=True)

    eyelids_adnexa_right: Mapped[str | None] = mapped_column(Text, nullable=True)
    eyelids_adnexa_left: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_ocular_movements_right: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_ocular_movements_left: Mapped[str | None] = mapped_column(Text, nullable=True)
    cornea_right: Mapped[str | None] = mapped_column(Text, nullable=True)
    cornea_left: Mapped[str | None] = mapped_column(Text, nullable=True)
    anterior_chamber_right: Mapped[str | None] = mapped_column(Text, nullable=True)
    anterior_chamber_left: Mapped[str | None] = mapped_column(Text, nullable=True)
    conjunctiva_right: Mapped[str | None] = mapped_column(Text, nullable=True)
    conjunctiva_left: Mapped[str | None] = mapped_column(Text, nullable=True)
    pupil_right: Mapped[str | None] = mapped_column(Text, nullable=True)
    pupil_left: Mapped[str | None] = mapped_column(Text, nullable=True)
    lens_right: Mapped[str | None] = mapped_column(Text, nullable=True)
    lens_left: Mapped[str | None] = mapped_column(Text, nullable=True)
    fundus_right: Mapped[str | None] = mapped_column(Text, nullable=True)
    fundus_left: Mapped[str | None] = mapped_column(Text, nullable=True)

    advice: Mapped[str | None] = mapped_column(Text, nullable=True)
    tests_prescribed: Mapped[str | None] = mapped_column(Text, nullable=True)

    patient: Mapped["Patient"] = relationship(back_populates="visits")
    doctor: Mapped["User"] = relationship(back_populates="visits")
