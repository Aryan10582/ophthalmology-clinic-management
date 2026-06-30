import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class SupplyCategory(str, enum.Enum):
    EMERGENCY = "emergency"
    OPERATION = "operation"
    GENERAL = "general"


class MedicalSupply(Base):
    __tablename__ = "medical_supplies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category: Mapped[SupplyCategory] = mapped_column(Enum(SupplyCategory, name="supply_category"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    current_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    unit: Mapped[str] = mapped_column(String(40), nullable=False)
    minimum_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_demo_data: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    batches: Mapped[list["MedicalSupplyBatch"]] = relationship(back_populates="supply", cascade="all, delete-orphan")


class NotificationType(str, enum.Enum):
    LOW_STOCK = "low_stock"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    notification_type: Mapped[NotificationType] = mapped_column(Enum(NotificationType, name="notification_type"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_demo_data: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
