import logging
import random
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.crud.followups import followup_crud
from app.crud.operations import operation_crud, operation_test_crud, operation_type_crud
from app.crud.payments import CONSULTATION_FEE_KEY, get_or_create_setting
from app.crud.patients import patient_crud
from app.crud.queue import queue_crud
from app.crud.supplies import supply_crud
from app.crud.users import user_crud
from app.crud.visits import visit_crud
from app.models.followup import FollowUpType
from app.models.operation import FitnessStatus, Operation, OperationStatus, OperationTest, OperationTestReport, OperationType, TestStatus
from app.models.patient import Patient
from app.models.payment import PaymentMethod, PaymentSetting, PaymentStatus
from app.models.prescription_template import PrescriptionTemplate
from app.models.queue import QueueStatus
from app.models.suggestion import ConsultationSuggestion
from app.models.supply import MedicalSupply, Notification, NotificationType, SupplyCategory
from app.models.supply_batch import MedicalSupplyBatch
from app.models.user import User, UserRole
from app.models.visit import Visit
from app.schemas.followup import FollowUpCreate
from app.schemas.operation import OperationCreate, OperationTestUpdate, OperationTypeCreate
from app.schemas.patient import PatientCreate
from app.schemas.queue import QueueEntryCreate
from app.schemas.supply import MedicalSupplyCreate
from app.schemas.user import UserCreate
from app.schemas.visit import VisitCreate
from app.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_ADMIN_FULL_NAME = "System Administrator"
DEFAULT_ADMIN_EMAIL = "admin@clinic.com"
DEFAULT_ADMIN_PASSWORD = "ClinicPass123"

DEFAULT_DOCTOR_PASSWORD = "Doctor@12345"
DEFAULT_RECEPTIONIST_PASSWORD = "Reception@12345"

DUMMY_DOCTORS = [
    {"full_name": "Dr. Rupa Kapale", "email": "rupa.kapale@clinic.com"},
]

DUMMY_RECEPTIONISTS = [
    {"full_name": "Receptionist 1", "email": "reception1@clinic.com"},
    {"full_name": "Receptionist 2", "email": "reception2@clinic.com"},
]

DUMMY_OPERATION_TYPES = [
    ("Cataract", 18000),
    ("Cataract Surgery", 22000),
    ("LASIK", 38000),
    ("Retina Surgery", 52000),
    ("Glaucoma Surgery", 32000),
    ("Pterygium", 12000),
    ("Intravitreal Injection", 9000),
]
DUMMY_SUPPLIES = [
    (SupplyCategory.EMERGENCY, "Emergency Eye Wash", 4, "bottle", 5, date.today() + timedelta(days=25), "Low stock and near expiry"),
    (SupplyCategory.OPERATION, "2cc Syringe", 8, "pcs", 10, date.today() + timedelta(days=7), "Used for injections"),
    (SupplyCategory.OPERATION, "Sterile Eye Drapes", 35, "pcs", 20, date.today() + timedelta(days=180), None),
    (SupplyCategory.GENERAL, "Cotton Swabs", 120, "pcs", 50, date.today() + timedelta(days=365), None),
    (SupplyCategory.OPERATION, "IOL Cartridge", 6, "pcs", 12, date.today() - timedelta(days=12), "Expired demo item"),
    (SupplyCategory.GENERAL, "Lubricant Eye Drops", 80, "bottle", 30, date.today() + timedelta(days=90), "Healthy stock"),
    (SupplyCategory.GENERAL, "Moxifloxacin Eye Drops", 24, "bottle", 12, date.today() + timedelta(days=210), "Post-operative antibiotic"),
    (SupplyCategory.GENERAL, "Prednisolone Eye Drops", 18, "bottle", 10, date.today() + timedelta(days=160), "Steroid drops"),
    (SupplyCategory.GENERAL, "Tropicamide Eye Drops", 7, "bottle", 8, date.today() + timedelta(days=45), "Near expiry and low stock"),
    (SupplyCategory.OPERATION, "Phaco Tip Sleeves", 14, "pcs", 10, date.today() + timedelta(days=300), None),
    (SupplyCategory.OPERATION, "Viscoelastic Syringe", 9, "pcs", 8, date.today() + timedelta(days=120), None),
    (SupplyCategory.OPERATION, "Sterile Gloves 7.0", 42, "pair", 25, date.today() + timedelta(days=420), None),
    (SupplyCategory.OPERATION, "IOL Foldable Lens", 11, "pcs", 6, date.today() + timedelta(days=540), None),
    (SupplyCategory.EMERGENCY, "Fluorescein Strips", 15, "strip", 20, date.today() + timedelta(days=80), "Low stock"),
    (SupplyCategory.GENERAL, "Schirmer Test Strips", 22, "strip", 15, date.today() + timedelta(days=240), None),
    (SupplyCategory.GENERAL, "Eye Pads", 70, "pcs", 40, date.today() + timedelta(days=360), None),
]

