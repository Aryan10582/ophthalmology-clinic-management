from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.crud.patients import patient_crud
from app.models.patient import Patient
from app.models.user import UserRole
from app.schemas.patient import PatientCreate, PatientRead, PatientUpdate

router = APIRouter()
clinical_staff_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST)
doctor_or_admin_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR)


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(clinical_staff_required)], summary="Create patient")
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)) -> Patient:
    return patient_crud.create(db, obj_in=payload)


@router.get("", response_model=list[PatientRead], dependencies=[Depends(clinical_staff_required)], summary="List patients")
def list_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> list[Patient]:
    return patient_crud.get_multi(db, skip=skip, limit=limit)


@router.get("/{patient_pk}", response_model=PatientRead, dependencies=[Depends(clinical_staff_required)], summary="Get patient")
def get_patient(patient_pk: int, db: Session = Depends(get_db)) -> Patient:
    patient = patient_crud.get(db, id=patient_pk)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient


@router.patch("/{patient_pk}", response_model=PatientRead, dependencies=[Depends(clinical_staff_required)], summary="Update patient demographics")
def update_patient(patient_pk: int, payload: PatientUpdate, db: Session = Depends(get_db)) -> Patient:
    patient = patient_crud.get(db, id=patient_pk)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient_crud.update(db, db_obj=patient, obj_in=payload)


@router.delete("/{patient_pk}", response_model=PatientRead, dependencies=[Depends(doctor_or_admin_required)], summary="Delete patient")
def delete_patient(patient_pk: int, db: Session = Depends(get_db)) -> Patient:
    patient = patient_crud.remove(db, id=patient_pk)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient
