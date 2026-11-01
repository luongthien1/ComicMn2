from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import List, Optional

from db.model.chapter import Chapter
from db.model.chapter_analysis_job import ChapterAnalysisJob
from db.model.chapter_revision import ChapterRevision
from db.model.comic import Comic
from db.model.page import Page
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from libs.database.connect import get_db
from libs.logger.log import get_logger
from libs.story_graph.ingest import graph_configured, strip_html
from schemas.chapter_analysis import ChapterAnalysisJobOut
from schemas.comic import (
    ChapterCreate,
    ChapterDetailOut,
    ChapterOut,
    ChapterRevisionDetailOut,
    ChapterRevisionOut,
    ChapterUpdate,
    ComicCreate,
    ComicOut,
    ComicUpdate,
    PageCreate,
    PageOut,
    PageUpdate,
)
from services.chapter_analysis import enqueue_chapter_analysis
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload, undefer

router = APIRouter()
logger = get_logger(__name__)

# Chụp bản cũ tự động khi lần chụp trước đã quá khoảng này
SNAPSHOT_INTERVAL = timedelta(minutes=10)
# Giữ tối đa bấy nhiêu bản mỗi chương; bản cũ nhất bị xoá trước
MAX_REVISIONS = 200


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_comic(db: Session, comic_id: int) -> Comic:
    comic = db.get(Comic, comic_id)
    if not comic:
        raise HTTPException(status_code=404, detail="Không tìm thấy truyện")
    return comic


def _get_chapter(db: Session, comic_id: int, chapter_id: int, *, full: bool = False) -> Chapter:
    q = db.query(Chapter).filter(Chapter.id == chapter_id, Chapter.comic_id == comic_id)
    if full:
        q = q.options(undefer(Chapter.content), undefer(Chapter.notes))
    chapter = q.first()
    if not chapter:
        raise HTTPException(status_code=404, detail="Không tìm thấy chương")
    return chapter


@contextmanager
def _number_conflict_guard(db: Session):
    """Trùng (comic_id, number) → 409. Bọc cả khối vì autoflush có thể nổ trước commit."""
    try:
        yield
        db.commit()
    except IntegrityError as e:
        db.rollback()
        msg = str(e.orig)
        # Postgres báo tên constraint; SQLite (test) báo tên cột
        if "uq_chapters_comic_number" in msg or "chapters.comic_id, chapters.number" in msg:
            raise HTTPException(status_code=409, detail="Truyện đã có chương mang số này.")
        raise


def _touch_comic(db: Session, comic_id: int) -> None:
    """Sửa chương = truyện vừa được cập nhật (danh sách sắp theo updated_at)."""
    db.query(Comic).filter(Comic.id == comic_id).update(
        {"updated_at": datetime.utcnow()}, synchronize_session=False
    )


def _add_revision(db: Session, chapter_id: int, content: Optional[str], reason: str) -> bool:
    """Lưu một bản; bỏ qua nếu trùng bản gần nhất."""
    if not content:
        return False
    latest = (
        db.query(ChapterRevision)
        .filter(ChapterRevision.chapter_id == chapter_id)
        .order_by(ChapterRevision.created_at.desc(), ChapterRevision.id.desc())
        .first()
    )
    if latest is not None and latest.content == content:
        return False
    db.add(ChapterRevision(
        chapter_id=chapter_id,
        content=content,
        char_count=len(strip_html(content)),
        reason=reason,
        created_at=datetime.utcnow(),
    ))
    return True


def _last_revision_at(db: Session, chapter_id: int) -> Optional[datetime]:
    row = (
        db.query(ChapterRevision.created_at)
        .filter(ChapterRevision.chapter_id == chapter_id)
        .order_by(ChapterRevision.created_at.desc())
        .first()
    )
    return row[0] if row else None


def _prune_revisions(db: Session, chapter_id: int) -> None:
    ids = [
        r[0] for r in db.query(ChapterRevision.id)
        .filter(ChapterRevision.chapter_id == chapter_id)
        .order_by(ChapterRevision.created_at.desc(), ChapterRevision.id.desc())
        .offset(MAX_REVISIONS)
        .all()
    ]
    if ids:
        db.query(ChapterRevision).filter(ChapterRevision.id.in_(ids)).delete(
            synchronize_session=False
        )


def _remove_from_graph(comic_id: int, number: float) -> None:
    from libs.story_graph.ingest import delete_chapter

    try:
        delete_chapter(comic_id, number)
    except Exception:
        logger.exception("Không gỡ được chương khỏi graph")


