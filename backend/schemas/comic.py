from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ComicStatus(str, Enum):
    ongoing = "ongoing"
    completed = "completed"
    paused = "paused"


# ── Page ──────────────────────────────────────────────────────────────────────

class PageOut(BaseModel):
    id: int
    chapter_id: int
    order_index: int
    image_url: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PageCreate(BaseModel):
    image_url: str
    order_index: Optional[int] = None


class PageUpdate(BaseModel):
    image_url: Optional[str] = None
    order_index: Optional[int] = None


# ── Chapter ───────────────────────────────────────────────────────────────────

class ChapterOut(BaseModel):
    """Dùng trong danh sách (không load content/pages để giảm payload)."""
    id: int
    comic_id: int
    number: float
    title: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ChapterDetailOut(BaseModel):
    """Dùng trong trang viết chương — có đầy đủ content và pages."""
    id: int
    comic_id: int
    number: float
    title: Optional[str] = None
    content: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    pages: List[PageOut] = []

    model_config = {"from_attributes": True}


class ChapterCreate(BaseModel):
    number: float = Field(ge=0)
    title: Optional[str] = None


class ChapterUpdate(BaseModel):
    number: Optional[float] = Field(default=None, ge=0)
    title: Optional[str] = None
    content: Optional[str] = None
    notes: Optional[str] = None


# ── Revision ──────────────────────────────────────────────────────────────────

class ChapterRevisionOut(BaseModel):
    """Danh sách lịch sử — không kèm nội dung."""
    id: int
    chapter_id: int
    char_count: int
    reason: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChapterRevisionDetailOut(ChapterRevisionOut):
    content: Optional[str] = None


# ── Comic ─────────────────────────────────────────────────────────────────────

class ComicOut(BaseModel):
    id: int
    title: str
    author: Optional[str] = None
    genres: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    status: ComicStatus
    created_at: datetime
    updated_at: datetime
    chapters: List[ChapterOut] = []

    model_config = {"from_attributes": True}


class ComicCreate(BaseModel):
    title: str
    author: Optional[str] = None
    genres: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    status: ComicStatus = ComicStatus.ongoing


class ComicUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    genres: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    status: Optional[ComicStatus] = None
