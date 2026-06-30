import logging
import random
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal

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
from app.models.operation import FitnessStatus, Operation, OperationStatus, TestStatus
from app.models.patient import Patient
from app.models.payment import PaymentMethod, PaymentStatus
from app.models.supply import MedicalSupply, SupplyCategory
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
    {"full_name": "Dr. Amit Deshmukh", "email": "amit.deshmukh@clinic.com"},
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
]

DUMMY_PATIENTS = [
    {
        "first_name": "Anjali",
        "last_name": "Mehta",
        "age": 34,
        "gender": "Female",
        "phone": "9876501001",
        "address": "12 Lotus Residency, Pune",
        "date_of_birth": date(1992, 4, 18),
    },
    {
        "first_name": "Rohan",
        "last_name": "Kulkarni",
        "age": 42,
        "gender": "Male",
        "phone": "9876501002",
        "address": "8 Shivaji Nagar, Pune",
        "date_of_birth": date(1984, 9, 5),
    },
    {
        "first_name": "Meera",
        "last_name": "Iyer",
        "age": 29,
        "gender": "Female",
        "phone": "9876501003",
        "address": "Flat 403, Green Park, Baner",
        "date_of_birth": date(1997, 2, 11),
    },
    {
        "first_name": "Sanjay",
        "last_name": "Patil",
        "age": 58,
        "gender": "Male",
        "phone": "9876501004",
        "address": "Ganesh Colony, Aundh",
        "date_of_birth": date(1968, 7, 22),
    },
    {
        "first_name": "Fatima",
        "last_name": "Shaikh",
        "age": 47,
        "gender": "Female",
        "phone": "9876501005",
        "address": "Near Civil Hospital, Camp",
        "date_of_birth": date(1979, 12, 3),
    },
    {
        "first_name": "Arjun",
        "last_name": "Nair",
        "age": 16,
        "gender": "Male",
        "phone": "9876501006",
        "address": "Blue Ridge Township, Hinjewadi",
        "date_of_birth": date(2010, 1, 29),
    },
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
        existing = db.query(Patient).filter(Patient.phone == patient["phone"]).first()
        if existing is not None:
            continue
        patient_crud.create(db, obj_in=PatientCreate(**patient))
        logger.info("Seeded dummy patient: %s %s", patient["first_name"], patient["last_name"])


def seed_operation_types(db: Session) -> None:
    for name, price in DUMMY_OPERATION_TYPES:
        operation_type = operation_type_crud.get_by_name(db, name=name)
        if operation_type:
            if not operation_type.price:
                operation_type.price = price
                db.add(operation_type)
                db.commit()
            continue
        operation_type_crud.create(db, obj_in=OperationTypeCreate(name=name, price=price, is_active=True))
        logger.info("Seeded operation type: %s", name)


def seed_payment_settings(db: Session) -> None:
    get_or_create_setting(db, key=CONSULTATION_FEE_KEY, default_amount=500)


def seed_medical_supplies(db: Session) -> None:
    for category, name, current_stock, unit, minimum_stock, expiry_date, notes in DUMMY_SUPPLIES:
        existing = db.query(MedicalSupply).filter(MedicalSupply.name == name).first()
        if existing:
            if existing.expiry_date is None:
                existing.expiry_date = expiry_date
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
            ),
        )
    for category, name, current_stock, unit, minimum_stock, expiry_date, notes in DUMMY_SUPPLIES:
        supply = db.query(MedicalSupply).filter(MedicalSupply.name == name).first()
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
    queued_patients = db.query(Patient).order_by(Patient.id.asc()).limit(3).all()
    for patient in queued_patients:
        queue_crud.create_or_reuse_patient_entry(
            db,
            payload=QueueEntryCreate(patient_id=patient.id, queue_date=date.today(), reason="Routine eye check-up"),
            receptionist_id=receptionist.id,
            patient_create=patient_crud.create,
        )


