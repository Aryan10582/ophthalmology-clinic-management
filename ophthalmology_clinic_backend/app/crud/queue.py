from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.patient import Patient
from app.models.queue import QueueEntry, QueueStatus
from app.schemas.patient import PatientCreate
from app.schemas.queue import QueueEntryCreate, QueueEntryUpdate


class CRUDQueue(CRUDBase[QueueEntry, QueueEntryCreate, QueueEntryUpdate]):
    def get_today(self, db: Session) -> list[QueueEntry]:
        return self.get_by_date(db, queue_date=date.today())

    def get_today_active(self, db: Session) -> list[QueueEntry]:
        return list(
            db.query(QueueEntry)
            .filter(QueueEntry.queue_date == date.today(), QueueEntry.status.in_([QueueStatus.WAITING, QueueStatus.IN_CONSULTATION]))
            .order_by(QueueEntry.created_at.asc(), QueueEntry.id.asc())
            .all()
        )

    def get_today_completed(self, db: Session) -> list[QueueEntry]:
        return list(
            db.query(QueueEntry)
            .filter(QueueEntry.queue_date == date.today(), QueueEntry.status == QueueStatus.COMPLETED)
            .order_by(QueueEntry.completed_at.desc(), QueueEntry.id.desc())
            .all()
        )

    def get_active_consultation(self, db: Session) -> QueueEntry | None:
        return (
            db.query(QueueEntry)
            .filter(QueueEntry.queue_date == date.today(), QueueEntry.status == QueueStatus.IN_CONSULTATION)
            .first()
        )

    def get_by_date(self, db: Session, *, queue_date: date) -> list[QueueEntry]:
        return list(
            db.query(QueueEntry)
            .filter(QueueEntry.queue_date == queue_date)
            .order_by(QueueEntry.created_at.asc(), QueueEntry.id.asc())
            .all()
        )

    def get_active_for_patient(self, db: Session, *, patient_id: int, queue_date: date) -> QueueEntry | None:
        return (
            db.query(QueueEntry)
            .filter(
                QueueEntry.patient_id == patient_id,
                QueueEntry.queue_date == queue_date,
                QueueEntry.status.in_([QueueStatus.WAITING, QueueStatus.IN_CONSULTATION]),
            )
            .first()
        )

    def find_patient_match(self, db: Session, *, payload: QueueEntryCreate, is_demo_data: bool = False) -> Patient | None:
        if payload.patient_id:
            patient = db.get(Patient, payload.patient_id)
            return patient if patient is not None and patient.is_demo_data == is_demo_data else None
        if payload.phone:
            match = db.query(Patient).filter(Patient.phone == payload.phone, Patient.is_demo_data == is_demo_data).first()
            if match:
                return match
        if payload.first_name and payload.last_name:
            return (
                db.query(Patient)
                .filter(Patient.first_name.ilike(payload.first_name), Patient.last_name.ilike(payload.last_name), Patient.is_demo_data == is_demo_data)
                .first()
            )
        return None

    def create_or_reuse_patient_entry(
        self,
        db: Session,
        *,
        payload: QueueEntryCreate,
        receptionist_id: int | None,
        patient_create,
        is_demo_data: bool = False,
    ) -> QueueEntry:
        queue_date = payload.queue_date or date.today()
        patient = self.find_patient_match(db, payload=payload, is_demo_data=is_demo_data)
        if patient is None:
            if not all([payload.first_name, payload.last_name, payload.age is not None, payload.gender]):
                raise ValueError("New patient requires first_name, last_name, age and gender")
            patient = patient_create(
                db,
                obj_in=PatientCreate(
                    first_name=payload.first_name,
                    last_name=payload.last_name,
                    age=payload.age,
                    gender=payload.gender,
                    phone=payload.phone,
                    address=payload.address,
                    is_demo_data=is_demo_data,
                ),
            )

        existing = self.get_active_for_patient(db, patient_id=patient.id, queue_date=queue_date)
        if existing is not None:
            return existing

        db_obj = QueueEntry(
            patient_id=patient.id,
            receptionist_id=receptionist_id,
            queue_date=queue_date,
            status=QueueStatus.WAITING,
            reason=payload.reason,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def start_consultation(self, db: Session, *, entry: QueueEntry, doctor_id: int) -> QueueEntry:
        active = self.get_active_consultation(db)
        if active is not None and active.id != entry.id:
            raise ValueError("Another consultation is already active")
        entry.status = QueueStatus.IN_CONSULTATION
        entry.doctor_id = doctor_id
        entry.started_at = datetime.now(UTC)
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    def complete(self, db: Session, *, entry: QueueEntry) -> QueueEntry:
        entry.status = QueueStatus.COMPLETED
        entry.completed_at = datetime.now(UTC)
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry


queue_crud = CRUDQueue(QueueEntry)