DUMMY_PATIENTS = [
    {
        "first_name": "Anjali",
        "last_name": "Mehta",
        "age": 34,
        "gender": "Female",
        "phone": "9876501001",
        "address": "12 Lotus Residency, Pune",
        "occupation": "School Teacher",
        "date_of_birth": date(1992, 4, 18),
    },
    {
        "first_name": "Rohan",
        "last_name": "Kulkarni",
        "age": 42,
        "gender": "Male",
        "phone": "9876501002",
        "address": "8 Shivaji Nagar, Pune",
        "occupation": "Software Engineer",
        "date_of_birth": date(1984, 9, 5),
    },
    {
        "first_name": "Meera",
        "last_name": "Iyer",
        "age": 29,
        "gender": "Female",
        "phone": "9876501003",
        "address": "Flat 403, Green Park, Baner",
        "occupation": "Chartered Accountant",
        "date_of_birth": date(1997, 2, 11),
    },
    {
        "first_name": "Sanjay",
        "last_name": "Patil",
        "age": 58,
        "gender": "Male",
        "phone": "9876501004",
        "address": "Ganesh Colony, Aundh",
        "occupation": "Retired Bank Manager",
        "date_of_birth": date(1968, 7, 22),
    },
    {
        "first_name": "Fatima",
        "last_name": "Shaikh",
        "age": 47,
        "gender": "Female",
        "phone": "9876501005",
        "address": "Near Civil Hospital, Camp",
        "occupation": "Homemaker",
        "date_of_birth": date(1979, 12, 3),
    },
    {
        "first_name": "Arjun",
        "last_name": "Nair",
        "age": 16,
        "gender": "Male",
        "phone": "9876501006",
        "address": "Blue Ridge Township, Hinjewadi",
        "occupation": "Student",
        "date_of_birth": date(2010, 1, 29),
    },
]

DEMO_PATIENT_TARGET = 26

DEMO_CASES = [
    ("Cataract", "Progressive painless diminution of vision", "Immature senile cataract", "Cataract surgery planned after fitness clearance."),
    ("Glaucoma", "Headache and halos around lights", "Primary open angle glaucoma", "IOP control, OCT RNFL and visual field review."),
    ("Dry Eye", "Burning and foreign body sensation", "Evaporative dry eye disease", "Lubricants, warm compresses and screen hygiene."),
    ("Myopia", "Difficulty seeing distant objects", "Myopia with astigmatism", "Distance glasses prescribed."),
    ("Hyperopia", "Eye strain while reading", "Hypermetropia", "Refraction correction and review."),
    ("Astigmatism", "Distorted vision", "Compound myopic astigmatism", "Cylindrical correction prescribed."),
    ("Conjunctivitis", "Redness and watering", "Acute allergic conjunctivitis", "Anti-allergy drops and cold compresses."),
    ("Diabetic Retinopathy", "Blurred vision with diabetes", "Moderate NPDR", "Retina evaluation and glycemic control advised."),
    ("Hypertensive Retinopathy", "Routine eye check with hypertension", "Grade 1 hypertensive retinopathy", "Blood pressure control and fundus review."),
    ("Macular Degeneration", "Central vision distortion", "Dry age-related macular degeneration", "Amsler monitoring and retina follow-up."),
]


def seed_default_admin(db: Session, *, is_demo_account: bool = False) -> User | None:
    existing_admin = user_crud.get_by_email(db, email=DEFAULT_ADMIN_EMAIL)
    if existing_admin is not None:
        logger.info("Default admin seed skipped; admin account already exists.")
        return existing_admin

    user_count = db.query(User).count()
    if user_count > 0:
        logger.info("Default admin seed skipped; users already exist.")
        return None

    admin_in = UserCreate(
        full_name=DEFAULT_ADMIN_FULL_NAME,
        email=DEFAULT_ADMIN_EMAIL,
        password=DEFAULT_ADMIN_PASSWORD,
        role=UserRole.ADMIN,
        is_active=True,
        is_demo_account=is_demo_account,
    )
    try:
        admin = user_crud.create(db, obj_in=admin_in)
    except IntegrityError:
        db.rollback()
        logger.info("Default admin seed skipped; admin account was created concurrently.")
        return user_crud.get_by_email(db, email=DEFAULT_ADMIN_EMAIL)

    logger.info("Default admin account created: %s", DEFAULT_ADMIN_EMAIL)
    return admin


def init_db(db: Session) -> None:
    if not settings.SEED_DEMO_DATA:
        logger.info("Demo data seed skipped; SEED_DEMO_DATA is disabled.")
        return
    if real_doctor_exists(db):
        logger.info("Demo data seed skipped; real clinic doctor account already exists.")
        return
    ensure_demo_clinic(db)


def ensure_demo_clinic(db: Session) -> User | None:
    if demo_seed_needs_refresh(db):
        clear_demo_seed_data(db)
    seed_default_admin(db, is_demo_account=True)
    seed_dummy_doctors(db)
    seed_dummy_receptionists(db)
    seed_dummy_patients(db)
    seed_operation_types(db)
    seed_payment_settings(db)
    seed_medical_supplies(db)
    seed_queue_entries(db)
    seed_consultations(db)
    seed_operations_and_followups(db)
    seed_historical_analytics_data(db)
    seed_demo_operation_reports(db)
    seed_demo_prescription_template(db)
    seed_demo_notifications(db)
    return user_crud.get_by_email(db, email=DUMMY_DOCTORS[0]["email"])


