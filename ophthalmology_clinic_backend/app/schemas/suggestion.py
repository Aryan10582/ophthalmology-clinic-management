from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


SUGGESTION_FIELDS = {"chief_complaint", "diagnosis", "advice", "tests_prescribed", "clinical_notes"}


class SuggestionCreate(BaseModel):
    field_name: str = Field(..., min_length=1, max_length=60)
    suggestion_text: str = Field(..., min_length=1)


class SuggestionRead(BaseModel):
    id: int
    doctor_id: int
    field_name: str
    suggestion_text: str
    usage_count: int
    last_used_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
