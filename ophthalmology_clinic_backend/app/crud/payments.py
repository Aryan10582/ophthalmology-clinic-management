from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.operation import Operation
from app.models.payment import PaymentSetting, PaymentStatus
from app.models.visit import Visit

CONSULTATION_FEE_KEY = "consultation_fee"


def get_or_create_setting(db: Session, *, key: str, default_amount: Decimal = Decimal("0")) -> PaymentSetting:
    setting = db.query(PaymentSetting).filter(PaymentSetting.setting_key == key).first()
    if setting is not None:
        return setting
    setting = PaymentSetting(setting_key=key, amount=default_amount)
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


def set_setting(db: Session, *, key: str, amount: Decimal) -> PaymentSetting:
    setting = get_or_create_setting(db, key=key)
    setting.amount = amount
    db.add(setting)
    db.commit()
    db.refresh(setting)
    return setting


def today_income(db: Session, *, income_date: date) -> tuple[Decimal, Decimal]:
    consultation_income = (
        db.query(func.coalesce(func.sum(Visit.consultation_fee), 0))
        .filter(func.date(Visit.completed_at) == income_date, Visit.payment_status == PaymentStatus.PAID)
        .scalar()
    )
    operation_income = (
        db.query(func.coalesce(func.sum(Operation.operation_charge), 0))
        .filter(Operation.operation_date == income_date, Operation.payment_status == PaymentStatus.PAID)
        .scalar()
    )
    return Decimal(str(consultation_income)), Decimal(str(operation_income))
