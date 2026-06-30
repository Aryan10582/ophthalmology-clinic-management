from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.crud.patients import patient_crud
from app.crud.operations import operation_crud
from app.crud.visits import visit_crud
from app.models.followup import FollowUp
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.patient_history import PatientHistoryRead
from app.schemas.patient import PatientCreate, PatientRead, PatientUpdate

router = APIRouter()
clinical_staff_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST)
doctor_or_admin_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR)


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED, summary="Create patient")
def create_patient(payload: PatientCreate, db: Session = Depends(get_db), current_user: User = Depends(clinical_staff_required)) -> Patient:
    payload = payload.model_copy(update={"is_demo_data": current_user.is_demo_account})
    return patient_crud.create(db, obj_in=payload)


@router.get("", response_model=list[PatientRead], summary="List patients")
def list_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(clinical_staff_required)) -> list[Patient]:
    return list(patient_scope_query(db, current_user=current_user).offset(skip).limit(limit).all())


@router.get("/search", response_model=list[PatientRead], summary="Search patients by name, phone, or patient ID")
def search_patients(q: str, limit: int = 10, db: Session = Depends(get_db), current_user: User = Depends(clinical_staff_required)) -> list[Patient]:
    term = q.strip()
    if len(term) < 2:
        return []
    pattern = f"%{term}%"
    full_name = Patient.first_name + " " + Patient.last_name
    return list(
        patient_scope_query(db, current_user=current_user)
        .filter(
            or_(
                Patient.patient_id.ilike(pattern),
                Patient.phone.ilike(pattern),
                Patient.first_name.ilike(pattern),
                Patient.last_name.ilike(pattern),
                full_name.ilike(pattern),
            )
        )
        .order_by(Patient.last_visit_at.desc().nullslast(), Patient.created_at.desc())
        .limit(min(limit, 25))
        .all()
    )


@router.get("/{patient_pk}", response_model=PatientRead, summary="Get patient")
def get_patient(patient_pk: int, db: Session = Depends(get_db), current_user: User = Depends(clinical_staff_required)) -> Patient:
    return get_patient_or_404(db, patient_pk=patient_pk, current_user=current_user)


@router.get("/{patient_pk}/history", response_model=PatientHistoryRead, summary="Get patient clinical history")
def get_patient_history(patient_pk: int, db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> PatientHistoryRead:
    get_patient_or_404(db, patient_pk=patient_pk, current_user=current_user)
    return PatientHistoryRead(
        consultations=visit_crud.get_by_patient(db, patient_id=patient_pk, limit=20),
        operations=[operation_crud.with_ready_flag(operation) for operation in operation_crud.get_by_patient(db, patient_id=patient_pk, limit=20)],
        followups=list(db.query(FollowUp).filter(FollowUp.patient_id == patient_pk).order_by(FollowUp.follow_up_date.desc()).limit(20).all()),
    )


@router.patch("/{patient_pk}", response_model=PatientRead, summary="Update patient demographics")
def update_patient(patient_pk: int, payload: PatientUpdate, db: Session = Depends(get_db), current_user: User = Depends(clinical_staff_required)) -> Patient:
    patient = get_patient_or_404(db, patient_pk=patient_pk, current_user=current_user)
    return patient_crud.update(db, db_obj=patient, obj_in=payload)


@router.delete("/{patient_pk}", response_model=PatientRead, summary="Delete patient")
def delete_patient(patient_pk: int, db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> Patient:
    get_patient_or_404(db, patient_pk=patient_pk, current_user=current_user)
    patient = patient_crud.remove(db, id=patient_pk)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


def patient_scope_query(db: Session, *, current_user: User):
    return db.query(Patient).filter(Patient.is_demo_data == current_user.is_demo_account)


def get_patient_or_404(db: Session, *, patient_pk: int, current_user: User) -> Patient:
    patient = patient_scope_query(db, current_user=current_user).filter(Patient.id == patient_pk).first()
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient
