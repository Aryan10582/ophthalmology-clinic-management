from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.visit import Visit
from app.schemas.visit import VisitCreate, VisitUpdate


class CRUDVisit(CRUDBase[Visit, VisitCreate, VisitUpdate]):
    def get_by_patient(self, db: Session, *, patient_id: int, skip: int = 0, limit: int = 100) -> list[Visit]:
        return list(
            db.query(Visit)
            .filter(Visit.patient_id == patient_id)
            .order_by(Visit.visit_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )


visit_crud = CRUDVisit(Visit)
