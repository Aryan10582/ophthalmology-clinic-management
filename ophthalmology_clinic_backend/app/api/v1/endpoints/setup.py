from fastapi import APIRouter, Depends, HTTPException, status
from pathlib import Path
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.security import get_password_hash
from app.models.expense import Expense
from app.models.followup import FollowUp
from app.models.operation import Operation, OperationTest, OperationTestReport, OperationType
from app.models.patient import Patient
from app.models.payment import PaymentSetting
from app.models.prescription_template import PrescriptionTemplate
from app.models.queue import QueueEntry
from app.models.suggestion import ConsultationSuggestion
from app.models.supply import MedicalSupply, Notification
from app.models.supply_batch import MedicalSupplyBatch
from app.models.user import User, UserRole
from app.models.visit import Visit
from app.schemas.setup import ClinicSetupCreate, ClinicSetupRead, ReceptionistCreate, ReceptionistUpdate, SetupStatus
from app.schemas.user import UserRead

router = APIRouter()
doctor_required = require_roles(UserRole.DOCTOR)


@router.get("/status", response_model=SetupStatus, summary="Check first-time clinic setup status")
def setup_status(db: Session = Depends(get_db)) -> SetupStatus:
    return SetupStatus(needs_setup=not doctor_exists(db))


@router.post("", response_model=ClinicSetupRead, status_code=status.HTTP_201_CREATED, summary="Complete first-time clinic setup")
def complete_setup(payload: ClinicSetupCreate, db: Session = Depends(get_db)) -> ClinicSetupRead:
    if doctor_exists(db):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Clinic setup has already been completed")

    clear_demo_clinic_data(db)

    usernames = [payload.doctor.username.lower()] + [item.username.lower() for item in payload.receptionists]
    for username in usernames:
        if username_exists(db, username=username):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Username already exists: {username}")

    doctor = User(
        full_name=payload.doctor.doctor_name,
        username=payload.doctor.username.lower(),
        email=account_email(payload.doctor.username),
        password_hash=get_password_hash(payload.doctor.password),
        role=UserRole.DOCTOR,
        is_active=True,
        is_demo_account=False,
    )
    db.add(doctor)
    db.flush()

    for receptionist in payload.receptionists:
        db.add(
            User(
                full_name=receptionist.username,
                username=receptionist.username.lower(),
                email=account_email(receptionist.username),
                password_hash=get_password_hash(receptionist.password),
                role=UserRole.RECEPTIONIST,
                is_active=True,
                is_demo_account=False,
            )
        )

    db.add(
        PrescriptionTemplate(
            doctor_id=doctor.id,
            template_name="professional_blue",
            doctor_name=payload.doctor.doctor_name,
            doctor_qualifications=payload.clinic.doctor_qualifications,
            doctor_registration_number=payload.clinic.doctor_registration_number,
            clinic_name=payload.clinic.clinic_name,
            clinic_address=payload.clinic.clinic_address,
            clinic_phone=payload.clinic.clinic_phone,
            clinic_timings=payload.clinic.clinic_timings,
            email=str(payload.clinic.email),
            website=payload.clinic.website,
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Clinic setup could not be completed because a username already exists") from None
    db.refresh(doctor)
    return ClinicSetupRead(doctor_id=doctor.id, receptionist_count=len(payload.receptionists))


@router.get("/receptionists", response_model=list[UserRead], dependencies=[Depends(doctor_required)], summary="List receptionist accounts")
def list_receptionists(db: Session = Depends(get_db)) -> list[User]:
    return db.query(User).filter(User.role == UserRole.RECEPTIONIST, User.is_active.is_(True)).order_by(User.created_at.desc()).all()


@router.post("/receptionists", response_model=UserRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(doctor_required)], summary="Create receptionist account")
def create_receptionist(payload: ReceptionistCreate, db: Session = Depends(get_db)) -> User:
    username = payload.username.lower()
    if username_exists(db, username=username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
    receptionist = User(
        full_name=payload.username,
        username=username,
        email=account_email(payload.username),
        password_hash=get_password_hash(payload.password),
        role=UserRole.RECEPTIONIST,
        is_active=True,
    )
    db.add(receptionist)
    db.commit()
    db.refresh(receptionist)
    return receptionist


@router.patch("/receptionists/{receptionist_id}", response_model=UserRead, dependencies=[Depends(doctor_required)], summary="Update receptionist account")
def update_receptionist(receptionist_id: int, payload: ReceptionistUpdate, db: Session = Depends(get_db)) -> User:
    receptionist = get_receptionist_or_404(db, receptionist_id=receptionist_id)
    if payload.username is not None:
        username = payload.username.lower()
        existing = db.query(User).filter(User.username == username, User.id != receptionist.id).first()
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")
        receptionist.username = username
        receptionist.email = account_email(username)
        receptionist.full_name = username
    if payload.password is not None:
        receptionist.password_hash = get_password_hash(payload.password)
    if payload.is_active is not None:
        receptionist.is_active = payload.is_active
    db.add(receptionist)
    db.commit()
    db.refresh(receptionist)
    return receptionist


@router.delete("/receptionists/{receptionist_id}", response_model=UserRead, dependencies=[Depends(doctor_required)], summary="Delete receptionist account")
def delete_receptionist(receptionist_id: int, db: Session = Depends(get_db)) -> User:
    receptionist = get_receptionist_or_404(db, receptionist_id=receptionist_id)
    receptionist.is_active = False
    db.add(receptionist)
    db.commit()
    db.refresh(receptionist)
    return receptionist


def doctor_exists(db: Session) -> bool:
    return (
        db.query(User.id)
        .filter(
            User.role == UserRole.DOCTOR,
            User.is_demo_account.is_(False),
        )
        .first()
        is not None
    )


def clear_demo_clinic_data(db: Session) -> None:
    demo_patient_ids = [row[0] for row in db.query(Patient.id).filter(Patient.is_demo_data.is_(True)).all()]
    demo_user_ids = [row[0] for row in db.query(User.id).filter(User.is_demo_account.is_(True)).all()]
    demo_supply_ids = [row[0] for row in db.query(MedicalSupply.id).filter(MedicalSupply.is_demo_data.is_(True)).all()]
    demo_operation_type_ids = [row[0] for row in db.query(OperationType.id).filter(OperationType.is_demo_data.is_(True)).all()]
    demo_operation_ids = [row[0] for row in db.query(Operation.id).filter(Operation.patient_id.in_(demo_patient_ids)).all()] if demo_patient_ids else []
    demo_test_ids = [row[0] for row in db.query(OperationTest.id).filter(OperationTest.operation_id.in_(demo_operation_ids)).all()] if demo_operation_ids else []

    if demo_test_ids:
        for report in db.query(OperationTestReport).filter(OperationTestReport.operation_test_id.in_(demo_test_ids)).all():
            path = Path(report.file_path)
            if path.exists():
                path.unlink()
        db.query(OperationTestReport).filter(OperationTestReport.operation_test_id.in_(demo_test_ids)).delete(synchronize_session=False)
    if demo_operation_ids:
        db.query(OperationTest).filter(OperationTest.operation_id.in_(demo_operation_ids)).delete(synchronize_session=False)
        db.query(FollowUp).filter(FollowUp.operation_id.in_(demo_operation_ids)).delete(synchronize_session=False)
        db.query(Operation).filter(Operation.id.in_(demo_operation_ids)).delete(synchronize_session=False)
    if demo_patient_ids:
        db.query(FollowUp).filter(FollowUp.patient_id.in_(demo_patient_ids)).delete(synchronize_session=False)
        db.query(QueueEntry).filter(QueueEntry.patient_id.in_(demo_patient_ids)).delete(synchronize_session=False)
        db.query(Visit).filter(Visit.patient_id.in_(demo_patient_ids)).delete(synchronize_session=False)
        db.query(Patient).filter(Patient.id.in_(demo_patient_ids)).delete(synchronize_session=False)
    if demo_supply_ids:
        db.query(MedicalSupplyBatch).filter(MedicalSupplyBatch.supply_id.in_(demo_supply_ids)).delete(synchronize_session=False)
        db.query(MedicalSupply).filter(MedicalSupply.id.in_(demo_supply_ids)).delete(synchronize_session=False)
    db.query(Notification).filter(Notification.is_demo_data.is_(True)).delete(synchronize_session=False)
    db.query(Expense).filter(Expense.is_demo_data.is_(True)).delete(synchronize_session=False)
    if demo_user_ids:
        db.query(ConsultationSuggestion).filter(ConsultationSuggestion.doctor_id.in_(demo_user_ids)).delete(synchronize_session=False)
        db.query(PrescriptionTemplate).filter(PrescriptionTemplate.doctor_id.in_(demo_user_ids)).delete(synchronize_session=False)
    if demo_operation_type_ids:
        db.query(OperationType).filter(OperationType.id.in_(demo_operation_type_ids)).delete(synchronize_session=False)
    db.query(PaymentSetting).filter(PaymentSetting.is_demo_data.is_(True)).delete(synchronize_session=False)
    db.query(User).filter(User.is_demo_account.is_(True)).delete(synchronize_session=False)


def username_exists(db: Session, *, username: str) -> bool:
    normalized = username.lower()
    return (
        db.query(User.id)
        .filter((User.username == normalized) | (User.email == account_email(normalized)))
        .first()
        is not None
    )


def get_receptionist_or_404(db: Session, *, receptionist_id: int) -> User:
    receptionist = db.get(User, receptionist_id)
    if receptionist is None or receptionist.role != UserRole.RECEPTIONIST or not receptionist.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receptionist not found")
    return receptionist


def account_email(username: str) -> str:
    safe_username = username.lower().replace("@", "_at_")
    return f"{safe_username}@clinic.local"
