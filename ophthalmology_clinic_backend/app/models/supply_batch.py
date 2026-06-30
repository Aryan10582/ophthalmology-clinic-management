from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class MedicalSupplyBatch(Base):
    __tablename__ = "medical_supply_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    supply_id: Mapped[int] = mapped_column(ForeignKey("medical_supplies.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    quantity_initial: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_remaining: Mapped[int] = mapped_column(Integer, nullable=False)
    expiry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    supply: Mapped["MedicalSupply"] = relationship(back_populates="batches")