def reset_demo_clinic(db: Session) -> User | None:
    clear_demo_seed_data(db)
    return ensure_demo_clinic(db)


def demo_seed_needs_refresh(db: Session) -> bool:
    demo_patient_count = db.query(Patient.id).filter(Patient.is_demo_data.is_(True)).count()
    demo_visit_count = db.query(Visit.id).join(Patient).filter(Patient.is_demo_data.is_(True)).count()
    demo_operation_count = db.query(Operation.id).join(Patient).filter(Patient.is_demo_data.is_(True)).count()
    return demo_patient_count > 35 or demo_visit_count > 60 or demo_operation_count > 15


def clear_demo_seed_data(db: Session) -> None:
    demo_patients = [row[0] for row in db.query(Patient.id).filter(Patient.is_demo_data.is_(True)).all()]
    demo_users = [row[0] for row in db.query(User.id).filter(User.is_demo_account.is_(True)).all()]
    demo_supplies = [row[0] for row in db.query(MedicalSupply.id).filter(MedicalSupply.is_demo_data.is_(True)).all()]
    demo_operation_types = [row[0] for row in db.query(OperationType.id).filter(OperationType.is_demo_data.is_(True)).all()]
    demo_operations = [row[0] for row in db.query(Operation.id).filter(Operation.patient_id.in_(demo_patients)).all()] if demo_patients else []
    demo_tests = [row[0] for row in db.query(OperationTest.id).filter(OperationTest.operation_id.in_(demo_operations)).all()] if demo_operations else []

    if demo_tests:
        for report in db.query(OperationTestReport).filter(OperationTestReport.operation_test_id.in_(demo_tests)).all():
            path = Path(report.file_path)
            if path.exists():
                path.unlink()
        db.query(OperationTestReport).filter(OperationTestReport.operation_test_id.in_(demo_tests)).delete(synchronize_session=False)
    if demo_operations:
        db.query(OperationTest).filter(OperationTest.operation_id.in_(demo_operations)).delete(synchronize_session=False)
        db.query(followup_crud.model).filter(followup_crud.model.operation_id.in_(demo_operations)).delete(synchronize_session=False)
        db.query(Operation).filter(Operation.id.in_(demo_operations)).delete(synchronize_session=False)
    if demo_patients:
        db.query(followup_crud.model).filter(followup_crud.model.patient_id.in_(demo_patients)).delete(synchronize_session=False)
        db.query(queue_crud.model).filter(queue_crud.model.patient_id.in_(demo_patients)).delete(synchronize_session=False)
        db.query(Visit).filter(Visit.patient_id.in_(demo_patients)).delete(synchronize_session=False)
        db.query(Patient).filter(Patient.id.in_(demo_patients)).delete(synchronize_session=False)
    if demo_supplies:
        db.query(MedicalSupplyBatch).filter(MedicalSupplyBatch.supply_id.in_(demo_supplies)).delete(synchronize_session=False)
        db.query(MedicalSupply).filter(MedicalSupply.id.in_(demo_supplies)).delete(synchronize_session=False)
    db.query(Notification).filter(Notification.is_demo_data.is_(True)).delete(synchronize_session=False)
    db.query(Expense).filter(Expense.is_demo_data.is_(True)).delete(synchronize_session=False)
    if demo_users:
        db.query(ConsultationSuggestion).filter(ConsultationSuggestion.doctor_id.in_(demo_users)).delete(synchronize_session=False)
        db.query(PrescriptionTemplate).filter(PrescriptionTemplate.doctor_id.in_(demo_users)).delete(synchronize_session=False)
        db.query(User).filter(User.id.in_(demo_users)).delete(synchronize_session=False)
    if demo_operation_types:
        db.query(OperationType).filter(OperationType.id.in_(demo_operation_types)).delete(synchronize_session=False)
    db.query(PaymentSetting).filter(PaymentSetting.is_demo_data.is_(True)).delete(synchronize_session=False)
    db.commit()


def real_doctor_exists(db: Session) -> bool:
    return (
        db.query(User.id)
        .filter(
            User.role == UserRole.DOCTOR,
            User.is_demo_account.is_(False),
        )
        .first()
        is not None
    )


def seed_dummy_doctors(db: Session) -> None:
    for doctor in DUMMY_DOCTORS:
        if user_crud.get_by_email(db, email=doctor["email"]):
            continue
        user_crud.create(
            db,
            obj_in=UserCreate(
                full_name=doctor["full_name"],
                email=doctor["email"],
                password=DEFAULT_DOCTOR_PASSWORD,
                role=UserRole.DOCTOR,
                is_active=True,
                is_demo_account=True,
            ),
        )
        logger.info("Seeded doctor account: %s", doctor["email"])


def seed_dummy_receptionists(db: Session) -> None:
    for receptionist in DUMMY_RECEPTIONISTS:
        if user_crud.get_by_email(db, email=receptionist["email"]):
            continue
        user_crud.create(
            db,
            obj_in=UserCreate(
                full_name=receptionist["full_name"],
                email=receptionist["email"],
                password=DEFAULT_RECEPTIONIST_PASSWORD,
                role=UserRole.RECEPTIONIST,
                is_active=True,
                is_demo_account=True,
            ),
        )
        logger.info("Seeded receptionist account: %s", receptionist["email"])


