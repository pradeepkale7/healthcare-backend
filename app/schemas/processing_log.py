from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class ProcessingLogCreate(BaseModel):
    import_id: UUID
    header: str
    llm_suggestion: Optional[str]
    final_mapping: Optional[str]
    confidence_score: Optional[float]
    user_edited_mapping: Optional[bool] = False
