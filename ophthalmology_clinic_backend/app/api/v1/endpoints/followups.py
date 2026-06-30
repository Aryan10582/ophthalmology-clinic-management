from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.crud.followups import followup_crud
from app.crud.patients import patient_crud
from app.models.followup import FollowUp
from app.models.user import UserRole
from app.schemas.followup import FollowUpCreate, FollowUpRead, FollowUpUpdate

router = APIRouter()
doctor_or_admin_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR)
staff_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST)


@router.get("", response_model=list[FollowUpRead], dependencies=[Depends(staff_required)], summary="List follow-ups")
def list_followups(db: Session = Depends(get_db)) -> list[FollowUp]:
    return followup_crud.get_upcoming(db)


@router.post("", response_model=FollowUpRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(doctor_or_admin_required)], summary="Create follow-up")
def create_followup(payload: FollowUpCreate, db: Session = Depends(get_db)) -> FollowUp:
    if patient_crud.get(db, id=payload.patient_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return followup_crud.create(db, obj_in=payload)


@router.patch("/{followup_id}", response_model=FollowUpRead, dependencies=[Depends(doctor_or_admin_required)], summary="Update follow-up")
def update_followup(followup_id: int, payload: FollowUpUpdate, db: Session = Depends(get_db)) -> FollowUp:
    followup = followup_crud.get(db, id=followup_id)
    if followup is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow-up not found")
    return followup_crud.update(db, db_obj=followup, obj_in=payload)
