from datetime import timedelta

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.followup import FollowUp, FollowUpType
from app.models.operation import FitnessStatus, Operation, OperationTest, OperationType, TestStatus
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
    def get_by_name(self, db: Session, *, name: str) -> OperationType | None:
        return db.query(OperationType).filter(OperationType.name == name).first()


class CRUDOperation(CRUDBase[Operation, OperationCreate, OperationUpdate]):
    def create(self, db: Session, *, obj_in: OperationCreate) -> Operation:
        data = obj_in.model_dump()
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
