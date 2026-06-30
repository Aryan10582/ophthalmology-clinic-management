import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class FollowUpType(str, enum.Enum):
    NORMAL = "normal"
    OPERATION_NEXT_DAY = "operation_next_day"
    OPERATION_ONE_WEEK = "operation_one_week"


class FollowUpStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    operation_id: Mapped[int | None] = mapped_column(ForeignKey("operations.id", ondelete="CASCADE"), nullable=True, index=True)
    follow_up_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    follow_up_type: Mapped[FollowUpType] = mapped_column(Enum(FollowUpType, name="follow_up_type"), nullable=False)
    status: Mapped[FollowUpStatus] = mapped_column(Enum(FollowUpStatus, name="follow_up_status"), default=FollowUpStatus.SCHEDULED, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    patient: Mapped["Patient"] = relationship()
    doctor: Mapped["User"] = relationship()
    operation: Mapped["Operation"] = relationship()
