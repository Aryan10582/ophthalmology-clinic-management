from datetime import UTC, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.followup import FollowUp, FollowUpType
from app.models.operation import FitnessStatus, Operation, OperationTest, OperationType, TestStatus
from app.models.payment import PaymentStatus
from app.models.visit import Visit
from app.schemas.operation import OperationCreate, OperationTestCreate, OperationTestUpdate, OperationTypeCreate, OperationUpdate

REQUIRED_OPERATION_TESTS = [
    "CBC",
    "Blood Sugar (Fasting)",
    "Blood Sugar (Post Prandial)",
    "Urine Routine",
    "HIV",
    "HBsAg",
    "ECG",
    "Physician Fitness",
]


class CRUDOperationType(CRUDBase[OperationType, OperationTypeCreate, OperationTypeCreate]):
    def get_by_name(self, db: Session, *, name: str, is_demo_data: bool | None = None) -> OperationType | None:
        query = db.query(OperationType).filter(OperationType.name == name)
        if is_demo_data is not None:
            query = query.filter(OperationType.is_demo_data == is_demo_data)
        return query.first()


class CRUDOperation(CRUDBase[Operation, OperationCreate, OperationUpdate]):
    def get_by_patient(self, db: Session, *, patient_id: int, skip: int = 0, limit: int = 100) -> list[Operation]:
        return list(
            db.query(Operation)
            .filter(Operation.patient_id == patient_id)
            .order_by(Operation.operation_date.desc(), Operation.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, db: Session, *, obj_in: OperationCreate) -> Operation:
        data = obj_in.model_dump()
        visit_id = data.get("visit_id")
        if visit_id is not None:
            visit = db.get(Visit, visit_id)
            if visit is None:
                raise ValueError("visit_id must reference an existing consultation")
            data["patient_id"] = visit.patient_id
            data["doctor_id"] = visit.doctor_id
            if db.query(Operation.id).filter(Operation.visit_id == visit.id).first() is not None:
                raise ValueError("This consultation already has an operation")
        else:
            visit = Visit(
                patient_id=data["patient_id"],
                doctor_id=data["doctor_id"],
                visit_date=datetime.combine(data["operation_date"], time(hour=9), tzinfo=UTC),
                chief_complaint="Operation planning consultation",
                diagnosis="Surgical case planned",
                notes="Auto-created consultation for operation record.",
                payment_status=PaymentStatus.NOT_PAID,
            )
            db.add(visit)
            db.flush()
            data["visit_id"] = visit.id
        operation_type = db.get(OperationType, data["operation_type_id"])
        data["operation_charge"] = operation_type.price if operation_type else 0
        operation = Operation(**data)
        db.add(operation)
        db.commit()
        db.refresh(operation)

        for test_name in REQUIRED_OPERATION_TESTS:
            db.add(OperationTest(operation_id=operation.id, test_name=test_name, status=TestStatus.PENDING))

        db.add(
            FollowUp(
                patient_id=operation.patient_id,
                doctor_id=operation.doctor_id,
                operation_id=operation.id,
                follow_up_date=operation.operation_date + timedelta(days=1),
                follow_up_type=FollowUpType.OPERATION_NEXT_DAY,
                notes="Post-operative next day follow-up",
            )
        )
        db.add(
            FollowUp(
                patient_id=operation.patient_id,
                doctor_id=operation.doctor_id,
                operation_id=operation.id,
                follow_up_date=operation.operation_date + timedelta(weeks=1),
                follow_up_type=FollowUpType.OPERATION_ONE_WEEK,
                notes="Post-operative one week follow-up",
            )
        )
        db.commit()
        db.refresh(operation)
        return operation

    def with_ready_flag(self, operation: Operation) -> Operation:
        operation.ready_for_surgery = is_ready_for_surgery(operation.tests)
        return operation


class CRUDOperationTest(CRUDBase[OperationTest, OperationTestCreate, OperationTestUpdate]):
    def create_for_operation(self, db: Session, *, operation_id: int, obj_in: OperationTestCreate) -> OperationTest:
        db_obj = OperationTest(operation_id=operation_id, **obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


def is_ready_for_surgery(tests: list[OperationTest]) -> bool:
    required = {test.test_name: test for test in tests if test.test_name in REQUIRED_OPERATION_TESTS}
    if set(required) != set(REQUIRED_OPERATION_TESTS):
        return False
    for test_name, test in required.items():
        if test_name == "Physician Fitness":
            if test.fitness_status != FitnessStatus.FIT:
                return False
        elif test.status != TestStatus.DONE:
            return False
    return True


operation_type_crud = CRUDOperationType(OperationType)
operation_crud = CRUDOperation(Operation)
operation_test_crud = CRUDOperationTest(OperationTest)
