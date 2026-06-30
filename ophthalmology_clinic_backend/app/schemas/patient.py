from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PatientBase(BaseModel):
    patient_id: str | None = Field(default=None, min_length=2, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=0, le=130)
    gender: str = Field(..., min_length=1, max_length=30)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=500)
    date_of_birth: date | None = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    age: int | None = Field(default=None, ge=0, le=130)
    gender: str | None = Field(default=None, min_length=1, max_length=30)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=500)
    date_of_birth: date | None = None


class PatientRead(PatientBase):
    id: int
    patient_id: str
    created_at: datetime
    last_visit_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
