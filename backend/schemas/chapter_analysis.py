from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class ChapterAnalysisJobOut(BaseModel):
    id: int
    chapter_id: int
    status: str
    ingest_result: Optional[dict[str, Any]] = None
    issues: Optional[list[dict[str, Any]]] = None
    error_message: Optional[str] = None
    created_at: datetime
    finished_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
