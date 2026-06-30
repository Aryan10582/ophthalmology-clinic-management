import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.payment import PaymentMethod, PaymentStatus


class OperationStatus(str, enum.Enum):
    PLANNED = "planned"
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TestStatus(str, enum.Enum):
    PENDING = "pending"
    DONE = "done"


class FitnessStatus(str, enum.Enum):
    PENDING = "pending"
    FIT = "fit"
    NOT_FIT = "not_fit"


class OperationType(Base):
    __tablename__ = "operation_types"
    __table_args__ = (UniqueConstraint("name", "is_demo_data", name="uq_operation_types_name_demo"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_demo_data: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Operation(Base):
    __tablename__ = "operations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    visit_id: Mapped[int] = mapped_column(ForeignKey("visits.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    operation_type_id: Mapped[int] = mapped_column(ForeignKey("operation_types.id"), nullable=False, index=True)
    operation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[OperationStatus] = mapped_column(Enum(OperationStatus, name="operation_status"), default=OperationStatus.PLANNED, nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    payment_status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus, name="payment_status"), default=PaymentStatus.NOT_PAID, nullable=False)
    payment_method: Mapped[PaymentMethod | None] = mapped_column(Enum(PaymentMethod, name="payment_method"), nullable=True)
    operation_charge: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    patient: Mapped["Patient"] = relationship()
    visit: Mapped["Visit"] = relationship()
    doctor: Mapped["User"] = relationship()
    operation_type: Mapped["OperationType"] = relationship()
    tests: Mapped[list["OperationTest"]] = relationship(back_populates="operation", cascade="all, delete-orphan")


class OperationTest(Base):
    __tablename__ = "operation_tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    operation_id: Mapped[int] = mapped_column(ForeignKey("operations.id", ondelete="CASCADE"), nullable=False, index=True)
    test_name: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[TestStatus] = mapped_column(Enum(TestStatus, name="test_status"), default=TestStatus.PENDING, nullable=False)
    test_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    result: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    fitness_status: Mapped[FitnessStatus | None] = mapped_column(Enum(FitnessStatus, name="fitness_status"), nullable=True)

    operation: Mapped["Operation"] = relationship(back_populates="tests")
    reports: Mapped[list["OperationTestReport"]] = relationship(back_populates="test", cascade="all, delete-orphan")


class OperationTestReport(Base):
    __tablename__ = "operation_test_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    operation_test_id: Mapped[int] = mapped_column(ForeignKey("operation_tests.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    test: Mapped["OperationTest"] = relationship(back_populates="reports")
