from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, require_roles
from app.core.realtime import realtime_manager
from app.crud.patients import patient_crud
from app.crud.queue import queue_crud
from app.models.patient import Patient
from app.models.queue import QueueEntry, QueueStatus
from app.models.visit import Visit
from app.models.user import User, UserRole
from app.models.payment import PaymentMethod, PaymentStatus
from app.schemas.payment import TodayIncomeRead
from app.schemas.queue import QueueEntryCreate, QueueEntryRead

router = APIRouter()
reception_required = require_roles(UserRole.ADMIN, UserRole.RECEPTIONIST)
doctor_or_admin_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR)
staff_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST)


@router.get("/today", response_model=list[QueueEntryRead], summary="Get today's queue")
def today_queue(db: Session = Depends(get_db), current_user: User = Depends(staff_required)) -> list[QueueEntry]:
    return list(
        db.query(QueueEntry)
        .join(Patient)
        .filter(
            QueueEntry.queue_date == date.today(),
            QueueEntry.status.in_([QueueStatus.WAITING, QueueStatus.IN_CONSULTATION]),
            Patient.is_demo_data == current_user.is_demo_account,
        )
        .order_by(QueueEntry.created_at.asc(), QueueEntry.id.asc())
        .all()
    )


@router.get("/completed-today", response_model=list[QueueEntryRead], summary="Get today's completed consultations")
def completed_today_queue(db: Session = Depends(get_db), current_user: User = Depends(staff_required)) -> list["CompletedConsultationEntry"]:
    return completed_consultation_entries(db, current_user=current_user)


@router.get("/today-income", response_model=TodayIncomeRead, summary="Today's completed queue consultation income")
def queue_today_income(db: Session = Depends(get_db), current_user: User = Depends(staff_required)) -> TodayIncomeRead:
    entries = completed_consultation_entries(db, current_user=current_user)
    total = sum(
        (Decimal(str(entry.consultation_fee or 0)) for entry in entries if entry.payment_status == PaymentStatus.PAID),
        Decimal("0"),
    )
    return TodayIncomeRead(
        date=date.today().isoformat(),
        consultation_income=total,
        operation_income=Decimal("0"),
        total_income=total,
    )


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
            is_demo_data=current_user.is_demo_account,
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
    if entry is None or entry.patient is None or entry.patient.is_demo_data != current_user.is_demo_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Queue entry not found")
    try:
        entry = queue_crud.start_consultation(db, entry=entry, doctor_id=current_user.id)
        background_tasks.add_task(realtime_manager.broadcast, "queue.updated", {"entry_id": entry.id})
        return entry
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{entry_id}/complete", response_model=QueueEntryRead, summary="Complete queue entry")
def complete_queue_entry(entry_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> QueueEntry:
    entry = queue_crud.get(db, id=entry_id)
    if entry is None or entry.patient is None or entry.patient.is_demo_data != current_user.is_demo_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Queue entry not found")
    entry = queue_crud.complete(db, entry=entry)
    background_tasks.add_task(realtime_manager.broadcast, "queue.updated", {"entry_id": entry.id})
    return entry


@dataclass
class CompletedConsultationEntry:
    id: int
    patient_id: int
    receptionist_id: int | None
    doctor_id: int | None
    queue_date: date
    status: QueueStatus
    reason: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    completed_visit_id: int
    payment_status: PaymentStatus
    payment_method: PaymentMethod | None
    consultation_fee: Decimal | None
    patient: Patient | None
    receptionist: User | None
    doctor: User | None


def completed_consultation_entries(db: Session, *, current_user: User) -> list[CompletedConsultationEntry]:
    visits = (
        db.query(Visit)
        .options(joinedload(Visit.patient), joinedload(Visit.doctor))
        .join(Patient)
        .filter(
            Visit.completed_at.isnot(None),
            func.date(Visit.completed_at) == date.today(),
            Patient.is_demo_data == current_user.is_demo_account,
        )
        .order_by(Visit.completed_at.desc(), Visit.id.desc())
        .all()
    )
    return [completed_entry_from_visit(db, visit=visit) for visit in visits]


def completed_entry_from_visit(db: Session, *, visit: Visit) -> CompletedConsultationEntry:
    queue_entry = matching_queue_entry_for_visit(db, visit=visit)
    completed_date = visit.completed_at.date() if visit.completed_at is not None else date.today()
    return CompletedConsultationEntry(
        id=visit.id,
        patient_id=visit.patient_id,
        receptionist_id=queue_entry.receptionist_id if queue_entry is not None else None,
        doctor_id=visit.doctor_id,
        queue_date=queue_entry.queue_date if queue_entry is not None else completed_date,
        status=QueueStatus.COMPLETED,
        reason=queue_entry.reason if queue_entry is not None else visit.chief_complaint,
        created_at=queue_entry.created_at if queue_entry is not None else visit.visit_date,
        started_at=queue_entry.started_at if queue_entry is not None else visit.visit_date,
        completed_at=visit.completed_at,
        completed_visit_id=visit.id,
        payment_status=visit.payment_status,
        payment_method=visit.payment_method,
        consultation_fee=visit.consultation_fee,
        patient=visit.patient,
        receptionist=queue_entry.receptionist if queue_entry is not None else None,
        doctor=visit.doctor,
    )


def matching_queue_entry_for_visit(db: Session, *, visit: Visit) -> QueueEntry | None:
    completed_date = visit.completed_at.date() if visit.completed_at is not None else visit.visit_date.date()
    query = (
        db.query(QueueEntry)
        .options(joinedload(QueueEntry.receptionist))
        .filter(
            QueueEntry.patient_id == visit.patient_id,
            QueueEntry.queue_date == completed_date,
        )
    )
    return query.order_by(QueueEntry.completed_at.desc().nullslast(), QueueEntry.id.desc()).first()
