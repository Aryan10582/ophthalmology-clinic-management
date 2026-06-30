from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.crud.payments import CONSULTATION_FEE_KEY, get_or_create_setting, set_setting, today_income
from app.crud.operations import operation_type_crud
from app.models.payment import PaymentSetting
from app.models.user import UserRole
from app.schemas.operation import OperationTypeRead
from app.schemas.payment import PaymentSettingRead, PaymentSettingUpdate, TodayIncomeRead

router = APIRouter()
doctor_or_admin_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR)


@router.get("/settings", response_model=list[PaymentSettingRead], dependencies=[Depends(doctor_or_admin_required)], summary="Payment settings")
def get_payment_settings(db: Session = Depends(get_db)) -> list[PaymentSetting]:
    get_or_create_setting(db, key=CONSULTATION_FEE_KEY, default_amount=Decimal("500"))
    return list(db.query(PaymentSetting).order_by(PaymentSetting.setting_key.asc()).all())


@router.patch("/settings/{setting_key}", response_model=PaymentSettingRead, dependencies=[Depends(doctor_or_admin_required)], summary="Update payment setting")
def update_payment_setting(setting_key: str, payload: PaymentSettingUpdate, db: Session = Depends(get_db)) -> PaymentSetting:
    return set_setting(db, key=setting_key, amount=payload.amount)


@router.patch("/operation-types/{operation_type_id}/price", response_model=OperationTypeRead, dependencies=[Depends(doctor_or_admin_required)], summary="Update operation price")
def update_operation_price(operation_type_id: int, payload: PaymentSettingUpdate, db: Session = Depends(get_db)):
    operation_type = operation_type_crud.get(db, id=operation_type_id)
    if operation_type is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation type not found")
    operation_type.price = payload.amount
    db.add(operation_type)
    db.commit()
    db.refresh(operation_type)
    return operation_type


@router.get("/today-income", response_model=TodayIncomeRead, dependencies=[Depends(doctor_or_admin_required)], summary="Today's income")
def get_today_income(db: Session = Depends(get_db)) -> TodayIncomeRead:
    consultation_income, operation_income = today_income(db, income_date=date.today())
    return TodayIncomeRead(
        date=date.today().isoformat(),
        consultation_income=consultation_income,
        operation_income=operation_income,
        total_income=consultation_income + operation_income,
    )