def seed_consultations(db: Session) -> None:
    doctor = user_crud.get_by_email(db, email="rupa.kapale@clinic.com")
    patients = db.query(Patient).order_by(Patient.id.asc()).limit(2).all()
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
    patients = db.query(Patient).order_by(Patient.id.asc()).offset(3).limit(2).all()
    cataract = operation_type_crud.get_by_name(db, name="Cataract")
    injection = operation_type_crud.get_by_name(db, name="Intravitreal Injection")
    if doctor is None or cataract is None or injection is None or len(patients) < 2:
        return

    existing_operations = operation_crud.get_multi(db, limit=1)
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
    if db.query(Visit).filter(Visit.notes == "Historical analytics seed").first() is not None:
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
    first_names = ["Neha", "Vikram", "Priya", "Kiran", "Suresh", "Lata", "Asha", "Manoj", "Divya", "Rahul", "Sunita", "Nikhil"]
    last_names = ["Joshi", "Sharma", "Bhosale", "Kadam", "Pawar", "Menon", "Reddy", "Shah", "More", "Naik", "Jadhav", "Gokhale"]
    base_phone = 9887700000
    for index in range(48):
        phone = str(base_phone + index)
        if db.query(Patient).filter(Patient.phone == phone).first() is not None:
            continue
        age = 12 + (index * 7) % 72
        patient_crud.create(
            db,
            obj_in=PatientCreate(
                first_name=first_names[index % len(first_names)],
                last_name=last_names[(index * 3) % len(last_names)],
                age=age,
                gender="Female" if index % 2 == 0 else "Male",
                phone=phone,
                address=f"Analytics Demo Address {index + 1}, Pune",
                date_of_birth=date.today().replace(year=date.today().year - age),
            ),
        )
    return db.query(Patient).order_by(Patient.id.asc()).all()


def ensure_analytics_operation_types(db: Session) -> dict[str, int]:
    result: dict[str, int] = {}
    for name, price in DUMMY_OPERATION_TYPES:
        operation_type = operation_type_crud.get_by_name(db, name=name)
        if operation_type is None:
            operation_type = operation_type_crud.create(db, obj_in=OperationTypeCreate(name=name, price=price, is_active=True))
        elif operation_type.price != price:
            operation_type.price = price
            db.add(operation_type)
            db.commit()
            db.refresh(operation_type)
        result[name] = operation_type.id
    return result


def seed_historical_consultations(db: Session, *, doctor_id: int, patients: list[Patient], rng: random.Random) -> None:
    complaints = ["Blurred vision", "Eye watering", "Headache with eye strain", "Redness", "Difficulty reading", "Floaters"]
    diagnoses = ["Refractive error", "Dry eye disease", "Allergic conjunctivitis", "Immature cataract", "Presbyopia", "Normal retina"]
    today = date.today()
    start = today - timedelta(days=365)
    patient_index = 0
    current = start
    while current <= today:
        if current.weekday() == 6:
            current += timedelta(days=1)
            continue
        seasonal = 3 if current.month in {1, 2, 10, 11} else 0
        weekday_boost = 4 if current.weekday() in {0, 5} else 1
        count = max(4, 7 + seasonal + weekday_boost + rng.randint(-2, 4))
        for item in range(count):
            patient = patients[patient_index % len(patients)]
            patient_index += 1
            visit_time = datetime.combine(current, time(hour=9 + (item % 8), minute=(item * 7) % 60), tzinfo=UTC)
            fee = Decimal(500 + (current.month % 3) * 50)
            visit = visit_crud.create(
                db,
                obj_in=VisitCreate(
                    patient_id=patient.id,
                    doctor_id=doctor_id,
                    chief_complaint=complaints[(item + current.month) % len(complaints)],
                    diagnosis=diagnoses[(item + current.weekday()) % len(diagnoses)],
                    distance_prescription_enabled=True,
                    distance_right_sphere="0.00",
                    distance_right_cylinder="0.00",
                    distance_right_axis=0,
                    distance_right_va="6/6",
                    distance_left_sphere="0.00",
                    distance_left_cylinder="0.00",
                    distance_left_axis=0,
                    distance_left_va="6/6",
                    advice="Medication and review as advised.",
                    tests_prescribed="As clinically indicated",
                    additional_notes="Historical analytics seed",
                    notes="Historical analytics seed",
                ),
            )
            visit.visit_date = visit_time
            visit.completed_at = visit_time + timedelta(minutes=18 + item)
            visit.payment_status = PaymentStatus.PAID
            visit.payment_method = PaymentMethod.CASH if item % 3 else PaymentMethod.UPI_QR
            visit.consultation_fee = fee
            patient.last_visit_at = visit.completed_at
            db.add(visit)
            db.add(patient)
        db.commit()
        current += timedelta(days=1)


