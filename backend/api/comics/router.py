from typing import List, Optional

from db.model.chapter import Chapter
from db.model.chapter_analysis_job import ChapterAnalysisJob
from db.model.comic import Comic
from db.model.page import Page
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from libs.database.connect import get_db
from schemas.chapter_analysis import ChapterAnalysisJobOut
from schemas.comic import (
    ChapterCreate,
    ChapterDetailOut,
    ChapterOut,
    ChapterUpdate,
    ComicCreate,
    ComicOut,
    ComicUpdate,
    PageCreate,
    PageOut,
    PageUpdate,
)
from services.chapter_analysis import run_chapter_analysis
from sqlalchemy.orm import Session

router = APIRouter()


def _enqueue_chapter_analysis(chapter_id: int, db: Session, background_tasks: BackgroundTasks):
    job = ChapterAnalysisJob(chapter_id=chapter_id, status="pending")
    db.add(job)
    db.commit()
    db.refresh(job)
    background_tasks.add_task(run_chapter_analysis, job.id)


# ── Comics ────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[ComicOut])
def list_comics(
    q: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(Comic)
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
    comic = db.query(Comic).filter(Comic.id == comic_id).first()
    if not comic:
        raise HTTPException(status_code=404, detail="Không tìm thấy truyện")
    return comic


@router.put("/{comic_id}", response_model=ComicOut)
def update_comic(comic_id: int, data: ComicUpdate, db: Session = Depends(get_db)):
    comic = db.query(Comic).filter(Comic.id == comic_id).first()
    if not comic:
        raise HTTPException(status_code=404, detail="Không tìm thấy truyện")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(comic, key, value)
    db.commit()
    db.refresh(comic)
    return comic


@router.delete("/{comic_id}", status_code=204)
def delete_comic(comic_id: int, db: Session = Depends(get_db)):
    comic = db.query(Comic).filter(Comic.id == comic_id).first()
    if not comic:
        raise HTTPException(status_code=404, detail="Không tìm thấy truyện")
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
    if not db.query(Comic).filter(Comic.id == comic_id).first():
        raise HTTPException(status_code=404, detail="Không tìm thấy truyện")
    chapter = Chapter(comic_id=comic_id, **data.model_dump())
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter


@router.get("/{comic_id}/chapters/{chapter_id}", response_model=ChapterDetailOut)
def get_chapter(comic_id: int, chapter_id: int, db: Session = Depends(get_db)):
    chapter = (
        db.query(Chapter)
        .filter(Chapter.id == chapter_id, Chapter.comic_id == comic_id)
        .first()
    )
    if not chapter:
        raise HTTPException(status_code=404, detail="Không tìm thấy chương")
    return chapter


@router.put("/{comic_id}/chapters/{chapter_id}", response_model=ChapterDetailOut)
def update_chapter(
    comic_id: int,
    chapter_id: int,
    data: ChapterUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    chapter = (
        db.query(Chapter)
        .filter(Chapter.id == chapter_id, Chapter.comic_id == comic_id)
        .first()
    )
    if not chapter:
        raise HTTPException(status_code=404, detail="Không tìm thấy chương")
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(chapter, key, value)
    db.commit()
    db.refresh(chapter)

    if "content" in updates:
        _enqueue_chapter_analysis(chapter.id, db, background_tasks)

    return chapter


@router.get(
    "/{comic_id}/chapters/{chapter_id}/analysis",
    response_model=Optional[ChapterAnalysisJobOut],
)
def get_latest_chapter_analysis(comic_id: int, chapter_id: int, db: Session = Depends(get_db)):
    return (
        db.query(ChapterAnalysisJob)
        .filter(ChapterAnalysisJob.chapter_id == chapter_id)
        .order_by(ChapterAnalysisJob.created_at.desc())
        .first()
    )


@router.delete("/{comic_id}/chapters/{chapter_id}", status_code=204)
def delete_chapter(comic_id: int, chapter_id: int, db: Session = Depends(get_db)):
    chapter = (
        db.query(Chapter)
        .filter(Chapter.id == chapter_id, Chapter.comic_id == comic_id)
        .first()
    )
    if not chapter:
        raise HTTPException(status_code=404, detail="Không tìm thấy chương")
    db.delete(chapter)
    db.commit()


# ── Pages ─────────────────────────────────────────────────────────────────────

@router.get("/{comic_id}/chapters/{chapter_id}/pages", response_model=List[PageOut])
def list_pages(comic_id: int, chapter_id: int, db: Session = Depends(get_db)):
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
    chapter = (
        db.query(Chapter)
        .filter(Chapter.id == chapter_id, Chapter.comic_id == comic_id)
        .first()
    )
    if not chapter:
        raise HTTPException(status_code=404, detail="Không tìm thấy chương")

    if data.order_index is None:
        max_order = (
            db.query(Page)
            .filter(Page.chapter_id == chapter_id)
            .count()
        )
        order_index = max_order
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
    page = db.query(Page).filter(Page.id == page_id, Page.chapter_id == chapter_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Không tìm thấy trang")
    db.delete(page)
    db.commit()
