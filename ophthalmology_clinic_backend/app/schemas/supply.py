from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.supply import NotificationType, SupplyCategory
from app.schemas.supply_batch import MedicalSupplyBatchRead


class MedicalSupplyCreate(BaseModel):
    category: SupplyCategory
    name: str = Field(..., min_length=1, max_length=160)
    current_stock: int = Field(..., ge=0)
    unit: str = Field(..., min_length=1, max_length=40)
    minimum_stock: int = Field(..., ge=0)
    expiry_date: date | None = None
    notes: str | None = None
    is_demo_data: bool = False


class MedicalSupplyUpdate(BaseModel):
    category: SupplyCategory | None = None
    name: str | None = Field(default=None, min_length=1, max_length=160)
    current_stock: int | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, min_length=1, max_length=40)
    minimum_stock: int | None = Field(default=None, ge=0)
    expiry_date: date | None = None
    notes: str | None = None


class MedicalSupplyRead(MedicalSupplyCreate):
    id: int
    updated_at: datetime
    is_low_stock: bool
    expiry_status: str = "not_tracked"
    days_to_expiry: int | None = None
    batches: list[MedicalSupplyBatchRead] = []

    model_config = ConfigDict(from_attributes=True)


class NotificationRead(BaseModel):
    id: int
    notification_type: NotificationType
    title: str
    message: str
    is_read: bool
    is_demo_data: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
