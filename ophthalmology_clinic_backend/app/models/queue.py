import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class QueueStatus(str, enum.Enum):
    WAITING = "waiting"
    IN_CONSULTATION = "in_consultation"
    COMPLETED = "completed"


class QueueEntry(Base):
    __tablename__ = "queue_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    receptionist_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    doctor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    queue_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[QueueStatus] = mapped_column(Enum(QueueStatus, name="queue_status"), default=QueueStatus.WAITING, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    patient: Mapped["Patient"] = relationship()
    receptionist: Mapped["User"] = relationship(foreign_keys=[receptionist_id])
    doctor: Mapped["User"] = relationship(foreign_keys=[doctor_id])
