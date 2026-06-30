from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.crud.followups import followup_crud
from app.crud.payments import CONSULTATION_FEE_KEY, get_or_create_setting
from app.crud.patients import patient_crud
from app.crud.queue import queue_crud
from app.crud.suggestions import learn_from_visit
from app.crud.users import user_crud
from app.crud.visits import visit_crud
from app.core.realtime import realtime_manager
from app.models.followup import FollowUpType
from app.models.user import UserRole
from app.models.visit import Visit
from app.schemas.followup import FollowUpCreate
from app.schemas.payment import PaymentUpdate
from app.schemas.visit import VisitCreate, VisitRead, VisitUpdate

router = APIRouter()
doctor_or_admin_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR)
staff_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST)


@router.post("", response_model=VisitRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(doctor_or_admin_required)], summary="Create visit")
def create_visit(payload: VisitCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> Visit:
    patient = patient_crud.get(db, id=payload.patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    doctor = user_crud.get(db, id=payload.doctor_id)
    if doctor is None or doctor.role != UserRole.DOCTOR:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="doctor_id must reference a doctor")

    visit = visit_crud.create(db, obj_in=payload)
    visit.consultation_fee = get_or_create_setting(db, key=CONSULTATION_FEE_KEY).amount
    db.add(visit)
    db.commit()
    db.refresh(visit)
    if payload.follow_up_date:
        followup_crud.create(
            db,
            obj_in=FollowUpCreate(
                patient_id=payload.patient_id,
                doctor_id=payload.doctor_id,
                follow_up_date=payload.follow_up_date,
                follow_up_type=FollowUpType.NORMAL,
                notes="Normal follow-up",
            ),
        )
    learn_from_visit(db, visit=visit)
    background_tasks.add_task(realtime_manager.broadcast, "consultations.updated", {"visit_id": visit.id, "patient_id": visit.patient_id})
    return visit


@router.get("", response_model=list[VisitRead], dependencies=[Depends(doctor_or_admin_required)], summary="List visits")
def list_visits(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> list[Visit]:
    return visit_crud.get_multi(db, skip=skip, limit=limit)


@router.get("/patient/{patient_pk}", response_model=list[VisitRead], dependencies=[Depends(doctor_or_admin_required)], summary="List visits for a patient")
def list_patient_visits(patient_pk: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> list[Visit]:
    if patient_crud.get(db, id=patient_pk) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return visit_crud.get_by_patient(db, patient_id=patient_pk, skip=skip, limit=limit)


@router.get("/{visit_id}", response_model=VisitRead, dependencies=[Depends(doctor_or_admin_required)], summary="Get visit")
def get_visit(visit_id: int, db: Session = Depends(get_db)) -> Visit:
    visit = visit_crud.get(db, id=visit_id)
    if visit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    return visit


@router.patch("/{visit_id}", response_model=VisitRead, dependencies=[Depends(doctor_or_admin_required)], summary="Update visit")
def update_visit(visit_id: int, payload: VisitUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> Visit:
    visit = visit_crud.get(db, id=visit_id)
    if visit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    if payload.patient_id and patient_crud.get(db, id=payload.patient_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    if payload.doctor_id:
        doctor = user_crud.get(db, id=payload.doctor_id)
        if doctor is None or doctor.role != UserRole.DOCTOR:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="doctor_id must reference a doctor")
    visit = visit_crud.update(db, db_obj=visit, obj_in=payload)
    learn_from_visit(db, visit=visit)
    background_tasks.add_task(realtime_manager.broadcast, "consultations.updated", {"visit_id": visit.id, "patient_id": visit.patient_id})
    return visit


@router.post("/{visit_id}/end", response_model=VisitRead, dependencies=[Depends(doctor_or_admin_required)], summary="End consultation")
def end_consultation(visit_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> Visit:
    visit = visit_crud.get(db, id=visit_id)
    if visit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    visit.completed_at = datetime.now(UTC)
    patient = patient_crud.get(db, id=visit.patient_id)
    if patient is not None:
        patient.last_visit_at = visit.completed_at
        db.add(patient)
    active_entry = queue_crud.get_active_for_patient(db, patient_id=visit.patient_id, queue_date=visit.visit_date.date())
    if active_entry is not None:
        queue_crud.complete(db, entry=active_entry)
    db.add(visit)
    db.commit()
    db.refresh(visit)
    learn_from_visit(db, visit=visit)
    background_tasks.add_task(realtime_manager.broadcast, "consultations.completed", {"visit_id": visit.id, "patient_id": visit.patient_id})
    background_tasks.add_task(realtime_manager.broadcast, "queue.updated", {"patient_id": visit.patient_id})
    return visit


@router.patch("/{visit_id}/payment", response_model=VisitRead, dependencies=[Depends(staff_required)], summary="Update consultation payment")
def update_visit_payment(visit_id: int, payload: PaymentUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> Visit:
    visit = visit_crud.get(db, id=visit_id)
    if visit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    visit.payment_status = payload.payment_status
    visit.payment_method = payload.payment_method
    if visit.consultation_fee is None:
        visit.consultation_fee = get_or_create_setting(db, key=CONSULTATION_FEE_KEY).amount
    db.add(visit)
    db.commit()
    db.refresh(visit)
    background_tasks.add_task(realtime_manager.broadcast, "payments.updated", {"visit_id": visit.id, "patient_id": visit.patient_id})
    return visit


@router.put("/{visit_id}", response_model=VisitRead, dependencies=[Depends(doctor_or_admin_required)], summary="Replace visit")
def replace_visit(visit_id: int, payload: VisitCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> Visit:
    visit = visit_crud.get(db, id=visit_id)
    if visit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")

    patient = patient_crud.get(db, id=payload.patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    doctor = user_crud.get(db, id=payload.doctor_id)
    if doctor is None or doctor.role != UserRole.DOCTOR:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="doctor_id must reference a doctor")

    visit = visit_crud.update(db, db_obj=visit, obj_in=payload)
    learn_from_visit(db, visit=visit)
    background_tasks.add_task(realtime_manager.broadcast, "consultations.updated", {"visit_id": visit.id, "patient_id": visit.patient_id})
    return visit
