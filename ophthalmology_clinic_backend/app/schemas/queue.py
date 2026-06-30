from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.queue import QueueStatus
from app.models.payment import PaymentMethod, PaymentStatus
from app.schemas.patient import PatientRead
from app.schemas.user import UserRead


class QueueEntryCreate(BaseModel):
    patient_id: int | None = None
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    age: int | None = Field(default=None, ge=0, le=130)
    gender: str | None = Field(default=None, max_length=30)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=500)
    queue_date: date | None = None
    reason: str | None = Field(default=None, max_length=255)


class QueueEntryUpdate(BaseModel):
    status: QueueStatus | None = None
    doctor_id: int | None = None
    reason: str | None = Field(default=None, max_length=255)


class QueueEntryRead(BaseModel):
    id: int
    patient_id: int
    receptionist_id: int | None = None
    doctor_id: int | None = None
    queue_date: date
    status: QueueStatus
    reason: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    completed_visit_id: int | None = None
    payment_status: PaymentStatus | None = None
    payment_method: PaymentMethod | None = None
    consultation_fee: float | None = None
    patient: PatientRead | None = None
    receptionist: UserRead | None = None
    doctor: UserRead | None = None

    model_config = ConfigDict(from_attributes=True)
