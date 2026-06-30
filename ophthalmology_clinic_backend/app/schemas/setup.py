from pydantic import BaseModel, EmailStr, Field, model_validator


USERNAME_PATTERN = r"^[a-zA-Z0-9_.@-]+$"


class SetupStatus(BaseModel):
    needs_setup: bool


class SetupDoctorAccount(BaseModel):
    doctor_name: str = Field(..., min_length=2, max_length=255)
    username: str = Field(..., min_length=3, max_length=80, pattern=USERNAME_PATTERN)
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_match(self) -> "SetupDoctorAccount":
        if self.password != self.confirm_password:
            raise ValueError("Doctor password confirmation does not match")
        return self


class SetupReceptionistAccount(BaseModel):
    username: str = Field(..., min_length=3, max_length=80, pattern=USERNAME_PATTERN)
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_match(self) -> "SetupReceptionistAccount":
        if self.password != self.confirm_password:
            raise ValueError(f"Password confirmation does not match for receptionist {self.username}")
        return self


class SetupClinicInfo(BaseModel):
    clinic_name: str = Field(..., min_length=2, max_length=160)
    doctor_qualifications: str = Field(..., min_length=2, max_length=255)
    doctor_registration_number: str = Field(..., min_length=2, max_length=120)
    clinic_address: str = Field(..., min_length=2)
    clinic_phone: str = Field(..., min_length=5, max_length=80)
    email: EmailStr
    clinic_timings: str = Field(..., min_length=2, max_length=160)
    website: str | None = Field(default=None, max_length=160)


class ClinicSetupCreate(BaseModel):
    doctor: SetupDoctorAccount
    clinic: SetupClinicInfo
    receptionists: list[SetupReceptionistAccount] = []

    @model_validator(mode="after")
    def usernames_unique(self) -> "ClinicSetupCreate":
        usernames = [self.doctor.username.lower()] + [item.username.lower() for item in self.receptionists]
        if len(usernames) != len(set(usernames)):
            raise ValueError("Usernames must be unique")
        return self


class ClinicSetupRead(BaseModel):
    doctor_id: int
    receptionist_count: int


class ReceptionistCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=80, pattern=USERNAME_PATTERN)
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @model_validator(mode="after")
    def passwords_match(self) -> "ReceptionistCreate":
        if self.password != self.confirm_password:
            raise ValueError("Password confirmation does not match")
        return self


class ReceptionistUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=80, pattern=USERNAME_PATTERN)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    confirm_password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool | None = None

    @model_validator(mode="after")
    def password_confirmation_valid(self) -> "ReceptionistUpdate":
        if self.password is not None and self.password != self.confirm_password:
            raise ValueError("Password confirmation does not match")
        return self
