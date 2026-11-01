from datetime import datetime

from db.migrations.base import Base
from sqlalchemy import Column, DateTime, Integer, String


class AiSettings(Base):
    """Singleton row (id luôn = 1) — ghi đè endpoint/model Ollama trong .env. NULL = dùng .env."""

    __tablename__ = "ai_settings"

    id = Column(Integer, primary_key=True)
    ollama_endpoint = Column(String(500), nullable=True)
    # NULL = dùng OLLAMA_MODEL trong .env (xem core/ai_config.py)
    ollama_model = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
