import enum
from datetime import datetime

from db.migrations.base import Base
from sqlalchemy import Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import relationship


class ComicStatus(str, enum.Enum):
    ongoing = "ongoing"
    completed = "completed"
    paused = "paused"


class Comic(Base):
    __tablename__ = "comics"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    author = Column(String(255), nullable=True)
    genres = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    cover_url = Column(Text, nullable=True)
    status = Column(Enum(ComicStatus), default=ComicStatus.ongoing, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chapters = relationship(
        "Chapter",
        back_populates="comic",
        cascade="all, delete-orphan",
        order_by="Chapter.number",
    )
