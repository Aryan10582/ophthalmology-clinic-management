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
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.models.visit import Visit
from app.schemas.followup import FollowUpCreate
from app.schemas.patient import PatientUpdate
from app.schemas.payment import PaymentUpdate
from app.schemas.visit import ConsultationStartCreate, VisitCreate, VisitRead, VisitUpdate

router = APIRouter()
doctor_or_admin_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR)
staff_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST)


@router.post("", response_model=VisitRead, status_code=status.HTTP_201_CREATED, summary="Create visit")
def create_visit(payload: VisitCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> Visit:
    patient = get_scoped_patient_or_404(db, patient_id=payload.patient_id, current_user=current_user)

    doctor = user_crud.get(db, id=payload.doctor_id)
    if doctor is None or doctor.role != UserRole.DOCTOR or doctor.is_demo_account != current_user.is_demo_account:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="doctor_id must reference a doctor")

    visit = visit_crud.create(db, obj_in=payload)
    visit.consultation_fee = get_or_create_setting(db, key=CONSULTATION_FEE_KEY, is_demo_data=current_user.is_demo_account).amount
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


@router.get("", response_model=list[VisitRead], summary="List visits")
def list_visits(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> list[Visit]:
    return list(
        db.query(Visit)
        .join(Patient)
        .filter(Patient.is_demo_data == current_user.is_demo_account)
        .order_by(Visit.visit_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/patient/{patient_pk}", response_model=list[VisitRead], summary="List visits for a patient")
def list_patient_visits(patient_pk: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> list[Visit]:
    get_scoped_patient_or_404(db, patient_id=patient_pk, current_user=current_user)
    return visit_crud.get_by_patient(db, patient_id=patient_pk, skip=skip, limit=limit)


@router.post("/start", response_model=VisitRead, status_code=status.HTTP_201_CREATED, summary="Start consultation from patient intake")
def start_consultation(
    payload: ConsultationStartCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_required),
) -> Visit:
    patient = get_or_create_intake_patient(db, payload=payload, current_user=current_user)
    doctor_id = resolve_consultation_doctor_id(db, payload=payload, current_user=current_user)
    chief_complaint = payload.chief_complaint.strip() if current_user.role in {UserRole.ADMIN, UserRole.DOCTOR} and payload.chief_complaint else "Pending doctor consultation"

    visit = visit_crud.create(
        db,
        obj_in=VisitCreate(
            patient_id=patient.id,
            doctor_id=doctor_id,
            chief_complaint=chief_complaint,
            distance_prescription_enabled=False,
            near_prescription_enabled=False,
        ),
    )
    visit.consultation_fee = get_or_create_setting(db, key=CONSULTATION_FEE_KEY, is_demo_data=current_user.is_demo_account).amount
    db.add(visit)
    db.commit()
    db.refresh(visit)
    background_tasks.add_task(realtime_manager.broadcast, "consultations.updated", {"visit_id": visit.id, "patient_id": visit.patient_id})
    return visit


@router.get("/{visit_id}", response_model=VisitRead, summary="Get visit")
def get_visit(visit_id: int, db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> Visit:
    return get_scoped_visit_or_404(db, visit_id=visit_id, current_user=current_user)


def get_or_create_intake_patient(db: Session, *, payload: ConsultationStartCreate, current_user: User) -> Patient:
    if payload.patient_id is not None:
        patient = get_scoped_patient_or_404(db, patient_id=payload.patient_id, current_user=current_user)
        if payload.patient is not None:
            update_existing_patient_demographics(db, patient=patient, payload=payload)
        return patient

    if payload.patient is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Patient details are required")

    if payload.patient.patient_id:
        existing_by_patient_id = patient_crud.get_by_patient_id(db, patient_id=payload.patient.patient_id)
        if existing_by_patient_id is not None and existing_by_patient_id.is_demo_data == current_user.is_demo_account:
            update_existing_patient_demographics(db, patient=existing_by_patient_id, payload=payload)
            return existing_by_patient_id

    if payload.patient.phone:
        existing_by_phone = db.query(Patient).filter(Patient.phone == payload.patient.phone, Patient.is_demo_data == current_user.is_demo_account).first()
        if existing_by_phone is not None:
            update_existing_patient_demographics(db, patient=existing_by_phone, payload=payload)
            return existing_by_phone

    return patient_crud.create(db, obj_in=payload.patient.model_copy(update={"is_demo_data": current_user.is_demo_account}))


def update_existing_patient_demographics(db: Session, *, patient: Patient, payload: ConsultationStartCreate) -> Patient:
    if payload.patient is None:
        return patient
    patient_update = PatientUpdate(
        first_name=payload.patient.first_name,
        last_name=payload.patient.last_name,
        age=payload.patient.age,
        gender=payload.patient.gender,
        phone=payload.patient.phone,
        address=payload.patient.address,
        occupation=payload.patient.occupation,
        date_of_birth=payload.patient.date_of_birth,
    )
    return patient_crud.update(db, db_obj=patient, obj_in=patient_update)


def resolve_consultation_doctor_id(db: Session, *, payload: ConsultationStartCreate, current_user: User) -> int:
    if current_user.role == UserRole.DOCTOR:
        return current_user.id

    if payload.doctor_id is not None:
        doctor = user_crud.get(db, id=payload.doctor_id)
        if doctor is None or doctor.role != UserRole.DOCTOR or not doctor.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="doctor_id must reference an active doctor")
        return doctor.id

    doctor = (
        db.query(User)
        .filter(
            User.role == UserRole.DOCTOR,
            User.is_active.is_(True),
            User.is_demo_account == current_user.is_demo_account,
        )
        .order_by(User.created_at.asc())
        .first()
    )
    if doctor is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No doctor account is available")
    return doctor.id


def get_scoped_patient_or_404(db: Session, *, patient_id: int, current_user: User) -> Patient:
    patient = db.query(Patient).filter(Patient.id == patient_id, Patient.is_demo_data == current_user.is_demo_account).first()
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


def get_scoped_visit_or_404(db: Session, *, visit_id: int, current_user: User) -> Visit:
    visit = (
        db.query(Visit)
        .join(Patient)
        .filter(Visit.id == visit_id, Patient.is_demo_data == current_user.is_demo_account)
        .first()
    )
    if visit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    return visit


@router.patch("/{visit_id}", response_model=VisitRead, summary="Update visit")
def update_visit(visit_id: int, payload: VisitUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> Visit:
    visit = get_scoped_visit_or_404(db, visit_id=visit_id, current_user=current_user)
    if payload.patient_id:
        get_scoped_patient_or_404(db, patient_id=payload.patient_id, current_user=current_user)
    if payload.doctor_id:
        doctor = user_crud.get(db, id=payload.doctor_id)
        if doctor is None or doctor.role != UserRole.DOCTOR or doctor.is_demo_account != current_user.is_demo_account:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="doctor_id must reference a doctor")
    visit = visit_crud.update(db, db_obj=visit, obj_in=payload)
    learn_from_visit(db, visit=visit)
    background_tasks.add_task(realtime_manager.broadcast, "consultations.updated", {"visit_id": visit.id, "patient_id": visit.patient_id})
    return visit


@router.post("/{visit_id}/end", response_model=VisitRead, summary="End consultation")
def end_consultation(visit_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> Visit:
    visit = get_scoped_visit_or_404(db, visit_id=visit_id, current_user=current_user)
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


@router.patch("/{visit_id}/payment", response_model=VisitRead, summary="Update consultation payment")
def update_visit_payment(visit_id: int, payload: PaymentUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(staff_required)) -> Visit:
    visit = get_scoped_visit_or_404(db, visit_id=visit_id, current_user=current_user)
    visit.payment_status = payload.payment_status
    visit.payment_method = payload.payment_method
    if visit.consultation_fee is None:
        visit.consultation_fee = get_or_create_setting(db, key=CONSULTATION_FEE_KEY, is_demo_data=current_user.is_demo_account).amount
    db.add(visit)
    db.commit()
    db.refresh(visit)
    background_tasks.add_task(realtime_manager.broadcast, "payments.updated", {"visit_id": visit.id, "patient_id": visit.patient_id})
    return visit


@router.put("/{visit_id}", response_model=VisitRead, summary="Replace visit")
def replace_visit(visit_id: int, payload: VisitCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> Visit:
    visit = get_scoped_visit_or_404(db, visit_id=visit_id, current_user=current_user)

    get_scoped_patient_or_404(db, patient_id=payload.patient_id, current_user=current_user)

    doctor = user_crud.get(db, id=payload.doctor_id)
    if doctor is None or doctor.role != UserRole.DOCTOR or doctor.is_demo_account != current_user.is_demo_account:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="doctor_id must reference a doctor")

    visit = visit_crud.update(db, db_obj=visit, obj_in=payload)
    learn_from_visit(db, visit=visit)
    background_tasks.add_task(realtime_manager.broadcast, "consultations.updated", {"visit_id": visit.id, "patient_id": visit.patient_id})
    return visit
