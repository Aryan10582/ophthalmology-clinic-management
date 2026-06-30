from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class MedicalSupplyBatchCreate(BaseModel):
    batch_code: str = Field(..., min_length=1, max_length=80)
    quantity: int = Field(..., gt=0)
    expiry_date: date
    purchase_date: date
    notes: str | None = None


class MedicalSupplyConsume(BaseModel):
    quantity: int = Field(..., gt=0)
    notes: str | None = None


class MedicalSupplyBatchRead(BaseModel):
    id: int
    supply_id: int
    batch_code: str
    quantity_initial: int
    quantity_remaining: int
    expiry_date: date
    purchase_date: date
    notes: str | None = None
    created_at: datetime
    expiry_status: str = "safe"
    days_to_expiry: int | None = None

    model_config = ConfigDict(from_attributes=True)
