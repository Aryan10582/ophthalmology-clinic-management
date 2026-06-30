from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PrescriptionTemplateBase(BaseModel):
    template_name: str = "minimal_white"
    clinic_logo: str | None = None
    doctor_signature: str | None = None
    doctor_name: str | None = Field(default=None, max_length=160)
    doctor_qualifications: str | None = Field(default=None, max_length=255)
    doctor_registration_number: str | None = Field(default=None, max_length=120)
    clinic_name: str | None = Field(default=None, max_length=160)
    clinic_address: str | None = None
    clinic_phone: str | None = Field(default=None, max_length=80)
    clinic_timings: str | None = Field(default=None, max_length=160)
    website: str | None = Field(default=None, max_length=160)
    email: str | None = Field(default=None, max_length=160)
    footer_text: str | None = None
    header_background_color: str = "#ffffff"
    header_font_color: str = "#17202a"
    footer_background_color: str = "#ffffff"
    footer_font_color: str = "#17202a"
    accent_color: str = "#147c72"
    border_color: str = "#d8e1e8"
    font_style: str = "Inter"
    header_alignment: str = "left"
    logo_position: str = "left"


class PrescriptionTemplateUpdate(PrescriptionTemplateBase):
    pass


class PrescriptionTemplateRead(PrescriptionTemplateBase):
    id: int
    doctor_id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