def seed_historical_operations(db: Session, *, doctor_id: int, patients: list[Patient], operation_types: dict[str, int], rng: random.Random) -> None:
    today = date.today()
    type_cycle = [
        ("Cataract Surgery", 7),
        ("LASIK", 2),
        ("Retina Surgery", 2),
        ("Glaucoma Surgery", 1),
        ("Intravitreal Injection", 3),
    ]
    for month_offset in range(11, -1, -1):
        month_start = add_months(today.replace(day=1), -month_offset)
        cataract_boost = 5 if month_start.month in {1, 2, 11, 12} else 0
        total = 10 + cataract_boost + rng.randint(-2, 6)
        for index in range(total):
            weighted = [name for name, weight in type_cycle for _ in range(weight + (2 if name == "Cataract Surgery" and cataract_boost else 0))]
            operation_name = weighted[(index + rng.randint(0, len(weighted) - 1)) % len(weighted)]
            operation_day = min(25, 2 + (index * 3) % 24)
            operation_date = month_start.replace(day=operation_day)
            if operation_date > today:
                continue
            patient = patients[(index + month_offset * 5) % len(patients)]
            operation = operation_crud.create(
                db,
                obj_in=OperationCreate(
                    patient_id=patient.id,
                    doctor_id=doctor_id,
                    operation_type_id=operation_types[operation_name],
                    operation_date=operation_date,
                    status=OperationStatus.COMPLETED,
                    remarks="Historical analytics seed",
                ),
            )
            operation.status = OperationStatus.COMPLETED
            operation.payment_status = PaymentStatus.PAID
            operation.payment_method = PaymentMethod.UPI_QR if index % 2 else PaymentMethod.CASH
            for test in operation.tests:
                operation_test_crud.update(
                    db,
                    db_obj=test,
                    obj_in=OperationTestUpdate(status=TestStatus.DONE, test_date=operation_date - timedelta(days=2), result="Within normal limits", fitness_status=FitnessStatus.FIT if test.test_name == "Physician Fitness" else None),
                )
            db.add(operation)
        db.commit()


def seed_historical_expenses(db: Session, *, rng: random.Random) -> None:
    if db.query(Expense).filter(Expense.notes == "Historical analytics seed").first() is not None:
        return
    today = date.today()
    monthly_expenses = [
        ("Clinic Rent", "Rent", 28000),
        ("Staff Salary", "Staff Salary", 95000),
        ("Electricity Bill", "Electricity", 8500),
        ("Internet Bill", "Internet", 1800),
        ("Water Bill", "Water", 900),
        ("Medicines Purchase", "Medicines", 24000),
        ("Medical Supplies", "Medical Supplies", 18000),
        ("Surgical Consumables", "Surgical Consumables", 32000),
        ("Equipment Maintenance", "Equipment Maintenance", 9000),
        ("Miscellaneous Clinic Expense", "Miscellaneous", 4500),
    ]
    for month_offset in range(11, -1, -1):
        month_start = add_months(today.replace(day=1), -month_offset)
        for index, (name, category, base_amount) in enumerate(monthly_expenses):
            variation = Decimal(rng.randint(-12, 18)) / Decimal(100)
            seasonal = Decimal("0.18") if category in {"Surgical Consumables", "Medical Supplies"} and month_start.month in {1, 2, 11, 12} else Decimal("0")
            amount = Decimal(base_amount) * (Decimal("1") + variation + seasonal)
            db.add(
                Expense(
                    expense_name=name,
                    category=category,
                    amount=amount.quantize(Decimal("0.01")),
                    expense_date=month_start.replace(day=min(26, 3 + index * 2)),
                    notes="Historical analytics seed",
                )
            )
        if month_start.month in {3, 9}:
            db.add(
                Expense(
                    expense_name="Ophthalmic Equipment Purchase",
                    category="Equipment Purchase",
                    amount=Decimal(125000 + rng.randint(-15000, 22000)),
                    expense_date=month_start.replace(day=14),
                    notes="Historical analytics seed",
                )
            )
    db.commit()


def verify_seed_financials(db: Session) -> None:
    consultation_revenue = db.query(func.coalesce(func.sum(Visit.consultation_fee), 0)).filter(Visit.payment_status == PaymentStatus.PAID).scalar()
    operation_revenue = db.query(func.coalesce(func.sum(Operation.operation_charge), 0)).filter(Operation.payment_status == PaymentStatus.PAID).scalar()
    expenses = db.query(func.coalesce(func.sum(Expense.amount), 0)).scalar()
    logger.info("Seed finance totals: revenue=%s expenses=%s profit=%s", consultation_revenue + operation_revenue, expenses, consultation_revenue + operation_revenue - expenses)


def add_months(value: date, months: int) -> date:
    month = value.month - 1 + months
    year = value.year + month // 12
    month = month % 12 + 1
    return date(year, month, 1)
