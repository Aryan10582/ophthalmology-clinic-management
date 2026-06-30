from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.followup import FollowUp, FollowUpStatus, FollowUpType
from app.models.operation import Operation
from app.models.patient import Patient
from app.models.user import User, UserRole
from app.schemas.followup import CalendarEvent

router = APIRouter()
staff_required = require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST)


@router.get("/events", response_model=list[CalendarEvent], summary="Calendar events")
def calendar_events(
    filter: str = Query(default="all", pattern="^(all|operations|followups)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(staff_required),
) -> list[CalendarEvent]:
    events: list[CalendarEvent] = []

    if filter in {"all", "operations"}:
        operations = (
            db.query(Operation)
            .join(Patient)
            .filter(Patient.is_demo_data == current_user.is_demo_account)
            .order_by(Operation.operation_date.asc(), Operation.id.asc())
            .limit(500)
            .all()
        )
        for operation in operations:
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
        followups = (
            db.query(FollowUp)
            .join(Patient)
            .filter(Patient.is_demo_data == current_user.is_demo_account, FollowUp.status == FollowUpStatus.SCHEDULED)
            .order_by(FollowUp.follow_up_date.asc(), FollowUp.id.asc())
            .limit(500)
            .all()
        )
        for followup in followups:
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
