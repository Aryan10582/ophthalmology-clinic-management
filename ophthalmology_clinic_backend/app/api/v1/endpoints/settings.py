from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.prescription_template import PrescriptionTemplate
from app.models.user import User, UserRole
from app.schemas.prescription_template import PrescriptionTemplateRead, PrescriptionTemplateUpdate

router = APIRouter()
doctor_or_admin_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR)


@router.get("/prescription-template", response_model=PrescriptionTemplateRead, dependencies=[Depends(doctor_or_admin_required)])
def get_template(db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> PrescriptionTemplate:
    doctor_id = current_user.id
    template = db.query(PrescriptionTemplate).filter(PrescriptionTemplate.doctor_id == doctor_id).first()
    if template is None:
        template = PrescriptionTemplate(doctor_id=doctor_id, doctor_name=current_user.full_name, clinic_name="Ophthalmology Clinic")
        db.add(template)
        db.commit()
        db.refresh(template)
    return template


@router.put("/prescription-template", response_model=PrescriptionTemplateRead, dependencies=[Depends(doctor_or_admin_required)])
def update_template(payload: PrescriptionTemplateUpdate, db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> PrescriptionTemplate:
    template = db.query(PrescriptionTemplate).filter(PrescriptionTemplate.doctor_id == current_user.id).first()
    if template is None:
        template = PrescriptionTemplate(doctor_id=current_user.id)
    for key, value in payload.model_dump().items():
        setattr(template, key, value)
    db.add(template)
    db.commit()
    db.refresh(template)
    return template
