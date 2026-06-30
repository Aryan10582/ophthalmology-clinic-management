from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.operation import Operation
from app.models.patient import Patient
from app.models.payment import PaymentSetting, PaymentStatus
from app.models.visit import Visit

CONSULTATION_FEE_KEY = "consultation_fee"


def get_or_create_setting(db: Session, *, key: str, default_amount: Decimal = Decimal("0"), is_demo_data: bool = False) -> PaymentSetting:
    setting = db.query(PaymentSetting).filter(PaymentSetting.setting_key == key, PaymentSetting.is_demo_data == is_demo_data).first()
    if setting is not None:
        return setting
    setting = PaymentSetting(setting_key=key, amount=default_amount, is_demo_data=is_demo_data)
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


def set_setting(db: Session, *, key: str, amount: Decimal, is_demo_data: bool = False) -> PaymentSetting:
    setting = get_or_create_setting(db, key=key, is_demo_data=is_demo_data)
    setting.amount = amount
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


def today_income(db: Session, *, income_date: date, is_demo_data: bool = False) -> tuple[Decimal, Decimal]:
    consultation_income = (
        db.query(func.coalesce(func.sum(Visit.consultation_fee), 0))
        .join(Patient)
        .filter(func.date(Visit.completed_at) == income_date, Visit.payment_status == PaymentStatus.PAID, Patient.is_demo_data == is_demo_data)
        .scalar()
    )
    operation_income = (
        db.query(func.coalesce(func.sum(Operation.operation_charge), 0))
        .join(Patient)
        .filter(Operation.operation_date == income_date, Operation.payment_status == PaymentStatus.PAID, Patient.is_demo_data == is_demo_data)
        .scalar()
    )
    return Decimal(str(consultation_income)), Decimal(str(operation_income))
