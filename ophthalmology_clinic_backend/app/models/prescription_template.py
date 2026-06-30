from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class PrescriptionTemplate(Base):
    __tablename__ = "prescription_templates"
    __table_args__ = (UniqueConstraint("doctor_id", name="uq_prescription_template_doctor"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    template_name: Mapped[str] = mapped_column(String(80), default="minimal_white", nullable=False)
    clinic_logo: Mapped[str | None] = mapped_column(Text, nullable=True)
    doctor_signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    doctor_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    doctor_qualifications: Mapped[str | None] = mapped_column(String(255), nullable=True)
    doctor_registration_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    clinic_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    clinic_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    clinic_phone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    clinic_timings: Mapped[str | None] = mapped_column(String(160), nullable=True)
    website: Mapped[str | None] = mapped_column(String(160), nullable=True)
    email: Mapped[str | None] = mapped_column(String(160), nullable=True)
    footer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    header_background_color: Mapped[str] = mapped_column(String(20), default="#ffffff", nullable=False)
    header_font_color: Mapped[str] = mapped_column(String(20), default="#17202a", nullable=False)
    footer_background_color: Mapped[str] = mapped_column(String(20), default="#ffffff", nullable=False)
    footer_font_color: Mapped[str] = mapped_column(String(20), default="#17202a", nullable=False)
    accent_color: Mapped[str] = mapped_column(String(20), default="#147c72", nullable=False)
    border_color: Mapped[str] = mapped_column(String(20), default="#d8e1e8", nullable=False)
    font_style: Mapped[str] = mapped_column(String(80), default="Inter", nullable=False)
    header_alignment: Mapped[str] = mapped_column(String(20), default="left", nullable=False)
    logo_position: Mapped[str] = mapped_column(String(20), default="left", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
