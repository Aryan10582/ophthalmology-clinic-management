from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.crud.suggestions import save_suggestion, search_suggestions
from app.models.suggestion import ConsultationSuggestion
from app.models.user import User, UserRole
from app.schemas.suggestion import SUGGESTION_FIELDS, SuggestionCreate, SuggestionRead

router = APIRouter()
doctor_or_admin_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR)


@router.get("/search", response_model=list[SuggestionRead], summary="Search doctor-specific consultation suggestions")
def search(
    field_name: str = Query(...),
    q: str = Query(..., min_length=1),
    limit: int = Query(8, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_or_admin_required),
) -> list[ConsultationSuggestion]:
    if current_user.role != UserRole.DOCTOR:
        return []
    if field_name not in SUGGESTION_FIELDS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported suggestion field")
    return search_suggestions(db, doctor_id=current_user.id, field_name=field_name, query=q, limit=limit)


@router.post("", response_model=SuggestionRead, status_code=status.HTTP_201_CREATED, summary="Save or update a consultation suggestion")
def save(
    payload: SuggestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(doctor_or_admin_required),
) -> ConsultationSuggestion:
    if current_user.role != UserRole.DOCTOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only doctors can save suggestions")
    suggestion = save_suggestion(db, doctor_id=current_user.id, field_name=payload.field_name, suggestion_text=payload.suggestion_text)
    if suggestion is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid suggestion")
    return suggestion
