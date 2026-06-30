from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.crud.supplies import supply_crud
from app.core.realtime import realtime_manager
from app.models.supply import MedicalSupply, Notification, NotificationType
from app.models.supply_batch import MedicalSupplyBatch
from app.models.user import UserRole
from app.schemas.supply_batch import MedicalSupplyBatchCreate, MedicalSupplyBatchRead, MedicalSupplyConsume
from app.schemas.supply import MedicalSupplyCreate, MedicalSupplyRead, MedicalSupplyUpdate, NotificationRead

router = APIRouter()
staff_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST)
doctor_or_admin_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR)


@router.get("", response_model=list[MedicalSupplyRead], dependencies=[Depends(staff_required)], summary="List medical supplies")
def list_supplies(db: Session = Depends(get_db)) -> list[MedicalSupply]:
    supplies = supply_crud.get_multi(db, limit=500)
    for supply in supplies:
        decorate_supply(supply)
    return supplies


@router.post("", response_model=MedicalSupplyRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(staff_required)], summary="Create medical supply")
def create_supply(payload: MedicalSupplyCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> MedicalSupply:
    supply = supply_crud.create(db, obj_in=payload)
    decorate_supply(supply)
    background_tasks.add_task(realtime_manager.broadcast, "supplies.updated", {"supply_id": supply.id})
    return supply


@router.patch("/{supply_id}", response_model=MedicalSupplyRead, dependencies=[Depends(staff_required)], summary="Update medical supply")
def update_supply(supply_id: int, payload: MedicalSupplyUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> MedicalSupply:
    supply = supply_crud.get(db, id=supply_id)
    if supply is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supply not found")
    supply = supply_crud.update(db, db_obj=supply, obj_in=payload)
    decorate_supply(supply)
    create_expiry_notification(db, supply=supply)
    background_tasks.add_task(realtime_manager.broadcast, "supplies.updated", {"supply_id": supply.id})
    return supply


@router.post("/{supply_id}/batches", response_model=MedicalSupplyBatchRead, dependencies=[Depends(staff_required)], summary="Add inventory batch")
def add_batch(supply_id: int, payload: MedicalSupplyBatchCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> MedicalSupplyBatch:
    supply = supply_crud.get(db, id=supply_id)
    if supply is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supply not found")
    batch = MedicalSupplyBatch(
        supply_id=supply_id,
        batch_code=payload.batch_code,
        quantity_initial=payload.quantity,
        quantity_remaining=payload.quantity,
        expiry_date=payload.expiry_date,
        purchase_date=payload.purchase_date,
        notes=payload.notes,
    )
    supply.current_stock += payload.quantity
    supply.expiry_date = earliest_expiry(db, supply_id=supply_id, pending_batch=batch)
    db.add(batch)
    db.add(supply)
    db.commit()
    db.refresh(batch)
    decorate_batch(batch)
    create_expiry_notification(db, supply=supply)
    background_tasks.add_task(realtime_manager.broadcast, "supplies.updated", {"supply_id": supply_id})
    return batch


@router.post("/{supply_id}/consume", response_model=MedicalSupplyRead, dependencies=[Depends(staff_required)], summary="Consume stock by FEFO")
def consume_stock(supply_id: int, payload: MedicalSupplyConsume, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> MedicalSupply:
    supply = supply_crud.get(db, id=supply_id)
    if supply is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Supply not found")
    remaining = payload.quantity
    batches = (
        db.query(MedicalSupplyBatch)
        .filter(MedicalSupplyBatch.supply_id == supply_id, MedicalSupplyBatch.quantity_remaining > 0)
        .order_by(MedicalSupplyBatch.expiry_date.asc(), MedicalSupplyBatch.purchase_date.asc())
        .all()
    )
    if sum(batch.quantity_remaining for batch in batches) < remaining:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Insufficient stock")
    for batch in batches:
        if remaining <= 0:
            break
        used = min(batch.quantity_remaining, remaining)
        batch.quantity_remaining -= used
        remaining -= used
        db.add(batch)
    supply.current_stock = max(0, supply.current_stock - payload.quantity)
    supply.expiry_date = earliest_expiry(db, supply_id=supply_id)
    db.add(supply)
    db.commit()
    db.refresh(supply)
    decorate_supply(supply)
    background_tasks.add_task(realtime_manager.broadcast, "supplies.updated", {"supply_id": supply_id})
    return supply


@router.delete(
    "/batches/{batch_id}",
    response_model=MedicalSupplyBatchRead,
    dependencies=[Depends(doctor_or_admin_required)],
    summary="Delete inventory batch",
)
def delete_batch(batch_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> MedicalSupplyBatchRead:
    batch = db.get(MedicalSupplyBatch, batch_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    supply = batch.supply
    supply_id = batch.supply_id
    decorate_batch(batch)
    deleted_batch = MedicalSupplyBatchRead.model_validate(batch)
    db.delete(batch)
    db.flush()
    supply.current_stock = sum(
        row[0]
        for row in db.query(MedicalSupplyBatch.quantity_remaining)
        .filter(MedicalSupplyBatch.supply_id == supply_id, MedicalSupplyBatch.quantity_remaining > 0)
        .all()
    )
    supply.expiry_date = earliest_expiry(db, supply_id=supply_id)
    db.add(supply)
    db.commit()
    background_tasks.add_task(realtime_manager.broadcast, "supplies.updated", {"supply_id": supply_id})
    return deleted_batch


@router.get("/notifications", response_model=list[NotificationRead], dependencies=[Depends(staff_required)], summary="Notifications")
def list_notifications(db: Session = Depends(get_db)) -> list[Notification]:
    return list(db.query(Notification).order_by(Notification.created_at.desc()).limit(100).all())


def decorate_supply(supply: MedicalSupply) -> None:
    total = sum(batch.quantity_remaining for batch in supply.batches) if supply.batches else supply.current_stock
    supply.current_stock = total
    supply.is_low_stock = total < supply.minimum_stock
    supply.days_to_expiry = None
    supply.expiry_status = "not_tracked"
    active_batches = [batch for batch in supply.batches if batch.quantity_remaining > 0]
    for batch in supply.batches:
        decorate_batch(batch)
    if active_batches:
        supply.expiry_date = min(batch.expiry_date for batch in active_batches)
    if supply.expiry_date is None:
        return
    days = (supply.expiry_date - date.today()).days
    supply.days_to_expiry = days
    if days < 0:
        supply.expiry_status = "expired"
    elif days <= 90:
        supply.expiry_status = "expiring_soon"
    else:
        supply.expiry_status = "safe"


def decorate_batch(batch: MedicalSupplyBatch) -> None:
    days = (batch.expiry_date - date.today()).days
    batch.days_to_expiry = days
    if days < 0:
        batch.expiry_status = "expired"
    elif days <= 90:
        batch.expiry_status = "expiring_soon"
    else:
        batch.expiry_status = "safe"


def earliest_expiry(db: Session, *, supply_id: int, pending_batch: MedicalSupplyBatch | None = None):
    expiries = [
        row[0]
        for row in db.query(MedicalSupplyBatch.expiry_date)
        .filter(MedicalSupplyBatch.supply_id == supply_id, MedicalSupplyBatch.quantity_remaining > 0)
        .all()
    ]
    if pending_batch is not None and pending_batch.quantity_remaining > 0:
        expiries.append(pending_batch.expiry_date)
    return min(expiries) if expiries else None


def create_expiry_notification(db: Session, *, supply: MedicalSupply) -> None:
    if supply.expiry_date is None:
        return
    days = (supply.expiry_date - date.today()).days
    if days > 90:
        return
    title = "Medical Supply Expired" if days < 0 else "Medical Supply Near Expiry"
    if days < 0:
        message = f"{supply.name} expired on {supply.expiry_date.isoformat()}"
    else:
        message = f"{supply.name} expires in {days} days"
    exists = db.query(Notification).filter(Notification.title == title, Notification.message == message).first()
    if exists:
        return
    db.add(Notification(notification_type=NotificationType.LOW_STOCK, title=title, message=message))
    db.commit()
