from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.realtime import realtime_manager
from app.crud.patients import patient_crud
from app.crud.reports import save_operation_report
from app.crud.users import user_crud
from app.crud.operations import operation_crud, operation_test_crud, operation_type_crud
from app.models.operation import Operation, OperationTest, OperationTestReport, OperationType
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.models.visit import Visit
from app.schemas.operation import (
    OperationCreate,
    OperationRead,
    OperationTestCreate,
    OperationTestRead,
    OperationTestReportRead,
    OperationTestUpdate,
    OperationTypeCreate,
    OperationTypeRead,
    OperationUpdate,
)
from app.schemas.payment import PaymentUpdate

router = APIRouter()
doctor_or_admin_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR)
staff_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST)


@router.get("/types", response_model=list[OperationTypeRead], summary="List operation types")
def list_operation_types(include_archived: bool = False, db: Session = Depends(get_db), current_user: User = Depends(staff_required)) -> list[OperationType]:
    query = db.query(OperationType).filter(OperationType.is_demo_data == current_user.is_demo_account)
    if not include_archived:
        query = query.filter(OperationType.is_active.is_(True))
    return list(query.order_by(OperationType.name.asc()).limit(500).all())


@router.post("/types", response_model=OperationTypeRead, status_code=status.HTTP_201_CREATED, summary="Add operation type")
def create_operation_type(payload: OperationTypeCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> OperationType:
    existing = operation_type_crud.get_by_name(db, name=payload.name, is_demo_data=current_user.is_demo_account)
    if existing:
        if existing.is_demo_data != current_user.is_demo_account:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Operation type name already exists in another clinic context")
        return existing
    payload = payload.model_copy(update={"is_demo_data": current_user.is_demo_account})
    operation_type = operation_type_crud.create(db, obj_in=payload)
    background_tasks.add_task(realtime_manager.broadcast, "operations.updated", {"operation_type_id": operation_type.id})
    return operation_type


@router.delete("/types/{operation_type_id}", response_model=OperationTypeRead, summary="Archive or delete operation type")
def archive_operation_type(operation_type_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> OperationType:
    operation_type = operation_type_crud.get(db, id=operation_type_id)
    if operation_type is None or operation_type.is_demo_data != current_user.is_demo_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation type not found")
    used = db.query(Operation).filter(Operation.operation_type_id == operation_type.id).first() is not None
    if not used:
        db.delete(operation_type)
        db.commit()
    else:
        operation_type.is_active = False
        db.add(operation_type)
        db.commit()
        db.refresh(operation_type)
    background_tasks.add_task(realtime_manager.broadcast, "operations.updated", {"operation_type_id": operation_type_id})
    return operation_type


@router.get("", response_model=list[OperationRead], summary="List operations")
def list_operations(db: Session = Depends(get_db), current_user: User = Depends(staff_required)) -> list[Operation]:
    operations = (
        db.query(Operation)
        .join(Patient)
        .filter(Patient.is_demo_data == current_user.is_demo_account)
        .order_by(Operation.operation_date.desc(), Operation.created_at.desc())
        .limit(500)
        .all()
    )
    return [operation_crud.with_ready_flag(operation) for operation in operations]


@router.post("", response_model=OperationRead, status_code=status.HTTP_201_CREATED, summary="Create operation record")
def create_operation(payload: OperationCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> Operation:
    if payload.visit_id is not None:
        visit = (
            db.query(Visit)
            .join(Patient)
            .filter(Visit.id == payload.visit_id, Patient.is_demo_data == current_user.is_demo_account)
            .first()
        )
        if visit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consultation not found")
        patient = visit.patient
        doctor = visit.doctor
    else:
        patient = patient_crud.get(db, id=payload.patient_id)
        if patient is None or patient.is_demo_data != current_user.is_demo_account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
        doctor = user_crud.get(db, id=payload.doctor_id)
    if doctor is None or doctor.role != UserRole.DOCTOR or doctor.is_demo_account != current_user.is_demo_account:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="doctor_id must reference a doctor")
    operation_type = operation_type_crud.get(db, id=payload.operation_type_id)
    if operation_type is None or operation_type.is_demo_data != current_user.is_demo_account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation type not found")
    try:
        operation = operation_crud.with_ready_flag(operation_crud.create(db, obj_in=payload))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    background_tasks.add_task(realtime_manager.broadcast, "operations.updated", {"operation_id": operation.id})
    return operation


@router.get("/{operation_id}", response_model=OperationRead, summary="Get operation")
def get_operation(operation_id: int, db: Session = Depends(get_db), current_user: User = Depends(staff_required)) -> Operation:
    operation = get_scoped_operation_or_404(db, operation_id=operation_id, current_user=current_user)
    return operation_crud.with_ready_flag(operation)


@router.patch("/{operation_id}", response_model=OperationRead, summary="Update operation")
def update_operation(operation_id: int, payload: OperationUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> Operation:
    operation = get_scoped_operation_or_404(db, operation_id=operation_id, current_user=current_user)
    operation = operation_crud.with_ready_flag(operation_crud.update(db, db_obj=operation, obj_in=payload))
    background_tasks.add_task(realtime_manager.broadcast, "operations.updated", {"operation_id": operation.id})
    return operation


@router.delete("/{operation_id}", response_model=OperationRead, summary="Delete operation")
def delete_operation(operation_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(doctor_or_admin_required)) -> OperationRead:
    operation = get_scoped_operation_or_404(db, operation_id=operation_id, current_user=current_user)
    deleted = OperationRead.model_validate(operation_crud.with_ready_flag(operation))
    for test in operation.tests:
        for report in test.reports:
            path = Path(report.file_path)
            if path.exists():
                path.unlink()
    db.delete(operation)
    db.commit()
    background_tasks.add_task(realtime_manager.broadcast, "operations.updated", {"operation_id": operation_id})
    return deleted


@router.post("/{operation_id}/tests", response_model=OperationTestRead, status_code=status.HTTP_201_CREATED, summary="Add operation test")
def add_operation_test(
    operation_id: int,
    payload: OperationTestCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_or_admin_required),
) -> OperationTest:
    get_scoped_operation_or_404(db, operation_id=operation_id, current_user=current_user)
    test = operation_test_crud.create_for_operation(db, operation_id=operation_id, obj_in=payload)
    background_tasks.add_task(realtime_manager.broadcast, "operations.updated", {"operation_id": operation_id})
    return test


@router.patch("/tests/{test_id}", response_model=OperationTestRead, summary="Update operation test")
def update_operation_test(
    test_id: int,
    payload: OperationTestUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_or_admin_required),
) -> OperationTest:
    test = get_scoped_operation_test_or_404(db, test_id=test_id, current_user=current_user)
    test = operation_test_crud.update(db, db_obj=test, obj_in=payload)
    background_tasks.add_task(realtime_manager.broadcast, "operations.updated", {"operation_id": test.operation_id, "test_id": test.id})
    return test


@router.patch("/{operation_id}/payment", response_model=OperationRead, summary="Update operation payment")
def update_operation_payment(operation_id: int, payload: PaymentUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user: User = Depends(staff_required)) -> Operation:
    operation = get_scoped_operation_or_404(db, operation_id=operation_id, current_user=current_user)
    operation.payment_status = payload.payment_status
    operation.payment_method = payload.payment_method
    if operation.operation_charge is None and operation.operation_type:
        operation.operation_charge = operation.operation_type.price
    db.add(operation)
    db.commit()
    db.refresh(operation)
    background_tasks.add_task(realtime_manager.broadcast, "payments.updated", {"operation_id": operation.id})
    return operation_crud.with_ready_flag(operation)


def get_scoped_operation_or_404(db: Session, *, operation_id: int, current_user: User) -> Operation:
    operation = (
        db.query(Operation)
        .join(Patient)
        .filter(Operation.id == operation_id, Patient.is_demo_data == current_user.is_demo_account)
        .first()
    )
    if operation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation not found")
    return operation


def get_scoped_operation_test_or_404(db: Session, *, test_id: int, current_user: User) -> OperationTest:
    test = (
        db.query(OperationTest)
        .join(Operation)
        .join(Patient)
        .filter(OperationTest.id == test_id, Patient.is_demo_data == current_user.is_demo_account)
        .first()
    )
    if test is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation test not found")
    return test


def get_scoped_operation_report_or_404(db: Session, *, report_id: int, current_user: User) -> OperationTestReport:
    report = (
        db.query(OperationTestReport)
        .join(OperationTest)
        .join(Operation)
        .join(Patient)
        .filter(OperationTestReport.id == report_id, Patient.is_demo_data == current_user.is_demo_account)
        .first()
    )
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return report


@router.post("/tests/{test_id}/reports", response_model=OperationTestReportRead, summary="Upload operation test report")
def upload_operation_report(
    test_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_required),
) -> OperationTestReport:
    test = get_scoped_operation_test_or_404(db, test_id=test_id, current_user=current_user)
    try:
        report = save_operation_report(db, operation_test_id=test_id, file=file)
        background_tasks.add_task(realtime_manager.broadcast, "reports.updated", {"operation_id": test.operation_id, "test_id": test.id})
        return report
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/reports/{report_id}/download", summary="Download operation report")
def download_operation_report(report_id: int, db: Session = Depends(get_db), current_user: User = Depends(staff_required)) -> FileResponse:
    report = get_scoped_operation_report_or_404(db, report_id=report_id, current_user=current_user)
    return FileResponse(report.file_path, media_type=report.content_type, filename=report.original_filename)


@router.delete("/reports/{report_id}", response_model=OperationTestReportRead, summary="Delete operation report")
def delete_operation_report(
    report_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_required),
) -> OperationTestReport:
    report = get_scoped_operation_report_or_404(db, report_id=report_id, current_user=current_user)
    operation_id = report.test.operation_id if report.test else None
    path = Path(report.file_path)
    db.delete(report)
    db.commit()
    if path.exists():
        path.unlink()
    background_tasks.add_task(realtime_manager.broadcast, "reports.updated", {"operation_id": operation_id})
    return report
