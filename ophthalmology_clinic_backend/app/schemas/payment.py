from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.payment import PaymentMethod, PaymentStatus


class PaymentUpdate(BaseModel):
    payment_status: PaymentStatus
    payment_method: PaymentMethod | None = None

    @model_validator(mode="after")
    def require_method_when_paid(self):
        if self.payment_status == PaymentStatus.PAID and self.payment_method is None:
            raise ValueError("payment_method is required when payment_status is paid")
        return self


class PaymentSettingRead(BaseModel):
    id: int
    setting_key: str
    amount: Decimal
    is_demo_data: bool = False
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentSettingUpdate(BaseModel):
    amount: Decimal = Field(..., ge=0)


class TodayIncomeRead(BaseModel):
    date: str
    consultation_income: Decimal
    operation_income: Decimal
    total_income: Decimal
