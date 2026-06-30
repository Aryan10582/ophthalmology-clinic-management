from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models.operation import OperationTestReport

UPLOAD_ROOT = Path("uploads") / "operation_reports"
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}


def save_operation_report(db: Session, *, operation_test_id: int, file: UploadFile) -> OperationTestReport:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError("Only images and PDF reports are supported")
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "report").suffix
    stored_filename = f"{uuid4().hex}{suffix}"
    file_path = UPLOAD_ROOT / stored_filename
    with file_path.open("wb") as buffer:
        while chunk := file.file.read(1024 * 1024):
            buffer.write(chunk)
    report = OperationTestReport(
        operation_test_id=operation_test_id,
        original_filename=file.filename or stored_filename,
        stored_filename=stored_filename,
        content_type=file.content_type or "application/octet-stream",
        file_path=str(file_path),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
