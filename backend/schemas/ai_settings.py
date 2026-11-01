from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AiSettingsOut(BaseModel):
    ollama_endpoint: Optional[str] = None
    ollama_model: str
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AiSettingsUpdate(BaseModel):
    ollama_endpoint: Optional[str] = None
    ollama_model: Optional[str] = None
