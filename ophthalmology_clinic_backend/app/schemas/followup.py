from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.followup import FollowUpStatus, FollowUpType
from app.schemas.patient import PatientRead
from app.schemas.user import UserRead


class FollowUpCreate(BaseModel):
    patient_id: int
    doctor_id: int | None = None
    operation_id: int | None = None
    follow_up_date: date
    follow_up_type: FollowUpType = FollowUpType.NORMAL
    status: FollowUpStatus = FollowUpStatus.SCHEDULED
    notes: str | None = None


class FollowUpUpdate(BaseModel):
    doctor_id: int | None = None
    follow_up_date: date | None = None
    follow_up_type: FollowUpType | None = None
    status: FollowUpStatus | None = None
    notes: str | None = None


class FollowUpRead(BaseModel):
    id: int
    patient_id: int
    doctor_id: int | None = None
    operation_id: int | None = None
    follow_up_date: date
    follow_up_type: FollowUpType
    status: FollowUpStatus
    notes: str | None = None
    created_at: datetime
    patient: PatientRead | None = None
    doctor: UserRead | None = None

    model_config = ConfigDict(from_attributes=True)


class CalendarEvent(BaseModel):
    id: str
    date: date
    title: str
    category: str
    color: str
    patient_name: str
    source_id: int
