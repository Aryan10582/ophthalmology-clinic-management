from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.realtime import realtime_manager
from app.crud.patients import patient_crud
from app.crud.queue import queue_crud
from app.models.queue import QueueEntry
from app.models.visit import Visit
from app.models.user import User, UserRole
from app.schemas.queue import QueueEntryCreate, QueueEntryRead

router = APIRouter()
reception_required = require_roles(UserRole.ADMIN, UserRole.RECEPTIONIST)
doctor_or_admin_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR)
staff_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST)


@router.get("/today", response_model=list[QueueEntryRead], dependencies=[Depends(staff_required)], summary="Get today's queue")
def today_queue(db: Session = Depends(get_db)) -> list[QueueEntry]:
    return queue_crud.get_today_active(db)


@router.get("/completed-today", response_model=list[QueueEntryRead], dependencies=[Depends(staff_required)], summary="Get today's completed consultations")
def completed_today_queue(db: Session = Depends(get_db)) -> list[QueueEntry]:
    entries = queue_crud.get_today_completed(db)
    for entry in entries:
        visit = (
            db.query(Visit)
            .filter(Visit.patient_id == entry.patient_id, Visit.completed_at.isnot(None))
            .order_by(Visit.completed_at.desc())
            .first()
        )
        if visit is not None:
            entry.completed_visit_id = visit.id
            entry.payment_status = visit.payment_status
            entry.payment_method = visit.payment_method
            entry.consultation_fee = visit.consultation_fee
    return entries


@router.post("", response_model=QueueEntryRead, status_code=status.HTTP_201_CREATED, summary="Add patient to queue")
def add_to_queue(
    payload: QueueEntryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(reception_required),
) -> QueueEntry:
    try:
        entry = queue_crud.create_or_reuse_patient_entry(
            db,
            payload=payload,
            receptionist_id=current_user.id,
            patient_create=patient_crud.create,
        )
        background_tasks.add_task(realtime_manager.broadcast, "queue.updated", {"entry_id": entry.id})
        return entry
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/{entry_id}/start", response_model=QueueEntryRead, summary="Start consultation for queue entry")
def start_queue_entry(
    entry_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_or_admin_required),
) -> QueueEntry:
    entry = queue_crud.get(db, id=entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Queue entry not found")
    try:
        entry = queue_crud.start_consultation(db, entry=entry, doctor_id=current_user.id)
        background_tasks.add_task(realtime_manager.broadcast, "queue.updated", {"entry_id": entry.id})
        return entry
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{entry_id}/complete", response_model=QueueEntryRead, dependencies=[Depends(doctor_or_admin_required)], summary="Complete queue entry")
def complete_queue_entry(entry_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> QueueEntry:
    entry = queue_crud.get(db, id=entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Queue entry not found")
    entry = queue_crud.complete(db, entry=entry)
    background_tasks.add_task(realtime_manager.broadcast, "queue.updated", {"entry_id": entry.id})
    return entry