def seed_dummy_patients(db: Session) -> None:
    for patient in DUMMY_PATIENTS:
        existing = db.query(Patient).filter(Patient.phone == patient["phone"], Patient.is_demo_data.is_(True)).first()
        if existing is not None:
            continue
        created = patient_crud.create(db, obj_in=PatientCreate(**patient, is_demo_data=True))
        created.created_at = datetime.now(UTC) - timedelta(days=180 - created.id % 90)
        db.add(created)
        db.commit()
        logger.info("Seeded dummy patient: %s %s", patient["first_name"], patient["last_name"])

    first_names = ["Neha", "Vikram", "Priya", "Kiran", "Suresh", "Lata", "Asha", "Manoj", "Divya", "Rahul", "Sunita", "Nikhil", "Kavita", "Prakash", "Ishita", "Mahesh", "Pooja", "Sameer", "Vaishali", "Omkar"]
    last_names = ["Joshi", "Sharma", "Bhosale", "Kadam", "Pawar", "Menon", "Reddy", "Shah", "More", "Naik", "Jadhav", "Gokhale", "Deshpande", "Kulkarni", "Shetty", "Mane"]
    occupations = ["Teacher", "IT Professional", "Shop Owner", "Retired", "Homemaker", "Student", "Driver", "Nurse", "Accountant", "Farmer", "Business Owner", "Architect"]
    existing_count = db.query(Patient.id).filter(Patient.is_demo_data.is_(True)).count()
    base_phone = 9876502000
    index = 0
    while existing_count < DEMO_PATIENT_TARGET:
        phone = str(base_phone + index)
        index += 1
        if db.query(Patient).filter(Patient.phone == phone, Patient.is_demo_data.is_(True)).first() is not None:
            continue
        age = 14 + (index * 5) % 70
        patient = patient_crud.create(
            db,
            obj_in=PatientCreate(
                first_name=first_names[index % len(first_names)],
                last_name=last_names[(index * 3) % len(last_names)],
                age=age,
                gender="Female" if index % 2 == 0 else "Male",
                phone=phone,
                address=f"{12 + index}, {['Kothrud', 'Baner', 'Aundh', 'Hadapsar', 'Wakad'][index % 5]}, Pune",
                occupation=occupations[index % len(occupations)],
                date_of_birth=date.today().replace(year=date.today().year - age),
                is_demo_data=True,
            ),
        )
        patient.created_at = datetime.now(UTC) - timedelta(days=160 - (index * 4) % 140)
        db.add(patient)
        db.commit()
        existing_count += 1


def seed_operation_types(db: Session) -> None:
    for name, price in DUMMY_OPERATION_TYPES:
        operation_type = operation_type_crud.get_by_name(db, name=name, is_demo_data=True)
        if operation_type:
            if not operation_type.price:
                operation_type.price = price
            operation_type.is_demo_data = True
            db.add(operation_type)
            db.commit()
            continue
        operation_type_crud.create(db, obj_in=OperationTypeCreate(name=name, price=price, is_active=True, is_demo_data=True))
        logger.info("Seeded operation type: %s", name)


def seed_payment_settings(db: Session) -> None:
    get_or_create_setting(db, key=CONSULTATION_FEE_KEY, default_amount=500, is_demo_data=True)


def seed_medical_supplies(db: Session) -> None:
    for category, name, current_stock, unit, minimum_stock, expiry_date, notes in DUMMY_SUPPLIES:
        existing = db.query(MedicalSupply).filter(MedicalSupply.name == name, MedicalSupply.is_demo_data.is_(True)).first()
        if existing:
            if existing.expiry_date is None:
                existing.expiry_date = expiry_date
            existing.is_demo_data = True
            db.add(existing)
            db.commit()
            continue
        supply_crud.create(
            db,
            obj_in=MedicalSupplyCreate(
                category=category,
                name=name,
                current_stock=current_stock,
                unit=unit,
                minimum_stock=minimum_stock,
                expiry_date=expiry_date,
                notes=notes,
                is_demo_data=True,
            ),
        )
    for category, name, current_stock, unit, minimum_stock, expiry_date, notes in DUMMY_SUPPLIES:
        supply = db.query(MedicalSupply).filter(MedicalSupply.name == name, MedicalSupply.is_demo_data.is_(True)).first()
        if supply is None or db.query(MedicalSupplyBatch).filter(MedicalSupplyBatch.supply_id == supply.id).first() is not None:
            continue
        db.add(
            MedicalSupplyBatch(
                supply_id=supply.id,
                batch_code=f"{supply.id:03d}-A",
                quantity_initial=current_stock,
                quantity_remaining=current_stock,
                expiry_date=expiry_date or date.today() + timedelta(days=365),
                purchase_date=date.today() - timedelta(days=30),
                notes=notes,
            )
        )
        db.commit()


