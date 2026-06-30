from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.payment import PaymentMethod, PaymentStatus
from app.models.user import UserRole


class VisitPatientRead(BaseModel):
    id: int
    patient_id: str
    first_name: str
    last_name: str
    age: int
    gender: str
    phone: str | None = None
    address: str | None = None
    date_of_birth: date | None = None

    model_config = ConfigDict(from_attributes=True)


class VisitDoctorRead(BaseModel):
    id: int
    full_name: str
    email: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class VisitBase(BaseModel):
    patient_id: int
    doctor_id: int
    chief_complaint: str = Field(..., min_length=1)
    diagnosis: str | None = None
    prescription: str | None = None
    notes: str | None = None
    follow_up_date: date | None = None
    payment_status: PaymentStatus = PaymentStatus.NOT_PAID
    payment_method: PaymentMethod | None = None

    right_eye_sph: str | None = Field(default=None, max_length=20)
    right_eye_cyl: str | None = Field(default=None, max_length=20)
    right_eye_axis: int | None = Field(default=None, ge=0, le=180)
    right_eye_va: str | None = Field(default=None, max_length=20)
    left_eye_sph: str | None = Field(default=None, max_length=20)
    left_eye_cyl: str | None = Field(default=None, max_length=20)
    left_eye_axis: int | None = Field(default=None, ge=0, le=180)
    left_eye_va: str | None = Field(default=None, max_length=20)

    slit_lamp_enabled: bool = False
    slit_lamp_findings: str | None = None
    fundus_enabled: bool = False
    fundus_findings: str | None = None
    general_findings_enabled: bool = False
    general_findings: str | None = None

    iop_enabled: bool = False
    iop_right: int | None = Field(default=None, ge=0, le=80)
    iop_left: int | None = Field(default=None, ge=0, le=80)
    additional_notes: str | None = None

    distance_prescription_enabled: bool = False
    distance_right_sphere: str | None = Field(default=None, max_length=20)
    distance_right_cylinder: str | None = Field(default=None, max_length=20)
    distance_right_axis: int | None = Field(default=None, ge=0, le=180)
    distance_right_va: str | None = Field(default=None, max_length=20)
    distance_left_sphere: str | None = Field(default=None, max_length=20)
    distance_left_cylinder: str | None = Field(default=None, max_length=20)
    distance_left_axis: int | None = Field(default=None, ge=0, le=180)
    distance_left_va: str | None = Field(default=None, max_length=20)
    distance_add: str | None = Field(default=None, max_length=20)

    near_prescription_enabled: bool = False
    near_right_sphere: str | None = Field(default=None, max_length=20)
    near_right_cylinder: str | None = Field(default=None, max_length=20)
    near_right_axis: int | None = Field(default=None, ge=0, le=180)
    near_right_va: str | None = Field(default=None, max_length=20)
    near_left_sphere: str | None = Field(default=None, max_length=20)
    near_left_cylinder: str | None = Field(default=None, max_length=20)
    near_left_axis: int | None = Field(default=None, ge=0, le=180)
    near_left_va: str | None = Field(default=None, max_length=20)
    near_add: str | None = Field(default=None, max_length=20)

    eyelids_adnexa_right: str | None = None
    eyelids_adnexa_left: str | None = None
    extra_ocular_movements_right: str | None = None
    extra_ocular_movements_left: str | None = None
    cornea_right: str | None = None
    cornea_left: str | None = None
    anterior_chamber_right: str | None = None
    anterior_chamber_left: str | None = None
    conjunctiva_right: str | None = None
    conjunctiva_left: str | None = None
    pupil_right: str | None = None
    pupil_left: str | None = None
    lens_right: str | None = None
    lens_left: str | None = None
    fundus_right: str | None = None
    fundus_left: str | None = None

    advice: str | None = None
    tests_prescribed: str | None = None

    @field_validator("slit_lamp_findings")
    @classmethod
    def clear_slit_lamp_when_disabled(cls, value: str | None, info):
        if info.data.get("slit_lamp_enabled") is False:
            return None
        return value

    @field_validator("fundus_findings")
    @classmethod
    def clear_fundus_when_disabled(cls, value: str | None, info):
        if info.data.get("fundus_enabled") is False:
            return None
        return value

    @field_validator("general_findings")
    @classmethod
    def clear_general_when_disabled(cls, value: str | None, info):
        if info.data.get("general_findings_enabled") is False:
            return None
        return value


