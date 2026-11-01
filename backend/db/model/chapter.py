from datetime import datetime

from db.migrations.base import Base
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import deferred, relationship


class Chapter(Base):
    __tablename__ = "chapters"
    __table_args__ = (
        UniqueConstraint("comic_id", "number", name="uq_chapters_comic_number"),
    )

    id = Column(Integer, primary_key=True, index=True)
    comic_id = Column(Integer, ForeignKey("comics.id", ondelete="CASCADE"), nullable=False)
    # Float để có chương ngoại truyện (30.5)
    number = Column(Float, nullable=False)
    title = Column(String(255), nullable=True)
    # deferred: danh sách truyện/chương không kéo theo toàn bộ văn bản
    content = deferred(Column(Text, nullable=True))
    notes = deferred(Column(Text, nullable=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    comic = relationship("Comic", back_populates="chapters")
    pages = relationship(
        "Page",
        back_populates="chapter",
        cascade="all, delete-orphan",
        order_by="Page.order_index",
    )
    revisions = relationship(
        "ChapterRevision",
        back_populates="chapter",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
