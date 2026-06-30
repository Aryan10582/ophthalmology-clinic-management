from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.operation import FitnessStatus, OperationStatus, TestStatus
from app.models.payment import PaymentMethod, PaymentStatus
from app.schemas.patient import PatientRead
from app.schemas.user import UserRead


class OperationTypeBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    price: float = Field(default=0, ge=0)
    is_active: bool = True
    is_demo_data: bool = False


class OperationTypeCreate(OperationTypeBase):
    pass


class OperationTypeRead(OperationTypeBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OperationTestBase(BaseModel):
    test_name: str = Field(..., min_length=1, max_length=160)
    status: TestStatus = TestStatus.PENDING
    test_date: date | None = None
    result: str | None = Field(default=None, max_length=255)
    remarks: str | None = None
    fitness_status: FitnessStatus | None = None


class OperationTestCreate(OperationTestBase):
    pass


class OperationTestUpdate(BaseModel):
    status: TestStatus | None = None
    test_date: date | None = None
    result: str | None = Field(default=None, max_length=255)
    remarks: str | None = None
    fitness_status: FitnessStatus | None = None


class OperationTestRead(OperationTestBase):
    id: int
    operation_id: int
    reports: list["OperationTestReportRead"] = []

    model_config = ConfigDict(from_attributes=True)


class OperationCreate(BaseModel):
    patient_id: int
    visit_id: int | None = None
    doctor_id: int
    operation_type_id: int
    operation_date: date
    status: OperationStatus = OperationStatus.PLANNED
    remarks: str | None = None


class OperationUpdate(BaseModel):
    doctor_id: int | None = None
    operation_type_id: int | None = None
    operation_date: date | None = None
    status: OperationStatus | None = None
    remarks: str | None = None
    payment_status: PaymentStatus | None = None
    payment_method: PaymentMethod | None = None


class OperationRead(BaseModel):
    id: int
    visit_id: int
    patient_id: int
    doctor_id: int
    operation_type_id: int
    operation_date: date
    status: OperationStatus
    remarks: str | None = None
    payment_status: PaymentStatus
    payment_method: PaymentMethod | None = None
    operation_charge: float | None = None
    created_at: datetime
    patient: PatientRead | None = None
    doctor: UserRead | None = None
    operation_type: OperationTypeRead | None = None
    tests: list[OperationTestRead] = []
    ready_for_surgery: bool = False

    model_config = ConfigDict(from_attributes=True)


class OperationTestReportRead(BaseModel):
    id: int
    operation_test_id: int
    original_filename: str
    stored_filename: str
    content_type: str
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
