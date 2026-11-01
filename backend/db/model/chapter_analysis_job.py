from datetime import datetime

from db.migrations.base import Base
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text


class ChapterAnalysisJob(Base):
    """Kết quả ingest + kiểm tra lỗi cho 1 lần lưu chương (chạy nền)."""

    __tablename__ = "chapter_analysis_jobs"

    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(
        Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status = Column(String(20), nullable=False, default="pending")  # pending|running|done|error
    ingest_result = Column(JSON, nullable=True)
    issues = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
