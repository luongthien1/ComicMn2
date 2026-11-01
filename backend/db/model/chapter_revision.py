from datetime import datetime

from db.migrations.base import Base
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship


class ChapterRevision(Base):
    """Bản lưu cũ của nội dung chương — để khôi phục khi lỡ xoá/ghi đè."""

    __tablename__ = "chapter_revisions"
    __table_args__ = (
        Index("ix_chapter_revisions_chapter_created", "chapter_id", "created_at"),
    )

    id = Column(Integer, primary_key=True)
    chapter_id = Column(
        Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False
    )
    content = Column(Text, nullable=True)
    char_count = Column(Integer, nullable=False, default=0)
    # auto: chụp định kỳ khi lưu | manual: người dùng bấm Lưu | restore: trước khi khôi phục
    reason = Column(String(20), nullable=False, default="auto")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    chapter = relationship("Chapter", back_populates="revisions")
