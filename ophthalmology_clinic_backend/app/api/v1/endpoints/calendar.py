from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.crud.followups import followup_crud
from app.crud.operations import operation_crud
from app.models.followup import FollowUpType
from app.models.user import UserRole
from app.schemas.followup import CalendarEvent

router = APIRouter()
staff_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST)


@router.get("/events", response_model=list[CalendarEvent], dependencies=[Depends(staff_required)], summary="Calendar events")
def calendar_events(
    filter: str = Query(default="all", pattern="^(all|operations|followups)$"),
    db: Session = Depends(get_db),
) -> list[CalendarEvent]:
    events: list[CalendarEvent] = []

    if filter in {"all", "operations"}:
        for operation in operation_crud.get_multi(db, limit=500):
            events.append(
                CalendarEvent(
                    id=f"operation-{operation.id}",
                    date=operation.operation_date,
                    title=f"{operation.operation_type.name if operation.operation_type else 'Operation'}",
                    category="operation",
                    color="red",
                    patient_name=f"{operation.patient.first_name} {operation.patient.last_name}" if operation.patient else "Patient",
                    source_id=operation.id,
                )
            )

    if filter in {"all", "followups"}:
        for followup in followup_crud.get_upcoming(db):
            color = "blue"
            category = "normal_followup"
            if followup.follow_up_type == FollowUpType.OPERATION_NEXT_DAY:
                color = "green"
                category = "next_day_followup"
            elif followup.follow_up_type == FollowUpType.OPERATION_ONE_WEEK:
                color = "yellow"
                category = "one_week_followup"
            events.append(
                CalendarEvent(
                    id=f"followup-{followup.id}",
                    date=followup.follow_up_date,
                    title=followup.notes or "Follow-up",
                    category=category,
                    color=color,
                    patient_name=f"{followup.patient.first_name} {followup.patient.last_name}" if followup.patient else "Patient",
                    source_id=followup.id,
                )
            )

    return sorted(events, key=lambda event: event.date)
