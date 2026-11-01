from datetime import datetime

from db.migrations.base import Base
from sqlalchemy import Column, DateTime, Integer, String


class AiSettings(Base):
    """Singleton row (id luôn = 1) — cấu hình endpoint Ollama hiện dùng cho toàn hệ thống."""

    __tablename__ = "ai_settings"

    id = Column(Integer, primary_key=True)
    ollama_endpoint = Column(String(500), nullable=True)
    ollama_model = Column(String(255), nullable=False, default="qwen2.5:14b")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