def seed_queue_entries(db: Session) -> None:
    receptionist = user_crud.get_by_email(db, email=DUMMY_RECEPTIONISTS[0]["email"])
    if receptionist is None:
        return
    existing_demo_queue = (
        db.query(queue_crud.model)
        .join(Patient)
        .filter(queue_crud.model.queue_date == date.today(), Patient.is_demo_data.is_(True))
        .count()
    )
    if existing_demo_queue >= 10:
        return
    queued_patients = db.query(Patient).filter(Patient.is_demo_data.is_(True)).order_by(Patient.id.asc()).limit(12).all()
    reasons = ["Routine eye check-up", "Dilated fundus evaluation", "Post-operative review", "Refraction and glasses", "IOP monitoring"]
    for index, patient in enumerate(queued_patients):
        entry = queue_crud.create_or_reuse_patient_entry(
            db,
            payload=QueueEntryCreate(patient_id=patient.id, queue_date=date.today(), reason=reasons[index % len(reasons)]),
            receptionist_id=receptionist.id,
            patient_create=patient_crud.create,
            is_demo_data=True,
        )
        if index == 0:
            entry.status = QueueStatus.IN_CONSULTATION
            entry.doctor_id = user_crud.get_by_email(db, email=DUMMY_DOCTORS[0]["email"]).id if user_crud.get_by_email(db, email=DUMMY_DOCTORS[0]["email"]) else None
            entry.started_at = datetime.now(UTC) - timedelta(minutes=12)
        elif index in {1, 2, 3}:
            entry.status = QueueStatus.COMPLETED
            entry.completed_at = datetime.now(UTC) - timedelta(minutes=45 - index * 6)
        db.add(entry)
    db.commit()


def seed_consultations(db: Session) -> None:
    doctor = user_crud.get_by_email(db, email="rupa.kapale@clinic.com")
    patients = db.query(Patient).filter(Patient.is_demo_data.is_(True)).order_by(Patient.id.asc()).limit(2).all()
    if doctor is None or len(patients) < 2:
        return

    if visit_crud.get_by_patient(db, patient_id=patients[0].id, limit=1):
        return

    visit_crud.create(
        db,
        obj_in=VisitCreate(
            patient_id=patients[0].id,
            doctor_id=doctor.id,
            chief_complaint="Blurring of vision while reading",
            diagnosis="Presbyopia",
            follow_up_date=date.today() + timedelta(days=180),
            distance_prescription_enabled=True,
            distance_right_sphere="+0.50",
            distance_right_cylinder="0.00",
            distance_right_axis=0,
            distance_right_va="6/6",
            distance_left_sphere="+0.50",
            distance_left_cylinder="0.00",
            distance_left_axis=0,
            distance_left_va="6/6",
            distance_add="+1.50",
            near_prescription_enabled=True,
            near_right_va="N6",
            near_left_va="N6",
            near_add="+1.50",
            eyelids_adnexa_right="Normal",
            eyelids_adnexa_left="Normal",
            extra_ocular_movements_right="Full",
            extra_ocular_movements_left="Full",
            cornea_right="Clear",
            cornea_left="Clear",
            anterior_chamber_right="Normal depth",
            anterior_chamber_left="Normal depth",
            conjunctiva_right="Quiet",
            conjunctiva_left="Quiet",
            pupil_right="Round reactive",
            pupil_left="Round reactive",
            lens_right="Clear",
            lens_left="Clear",
            fundus_right="Normal",
            fundus_left="Normal",
            advice="Near glasses prescribed. Review if symptoms persist.",
            tests_prescribed="None",
            additional_notes="Routine consultation seeded for demo.",
        ),
    )
    followup_crud.create(
        db,
        obj_in=FollowUpCreate(
            patient_id=patients[0].id,
            doctor_id=doctor.id,
            follow_up_date=date.today() + timedelta(days=180),
            follow_up_type=FollowUpType.NORMAL,
            notes="Six month review",
        ),
    )
    visit_crud.create(
        db,
        obj_in=VisitCreate(
            patient_id=patients[1].id,
            doctor_id=doctor.id,
            chief_complaint="Watering and irritation in both eyes",
            diagnosis="Allergic conjunctivitis",
            distance_prescription_enabled=False,
            near_prescription_enabled=False,
            eyelids_adnexa_right="Normal",
            eyelids_adnexa_left="Normal",
            conjunctiva_right="Congestion",
            conjunctiva_left="Congestion",
            cornea_right="Clear",
            cornea_left="Clear",
            advice="Lubricating drops and anti-allergy medication.",
            tests_prescribed="None",
        ),
    )


