from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate


class CRUDPatient(CRUDBase[Patient, PatientCreate, PatientUpdate]):
    def get_by_patient_id(self, db: Session, *, patient_id: str) -> Patient | None:
        return db.query(Patient).filter(Patient.patient_id == patient_id).first()

    def generate_patient_id(self, db: Session) -> str:
        last_patient = db.query(Patient).order_by(Patient.id.desc()).first()
        next_number = 1 if last_patient is None else last_patient.id + 1
        patient_id = f"OP-{next_number:06d}"
        while self.get_by_patient_id(db, patient_id=patient_id) is not None:
            next_number += 1
            patient_id = f"OP-{next_number:06d}"
        return patient_id

    def create(self, db: Session, *, obj_in: PatientCreate) -> Patient:
        data = obj_in.model_dump()
        data["patient_id"] = self.generate_patient_id(db)
        db_obj = Patient(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


patient_crud = CRUDPatient(Patient)
