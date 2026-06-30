import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Enum, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class PaymentStatus(str, enum.Enum):
    NOT_PAID = "not_paid"
    PAID = "paid"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    UPI_QR = "upi_qr"


class PaymentSetting(Base):
    __tablename__ = "payment_settings"
    __table_args__ = (UniqueConstraint("setting_key", "is_demo_data", name="uq_payment_settings_key_demo"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    setting_key: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_demo_data: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
