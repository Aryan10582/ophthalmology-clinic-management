from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.suggestion import ConsultationSuggestion
from app.models.visit import Visit
from app.schemas.suggestion import SUGGESTION_FIELDS

VISIT_SUGGESTION_FIELDS = {
    "chief_complaint": "chief_complaint",
    "diagnosis": "diagnosis",
    "advice": "advice",
    "tests_prescribed": "tests_prescribed",
    "clinical_notes": "additional_notes",
}


def save_suggestion(db: Session, *, doctor_id: int, field_name: str, suggestion_text: str) -> ConsultationSuggestion | None:
    normalized_text = " ".join(suggestion_text.split())
    if field_name not in SUGGESTION_FIELDS or not normalized_text:
        return None

    existing = (
        db.query(ConsultationSuggestion)
        .filter(
            ConsultationSuggestion.doctor_id == doctor_id,
            ConsultationSuggestion.field_name == field_name,
            ConsultationSuggestion.suggestion_text == normalized_text,
        )
        .first()
    )
    if existing:
        existing.usage_count += 1
        existing.last_used_at = datetime.now(UTC)
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    suggestion = ConsultationSuggestion(
        doctor_id=doctor_id,
        field_name=field_name,
        suggestion_text=normalized_text,
        usage_count=1,
        last_used_at=datetime.now(UTC),
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)
    return suggestion


def search_suggestions(db: Session, *, doctor_id: int, field_name: str, query: str, limit: int = 8) -> list[ConsultationSuggestion]:
    if field_name not in SUGGESTION_FIELDS:
        return []
    term = f"{query.strip().lower()}%"
    if term == "%":
        return []
    return list(
        db.query(ConsultationSuggestion)
        .filter(
            ConsultationSuggestion.doctor_id == doctor_id,
            ConsultationSuggestion.field_name == field_name,
            func.lower(ConsultationSuggestion.suggestion_text).like(term),
        )
        .order_by(ConsultationSuggestion.usage_count.desc(), ConsultationSuggestion.last_used_at.desc())
        .limit(min(limit, 10))
        .all()
    )


def learn_from_visit(db: Session, *, visit: Visit) -> None:
    for field_name, attr in VISIT_SUGGESTION_FIELDS.items():
        value = getattr(visit, attr, None)
        if value:
            save_suggestion(db, doctor_id=visit.doctor_id, field_name=field_name, suggestion_text=value)
