from datetime import datetime

from db.migrations.base import Base
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    comic_id = Column(Integer, ForeignKey("comics.id", ondelete="CASCADE"), nullable=False)
    number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    comic = relationship("Comic", back_populates="chapters")
    pages = relationship(
        "Page",
        back_populates="chapter",
        cascade="all, delete-orphan",
        order_by="Page.order_index",
    )