class VisitCreate(VisitBase):
    pass


class VisitUpdate(BaseModel):
    chief_complaint: str | None = Field(default=None, min_length=1)
    diagnosis: str | None = None
    prescription: str | None = None
    notes: str | None = None
    follow_up_date: date | None = None
    payment_status: PaymentStatus | None = None
    payment_method: PaymentMethod | None = None
    patient_id: int | None = None
    doctor_id: int | None = None

    right_eye_sph: str | None = Field(default=None, max_length=20)
    right_eye_cyl: str | None = Field(default=None, max_length=20)
    right_eye_axis: int | None = Field(default=None, ge=0, le=180)
    right_eye_va: str | None = Field(default=None, max_length=20)
    left_eye_sph: str | None = Field(default=None, max_length=20)
    left_eye_cyl: str | None = Field(default=None, max_length=20)
    left_eye_axis: int | None = Field(default=None, ge=0, le=180)
    left_eye_va: str | None = Field(default=None, max_length=20)

    slit_lamp_enabled: bool | None = None
    slit_lamp_findings: str | None = None
    fundus_enabled: bool | None = None
    fundus_findings: str | None = None
    general_findings_enabled: bool | None = None
    general_findings: str | None = None

    iop_enabled: bool | None = None
    iop_right: int | None = Field(default=None, ge=0, le=80)
    iop_left: int | None = Field(default=None, ge=0, le=80)
    additional_notes: str | None = None

    distance_prescription_enabled: bool | None = None
    distance_right_sphere: str | None = Field(default=None, max_length=20)
    distance_right_cylinder: str | None = Field(default=None, max_length=20)
    distance_right_axis: int | None = Field(default=None, ge=0, le=180)
    distance_right_va: str | None = Field(default=None, max_length=20)
    distance_left_sphere: str | None = Field(default=None, max_length=20)
    distance_left_cylinder: str | None = Field(default=None, max_length=20)
    distance_left_axis: int | None = Field(default=None, ge=0, le=180)
    distance_left_va: str | None = Field(default=None, max_length=20)
    distance_add: str | None = Field(default=None, max_length=20)

    near_prescription_enabled: bool | None = None
    near_right_sphere: str | None = Field(default=None, max_length=20)
    near_right_cylinder: str | None = Field(default=None, max_length=20)
    near_right_axis: int | None = Field(default=None, ge=0, le=180)
    near_right_va: str | None = Field(default=None, max_length=20)
    near_left_sphere: str | None = Field(default=None, max_length=20)
    near_left_cylinder: str | None = Field(default=None, max_length=20)
    near_left_axis: int | None = Field(default=None, ge=0, le=180)
    near_left_va: str | None = Field(default=None, max_length=20)
    near_add: str | None = Field(default=None, max_length=20)

    eyelids_adnexa_right: str | None = None
    eyelids_adnexa_left: str | None = None
    extra_ocular_movements_right: str | None = None
    extra_ocular_movements_left: str | None = None
    cornea_right: str | None = None
    cornea_left: str | None = None
    anterior_chamber_right: str | None = None
    anterior_chamber_left: str | None = None
    conjunctiva_right: str | None = None
    conjunctiva_left: str | None = None
    pupil_right: str | None = None
    pupil_left: str | None = None
    lens_right: str | None = None
    lens_left: str | None = None
    fundus_right: str | None = None
    fundus_left: str | None = None

    advice: str | None = None
    tests_prescribed: str | None = None


class VisitRead(VisitBase):
    id: int
    visit_date: datetime
    completed_at: datetime | None = None
    consultation_fee: float | None = None
    patient: VisitPatientRead | None = None
    doctor: VisitDoctorRead | None = None

    model_config = ConfigDict(from_attributes=True)
