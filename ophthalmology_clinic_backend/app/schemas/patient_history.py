from pydantic import BaseModel

from app.schemas.followup import FollowUpRead
from app.schemas.operation import OperationRead
from app.schemas.visit import VisitRead


class PatientHistoryRead(BaseModel):
    consultations: list[VisitRead]
    operations: list[OperationRead]
    followups: list[FollowUpRead]