def seed_operations_and_followups(db: Session) -> None:
    doctor = user_crud.get_by_email(db, email="rupa.kapale@clinic.com")
    patients = db.query(Patient).filter(Patient.is_demo_data.is_(True)).order_by(Patient.id.asc()).offset(3).limit(2).all()
    cataract = operation_type_crud.get_by_name(db, name="Cataract", is_demo_data=True)
    injection = operation_type_crud.get_by_name(db, name="Intravitreal Injection", is_demo_data=True)
    if doctor is None or cataract is None or injection is None or len(patients) < 2:
        return

    existing_operations = db.query(Operation).join(Patient).filter(Patient.is_demo_data.is_(True)).first()
    if existing_operations:
        return

    cataract_operation = operation_crud.create(
        db,
        obj_in=OperationCreate(
            patient_id=patients[0].id,
            doctor_id=doctor.id,
            operation_type_id=cataract.id,
            operation_date=date.today() + timedelta(days=5),
            status=OperationStatus.SCHEDULED,
            remarks="Right eye cataract planned.",
        ),
    )
    for test in cataract_operation.tests[:4]:
        operation_test_crud.update(
            db,
            db_obj=test,
            obj_in=OperationTestUpdate(status=TestStatus.DONE, test_date=date.today(), result="Within normal limits"),
        )

    operation_crud.create(
        db,
        obj_in=OperationCreate(
            patient_id=patients[1].id,
            doctor_id=doctor.id,
            operation_type_id=injection.id,
            operation_date=date.today() + timedelta(days=12),
            status=OperationStatus.PLANNED,
            remarks="Anti-VEGF injection planned after test clearance.",
        ),
    )


def seed_historical_analytics_data(db: Session) -> None:
    if db.query(Visit).join(Patient).filter(Visit.notes == "Historical analytics seed", Patient.is_demo_data.is_(True)).first() is not None:
        logger.info("Historical analytics seed skipped; data already exists.")
        return

    doctor = user_crud.get_by_email(db, email="rupa.kapale@clinic.com")
    if doctor is None:
        return

    rng = random.Random(4317)
    patients = ensure_analytics_patients(db)
    operation_types = ensure_analytics_operation_types(db)
    seed_historical_consultations(db, doctor_id=doctor.id, patients=patients, rng=rng)
    seed_historical_operations(db, doctor_id=doctor.id, patients=patients, operation_types=operation_types, rng=rng)
    seed_historical_expenses(db, rng=rng)
    verify_seed_financials(db)


def ensure_analytics_patients(db: Session) -> list[Patient]:
    seed_dummy_patients(db)
    return list(db.query(Patient).filter(Patient.is_demo_data.is_(True)).order_by(Patient.id.asc()).all())


def ensure_analytics_operation_types(db: Session) -> dict[str, int]:
    result: dict[str, int] = {}
    for name, price in DUMMY_OPERATION_TYPES:
        operation_type = operation_type_crud.get_by_name(db, name=name, is_demo_data=True)
        if operation_type is None:
            operation_type = operation_type_crud.create(db, obj_in=OperationTypeCreate(name=name, price=price, is_active=True, is_demo_data=True))
        elif operation_type.price != price:
            operation_type.price = price
            operation_type.is_demo_data = True
            db.add(operation_type)
            db.commit()
            db.refresh(operation_type)
        result[name] = operation_type.id
    return result


def seed_historical_consultations(db: Session, *, doctor_id: int, patients: list[Patient], rng: random.Random) -> None:
    if len(patients) == 0:
        return
    today = date.today()
    patient_index = 0
    for month_offset in range(11, -1, -1):
        month_start = add_months(today.replace(day=1), -month_offset)
        count = 3 + (1 if month_start.month in {1, 2, 10, 11} else 0)
        for item in range(count):
            case = DEMO_CASES[(item + month_start.month + month_offset) % len(DEMO_CASES)]
            patient = patients[patient_index % len(patients)]
            patient_index += 1
            day = min(26, 2 + (item * 3) % 24)
            current = month_start.replace(day=day)
            if current > today:
                continue
            visit_time = datetime.combine(current, time(hour=9 + (item % 8), minute=(item * 7) % 60), tzinfo=UTC)
            fee = Decimal(500 + (current.month % 3) * 50)
            visit = visit_crud.create(
                db,
                obj_in=VisitCreate(
                    patient_id=patient.id,
                    doctor_id=doctor_id,
                    chief_complaint=case[1],
                    diagnosis=case[2],
                    distance_prescription_enabled=True,
                    distance_right_sphere=["0.00", "-1.25", "+0.75", "-2.00"][item % 4],
                    distance_right_cylinder=["0.00", "-0.50", "-0.75", "-1.00"][month_offset % 4],
                    distance_right_axis=(20 + item * 25) % 180,
                    distance_right_va=["6/6", "6/9", "6/12", "6/18"][item % 4],
                    distance_left_sphere=["0.00", "-1.00", "+0.50", "-1.75"][(item + 1) % 4],
                    distance_left_cylinder=["0.00", "-0.50", "-0.75", "-1.25"][(month_offset + 1) % 4],
                    distance_left_axis=(35 + item * 30) % 180,
                    distance_left_va=["6/6", "6/9", "6/12", "6/18"][(item + 1) % 4],
                    iop_enabled=True,
                    iop_right=14 + (item + month_offset) % 6,
                    iop_left=13 + (item * 2 + month_offset) % 6,
                    eyelids_adnexa_right="Normal",
                    eyelids_adnexa_left="Normal",
                    extra_ocular_movements_right="Full",
                    extra_ocular_movements_left="Full",
                    cornea_right="Clear",
                    cornea_left="Clear",
                    anterior_chamber_right="Normal depth",
                    anterior_chamber_left="Normal depth",
                    conjunctiva_right="Quiet" if case[0] != "Conjunctivitis" else "Congested",
                    conjunctiva_left="Quiet" if case[0] != "Conjunctivitis" else "Congested",
                    pupil_right="Round reactive",
                    pupil_left="Round reactive",
                    lens_right="Early NS" if case[0] == "Cataract" else "Clear",
                    lens_left="Early NS" if case[0] == "Cataract" else "Clear",
                    fundus_right="Healthy disc and macula" if "Retinopathy" not in case[0] else case[2],
                    fundus_left="Healthy disc and macula" if "Retinopathy" not in case[0] else case[2],
                    advice=case[3],
                    tests_prescribed="OCT / Fundus photo as clinically indicated" if case[0] in {"Glaucoma", "Diabetic Retinopathy", "Macular Degeneration"} else "None",
                    additional_notes="Historical analytics seed",
                    notes="Historical analytics seed",
                ),
            )
            visit.visit_date = visit_time
            visit.completed_at = visit_time + timedelta(minutes=18 + item)
            visit.payment_status = PaymentStatus.NOT_PAID if (month_offset == 0 and item == count - 1) else PaymentStatus.PAID
            visit.payment_method = None if visit.payment_status == PaymentStatus.NOT_PAID else (PaymentMethod.CASH if item % 3 else PaymentMethod.UPI_QR)
            visit.consultation_fee = fee
            patient.last_visit_at = visit.completed_at
            db.add(visit)
            db.add(patient)
        db.commit()