# ── Comics ────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[ComicOut])
def list_comics(
    q: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Comic).options(selectinload(Comic.chapters))
    if q:
        query = query.filter(Comic.title.ilike(f"%{q}%"))
    if status:
        query = query.filter(Comic.status == status)
    return query.order_by(Comic.updated_at.desc()).offset(skip).limit(limit).all()


@router.post("/", response_model=ComicOut, status_code=201)
def create_comic(data: ComicCreate, db: Session = Depends(get_db)):
    comic = Comic(**data.model_dump())
    db.add(comic)
    db.commit()
    db.refresh(comic)
    return comic


@router.get("/{comic_id}", response_model=ComicOut)
def get_comic(comic_id: int, db: Session = Depends(get_db)):
    comic = (
        db.query(Comic)
        .options(selectinload(Comic.chapters))
        .filter(Comic.id == comic_id)
        .first()
    )
    if not comic:
        raise HTTPException(status_code=404, detail="Không tìm thấy truyện")
    return comic


@router.put("/{comic_id}", response_model=ComicOut)
def update_comic(comic_id: int, data: ComicUpdate, db: Session = Depends(get_db)):
    comic = _get_comic(db, comic_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(comic, key, value)
    db.commit()
    db.refresh(comic)
    return comic


@router.delete("/{comic_id}", status_code=204)
def delete_comic(comic_id: int, db: Session = Depends(get_db)):
    comic = _get_comic(db, comic_id)
    db.delete(comic)
    db.commit()


# ── Chapters ──────────────────────────────────────────────────────────────────

@router.get("/{comic_id}/chapters", response_model=List[ChapterOut])
def list_chapters(comic_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Chapter)
        .filter(Chapter.comic_id == comic_id)
        .order_by(Chapter.number)
        .all()
    )


@router.post("/{comic_id}/chapters", response_model=ChapterOut, status_code=201)
def create_chapter(comic_id: int, data: ChapterCreate, db: Session = Depends(get_db)):
    _get_comic(db, comic_id)
    chapter = Chapter(comic_id=comic_id, **data.model_dump())
    with _number_conflict_guard(db):
        db.add(chapter)
        _touch_comic(db, comic_id)
    db.refresh(chapter)
    return chapter


@router.get("/{comic_id}/chapters/{chapter_id}", response_model=ChapterDetailOut)
def get_chapter(comic_id: int, chapter_id: int, db: Session = Depends(get_db)):
    return _get_chapter(db, comic_id, chapter_id, full=True)


@router.put("/{comic_id}/chapters/{chapter_id}", response_model=ChapterDetailOut)
def update_chapter(
    comic_id: int,
    chapter_id: int,
    data: ChapterUpdate,
    background_tasks: BackgroundTasks,
    snapshot: bool = False,
    db: Session = Depends(get_db),
):
    """Lưu chương.

    `snapshot=true` (người dùng bấm Lưu / Ctrl+S): ghi thêm một bản vào lịch sử.
    Tự lưu (`snapshot=false`): chụp bản CŨ nếu lần chụp trước đã quá 10 phút —
    viết liền cả buổi rồi lỡ xoá hết vẫn lấy lại được.
    """
    chapter = _get_chapter(db, comic_id, chapter_id, full=True)
    updates = data.model_dump(exclude_unset=True)
    old_number = chapter.number

    content_changed = "content" in updates and updates["content"] != chapter.content

    with _number_conflict_guard(db):
        # Lịch sử ghi TRƯỚC khi sửa chương, để autoflush không đụng số chương mới
        if content_changed:
            last = _last_revision_at(db, chapter.id)
            if last is None or datetime.utcnow() - last >= SNAPSHOT_INTERVAL:
                _add_revision(db, chapter.id, chapter.content, "auto")
        if snapshot:
            _add_revision(db, chapter.id, updates.get("content", chapter.content), "manual")
        _prune_revisions(db, chapter.id)

        for key, value in updates.items():
            setattr(chapter, key, value)
        if content_changed or "title" in updates or "number" in updates:
            _touch_comic(db, comic_id)

    if content_changed or ("number" in updates and updates["number"] != old_number):
        enqueue_chapter_analysis(chapter.id, db, background_tasks)

    return _get_chapter(db, comic_id, chapter_id, full=True)


@router.get(
    "/{comic_id}/chapters/{chapter_id}/analysis",
    response_model=Optional[ChapterAnalysisJobOut],
)
def get_latest_chapter_analysis(comic_id: int, chapter_id: int, db: Session = Depends(get_db)):
    _get_chapter(db, comic_id, chapter_id)
    return (
        db.query(ChapterAnalysisJob)
        .filter(ChapterAnalysisJob.chapter_id == chapter_id)
        .order_by(ChapterAnalysisJob.created_at.desc())
        .first()
    )


