from datetime import date

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.followup import FollowUp
from app.schemas.followup import FollowUpCreate, FollowUpUpdate


class CRUDFollowUp(CRUDBase[FollowUp, FollowUpCreate, FollowUpUpdate]):
    def get_upcoming(self, db: Session, *, start: date | None = None, end: date | None = None) -> list[FollowUp]:
        query = db.query(FollowUp)
        if start:
            query = query.filter(FollowUp.follow_up_date >= start)
        if end:
            query = query.filter(FollowUp.follow_up_date <= end)
        return list(query.order_by(FollowUp.follow_up_date.asc(), FollowUp.id.asc()).all())


followup_crud = CRUDFollowUp(FollowUp)
