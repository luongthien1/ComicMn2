from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AiSettingsOut(BaseModel):
    # Giá trị ghi đè lưu trong DB — None = dùng .env
    ollama_endpoint: Optional[str] = None
    ollama_model: Optional[str] = None
    updated_at: Optional[datetime] = None
    # Giá trị đang thực sự dùng (sau khi gộp DB + .env) — để UI hiện gợi ý
    effective_endpoint: str = ""
    effective_model: str = ""
    token_configured: bool = False
    graph_configured: bool = False


class AiSettingsUpdate(BaseModel):
    ollama_endpoint: Optional[str] = None
    ollama_model: Optional[str] = None