@router.delete("/{comic_id}/chapters/{chapter_id}", status_code=204)
def delete_chapter(
    comic_id: int,
    chapter_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    chapter = _get_chapter(db, comic_id, chapter_id)
    number = chapter.number
    db.delete(chapter)
    _touch_comic(db, comic_id)
    db.commit()
    if graph_configured():
        background_tasks.add_task(_remove_from_graph, comic_id, float(number))


# ── Revisions ─────────────────────────────────────────────────────────────────

@router.get(
    "/{comic_id}/chapters/{chapter_id}/revisions",
    response_model=List[ChapterRevisionOut],
)
def list_revisions(comic_id: int, chapter_id: int, db: Session = Depends(get_db)):
    _get_chapter(db, comic_id, chapter_id)
    return (
        db.query(ChapterRevision)
        .filter(ChapterRevision.chapter_id == chapter_id)
        .order_by(ChapterRevision.created_at.desc(), ChapterRevision.id.desc())
        .all()
    )


def _get_revision(db: Session, chapter_id: int, revision_id: int) -> ChapterRevision:
    rev = (
        db.query(ChapterRevision)
        .filter(ChapterRevision.id == revision_id, ChapterRevision.chapter_id == chapter_id)
        .first()
    )
    if not rev:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản lưu")
    return rev


@router.get(
    "/{comic_id}/chapters/{chapter_id}/revisions/{revision_id}",
    response_model=ChapterRevisionDetailOut,
)
def get_revision(comic_id: int, chapter_id: int, revision_id: int, db: Session = Depends(get_db)):
    _get_chapter(db, comic_id, chapter_id)
    return _get_revision(db, chapter_id, revision_id)


@router.post(
    "/{comic_id}/chapters/{chapter_id}/revisions/{revision_id}/restore",
    response_model=ChapterDetailOut,
)
def restore_revision(
    comic_id: int,
    chapter_id: int,
    revision_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Khôi phục một bản. Nội dung hiện tại được lưu lại trước — khôi phục nhầm vẫn quay lại được."""
    chapter = _get_chapter(db, comic_id, chapter_id, full=True)
    rev = _get_revision(db, chapter_id, revision_id)
    _add_revision(db, chapter.id, chapter.content, "restore")
    chapter.content = rev.content
    _prune_revisions(db, chapter.id)
    _touch_comic(db, comic_id)
    db.commit()
    enqueue_chapter_analysis(chapter.id, db, background_tasks)
    return _get_chapter(db, comic_id, chapter_id, full=True)


# ── Pages ─────────────────────────────────────────────────────────────────────

@router.get("/{comic_id}/chapters/{chapter_id}/pages", response_model=List[PageOut])
def list_pages(comic_id: int, chapter_id: int, db: Session = Depends(get_db)):
    _get_chapter(db, comic_id, chapter_id)
    return (
        db.query(Page)
        .filter(Page.chapter_id == chapter_id)
        .order_by(Page.order_index)
        .all()
    )


@router.post("/{comic_id}/chapters/{chapter_id}/pages", response_model=PageOut, status_code=201)
def create_page(
    comic_id: int,
    chapter_id: int,
    data: PageCreate,
    db: Session = Depends(get_db),
):
    _get_chapter(db, comic_id, chapter_id)

    if data.order_index is None:
        order_index = db.query(Page).filter(Page.chapter_id == chapter_id).count()
    else:
        order_index = data.order_index

    page = Page(chapter_id=chapter_id, image_url=data.image_url, order_index=order_index)
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


@router.put("/{comic_id}/chapters/{chapter_id}/pages/{page_id}", response_model=PageOut)
def update_page(
    comic_id: int,
    chapter_id: int,
    page_id: int,
    data: PageUpdate,
    db: Session = Depends(get_db),
):
    _get_chapter(db, comic_id, chapter_id)
    page = db.query(Page).filter(Page.id == page_id, Page.chapter_id == chapter_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Không tìm thấy trang")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(page, key, value)
    db.commit()
    db.refresh(page)
    return page


@router.delete("/{comic_id}/chapters/{chapter_id}/pages/{page_id}", status_code=204)
def delete_page(
    comic_id: int,
    chapter_id: int,
    page_id: int,
    db: Session = Depends(get_db),
):
    _get_chapter(db, comic_id, chapter_id)
    page = db.query(Page).filter(Page.id == page_id, Page.chapter_id == chapter_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Không tìm thấy trang")
    db.delete(page)
    db.commit()
