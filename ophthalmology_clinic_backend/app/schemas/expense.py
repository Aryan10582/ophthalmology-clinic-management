from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


DEFAULT_EXPENSE_CATEGORIES = [
    "Medical Supplies",
    "Medicines",
    "Surgical Consumables",
    "Equipment Purchase",
    "Equipment Maintenance",
    "Staff Salary",
    "Rent",
    "Electricity",
    "Internet",
    "Water",
    "Miscellaneous",
]


class ExpenseBase(BaseModel):
    expense_name: str = Field(..., min_length=1, max_length=160)
    category: str = Field(..., min_length=1, max_length=80)
    amount: Decimal = Field(..., ge=0)
    expense_date: date
    notes: str | None = None


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    expense_name: str | None = Field(default=None, min_length=1, max_length=160)
    category: str | None = Field(default=None, min_length=1, max_length=80)
    amount: Decimal | None = Field(default=None, ge=0)
    expense_date: date | None = None
    notes: str | None = None


class ExpenseRead(ExpenseBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