def seed_historical_operations(db: Session, *, doctor_id: int, patients: list[Patient], operation_types: dict[str, int], rng: random.Random) -> None:
    if len(patients) == 0:
        return
    today = date.today()
    planned_operations = [
        ("Cataract Surgery", -150, OperationStatus.COMPLETED),
        ("LASIK", -118, OperationStatus.COMPLETED),
        ("Retina Surgery", -92, OperationStatus.COMPLETED),
        ("Glaucoma Surgery", -63, OperationStatus.COMPLETED),
        ("Intravitreal Injection", -41, OperationStatus.COMPLETED),
        ("Cataract Surgery", -24, OperationStatus.COMPLETED),
        ("Pterygium", -10, OperationStatus.COMPLETED),
        ("LASIK", 18, OperationStatus.SCHEDULED),
    ]
    for index, (operation_name, day_offset, status_value) in enumerate(planned_operations):
        if operation_name not in operation_types:
            continue
        operation_date = today + timedelta(days=day_offset)
        patient = patients[(index * 3 + 4) % len(patients)]
        operation = operation_crud.create(
            db,
            obj_in=OperationCreate(
                patient_id=patient.id,
                doctor_id=doctor_id,
                operation_type_id=operation_types[operation_name],
                operation_date=operation_date,
                status=status_value,
                remarks=f"{operation_name} demo record with realistic pre-operative documentation.",
            ),
        )
        operation.status = status_value
        operation.payment_status = PaymentStatus.NOT_PAID if index in {6, 7} else PaymentStatus.PAID
        operation.payment_method = None if operation.payment_status == PaymentStatus.NOT_PAID else (PaymentMethod.UPI_QR if index % 2 else PaymentMethod.CASH)
        for test in operation.tests:
            operation_test_crud.update(
                db,
                db_obj=test,
                obj_in=OperationTestUpdate(
                    status=TestStatus.DONE if status_value == OperationStatus.COMPLETED or test.test_name != "Physician Fitness" else TestStatus.PENDING,
                    test_date=operation_date - timedelta(days=2),
                    result="Within normal limits" if status_value == OperationStatus.COMPLETED or test.test_name != "Physician Fitness" else None,
                    fitness_status=FitnessStatus.FIT if test.test_name == "Physician Fitness" and status_value == OperationStatus.COMPLETED else None,
                ),
            )
        db.add(operation)
    db.commit()


def seed_demo_prescription_template(db: Session) -> None:
    doctor = user_crud.get_by_email(db, email=DUMMY_DOCTORS[0]["email"])
    if doctor is None:
        return
    existing = db.query(PrescriptionTemplate).filter(PrescriptionTemplate.doctor_id == doctor.id).first()
    if existing is None:
        existing = PrescriptionTemplate(doctor_id=doctor.id)
    existing.template_name = "professional_blue"
    existing.doctor_name = "Dr. Rupa Kapale"
    existing.doctor_qualifications = "MS Ophthalmology, Fellowship in Phacoemulsification"
    existing.doctor_registration_number = "MMC 2014/04/2847"
    existing.clinic_name = "Iris Eye Clinic"
    existing.clinic_address = "2nd Floor, Lotus Medical Plaza, Baner Road, Pune, Maharashtra"
    existing.clinic_phone = "+91 98765 01000"
    existing.clinic_timings = "Mon-Sat 10:00 AM - 7:00 PM"
    existing.email = "care@iriseyeclinic.local"
    existing.website = "www.iriseyeclinic.local"
    existing.footer_text = "Please bring this prescription on your next visit."
    db.add(existing)
    db.commit()


def seed_demo_operation_reports(db: Session) -> None:
    if db.query(OperationTestReport).join(OperationTest).join(Operation).join(Patient).filter(Patient.is_demo_data.is_(True)).count() >= 5:
        return
    upload_root = Path("uploads") / "operation_reports"
    upload_root.mkdir(parents=True, exist_ok=True)
    tests = (
        db.query(OperationTest)
        .join(Operation)
        .join(Patient)
        .filter(Patient.is_demo_data.is_(True), OperationTest.status == TestStatus.DONE)
        .order_by(OperationTest.id.asc())
        .limit(6)
        .all()
    )
    for index, test in enumerate(tests, start=1):
        stored_filename = f"demo-report-{test.id}.pdf"
        file_path = upload_root / stored_filename
        if not file_path.exists():
            file_path.write_bytes(
                b"%PDF-1.4\n"
                b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
                b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
                b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 144]/Contents 4 0 R>>endobj\n"
                b"4 0 obj<</Length 61>>stream\nBT /F1 12 Tf 24 96 Td (Demo operation report - Iris Eye Clinic) Tj ET\nendstream endobj\n"
                b"xref\n0 5\n0000000000 65535 f \ntrailer<</Root 1 0 R/Size 5>>\nstartxref\n0\n%%EOF\n"
            )
        db.add(
            OperationTestReport(
                operation_test_id=test.id,
                original_filename=f"Demo {test.test_name} Report {index}.pdf",
                stored_filename=stored_filename,
                content_type="application/pdf",
                file_path=str(file_path),
            )
        )
    db.commit()


def seed_demo_notifications(db: Session) -> None:
    if db.query(Notification).filter(Notification.is_demo_data.is_(True)).count() >= 5:
        return
    messages = [
        ("Low Stock", "Fluorescein Strips are below minimum stock. Reorder this week."),
        ("Near Expiry", "Tropicamide Eye Drops expire soon. Use older batch first."),
        ("Expired Inventory", "IOL Cartridge has an expired batch. Review before surgery."),
        ("Pending Follow-up", "Three post-operative follow-ups are scheduled this week."),
        ("Pending Payment", "Two recent procedures are marked as not paid."),
        ("Low Stock", "Emergency Eye Wash is below minimum stock."),
    ]
    for title, message in messages:
        exists = db.query(Notification).filter(Notification.title == title, Notification.message == message, Notification.is_demo_data.is_(True)).first()
        if exists:
            continue
        db.add(Notification(notification_type=NotificationType.LOW_STOCK, title=title, message=message, is_demo_data=True))
    db.commit()


def seed_historical_expenses(db: Session, *, rng: random.Random) -> None:
    if db.query(Expense).filter(Expense.notes == "Historical analytics seed", Expense.is_demo_data.is_(True)).first() is not None:
        return
    today = date.today()
    demo_expenses = [
        ("Clinic Rent", "Rent", 28500, -330),
        ("Staff Salary", "Staff Salary", 98000, -300),
        ("Electricity Bill", "Electricity", 8600, -270),
        ("Internet Bill", "Internet", 1800, -240),
        ("Water Bill", "Water", 950, -210),
        ("Medicines Purchase", "Medicines", 24500, -180),
        ("Medical Supplies", "Medical Supplies", 18600, -150),
        ("Surgical Consumables", "Surgical Consumables", 33500, -120),
        ("Equipment Maintenance", "Equipment Maintenance", 9200, -90),
        ("Phaco Machine Service", "Equipment Maintenance", 18500, -60),
        ("Staff Incentive", "Staff Salary", 12000, -30),
        ("Miscellaneous Clinic Expense", "Miscellaneous", 4600, -6),
    ]
    for index, (name, category, base_amount, day_offset) in enumerate(demo_expenses):
        variation = Decimal(rng.randint(-10, 16)) / Decimal(100)
        amount = Decimal(base_amount) * (Decimal("1") + variation)
        expense_date = today + timedelta(days=day_offset)
        db.add(
            Expense(
                expense_name=name,
                category=category,
                amount=amount.quantize(Decimal("0.01")),
                expense_date=expense_date,
                notes="Historical analytics seed",
                is_demo_data=True,
            )
        )
    db.commit()


def verify_seed_financials(db: Session) -> None:
    consultation_revenue = db.query(func.coalesce(func.sum(Visit.consultation_fee), 0)).join(Patient).filter(Visit.payment_status == PaymentStatus.PAID, Patient.is_demo_data.is_(True)).scalar()
    operation_revenue = db.query(func.coalesce(func.sum(Operation.operation_charge), 0)).join(Patient).filter(Operation.payment_status == PaymentStatus.PAID, Patient.is_demo_data.is_(True)).scalar()
    expenses = db.query(func.coalesce(func.sum(Expense.amount), 0)).filter(Expense.is_demo_data.is_(True)).scalar()
    logger.info("Seed finance totals: revenue=%s expenses=%s profit=%s", consultation_revenue + operation_revenue, expenses, consultation_revenue + operation_revenue - expenses)


def add_months(value: date, months: int) -> date:
    month = value.month - 1 + months
    year = value.year + month // 12
    month = month % 12 + 1
    return date(year, month, 1)
