"""Cập nhật đồ thị truyện sau khi lưu chương (chạy nền).

Trước: mỗi lần lưu tạo một job gọi comic-graphrag-mcp (subprocess riêng, chưa
từng chạy thành công). Lưu 5 lần = 5 job song song.

Giờ:
  - Dùng `libs.story_graph` — cùng graph mà chat/kiểm mâu thuẫn đọc.
  - Mỗi chương tối đa MỘT job `pending`. Lưu thêm khi đã có job chờ thì bỏ qua:
    job chờ sẽ đọc nội dung MỚI NHẤT lúc chạy.
  - Job đợi ANALYSIS_DELAY giây trước khi chạy để gộp loạt tự lưu liên tiếp.
  - Khoá theo chương: hai job cùng chương không bao giờ chạy song song.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from datetime import datetime

from db.model.chapter import Chapter
from db.model.chapter_analysis_job import ChapterAnalysisJob
from fastapi import BackgroundTasks
from libs.database.connect import SessionMaker
from libs.logger.log import get_logger
from libs.story_graph.ingest import graph_configured, ingest_chapter, strip_html
from sqlalchemy.orm import Session

logger = get_logger(__name__)

ANALYSIS_DELAY = 20.0

_locks: dict[int, threading.Lock] = defaultdict(threading.Lock)
_locks_guard = threading.Lock()


def _chapter_lock(chapter_id: int) -> threading.Lock:
    with _locks_guard:
        return _locks[chapter_id]


def enqueue_chapter_analysis(
    chapter_id: int, db: Session, background_tasks: BackgroundTasks
) -> bool:
    """Xếp hàng cập nhật graph cho chương. Trả False nếu không cần tạo job mới."""
    if not graph_configured():
        return False

    pending = (
        db.query(ChapterAnalysisJob.id)
        .filter(
            ChapterAnalysisJob.chapter_id == chapter_id,
            ChapterAnalysisJob.status == "pending",
        )
        .first()
    )
    if pending:
        return False

    job = ChapterAnalysisJob(chapter_id=chapter_id, status="pending")
    db.add(job)
    db.commit()
    background_tasks.add_task(run_chapter_analysis, job.id, chapter_id)
    return True


def run_chapter_analysis(job_id: int, chapter_id: int, delay: float | None = None) -> None:
    """Chạy trong threadpool của FastAPI (hàm sync)."""
    time.sleep(ANALYSIS_DELAY if delay is None else delay)

    with _chapter_lock(chapter_id):
        db = SessionMaker()
        try:
            _run_locked(db, job_id)
        except Exception as e:
            logger.exception("Lỗi khi cập nhật graph cho chương")
            db.rollback()
            job = db.get(ChapterAnalysisJob, job_id)
            if job is not None:
                job.status = "error"
                job.error_message = str(e)[:2000]
                job.finished_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()


def _run_locked(db: Session, job_id: int) -> None:
    job = db.get(ChapterAnalysisJob, job_id)
    if job is None or job.status != "pending":
        return

    chapter = db.get(Chapter, job.chapter_id)
    if chapter is None:
        return  # chương đã xoá — job cũng bị xoá theo (ON DELETE CASCADE)

    job.status = "running"
    db.commit()

    rows = (
        db.query(Chapter.id, Chapter.number, Chapter.title, Chapter.content)
        .filter(Chapter.comic_id == chapter.comic_id)
        .order_by(Chapter.number)
        .all()
    )
    all_chapters = [
        {"id": r.id, "number": float(r.number), "title": r.title or "",
         "text": strip_html(r.content or "")}
        for r in rows
    ]
    this = next(c for c in all_chapters if c["id"] == chapter.id)

    job.ingest_result = ingest_chapter(chapter.comic_id, this, all_chapters)
    job.status = "done"
    job.finished_at = datetime.utcnow()
    db.commit()


def fail_interrupted_jobs() -> None:
    """Job đang chờ/chạy khi backend tắt sẽ không bao giờ xong — đánh dấu lỗi."""
    db = SessionMaker()
    try:
        n = (
            db.query(ChapterAnalysisJob)
            .filter(ChapterAnalysisJob.status.in_(["pending", "running"]))
            .update(
                {
                    "status": "error",
                    "error_message": "Bị ngắt do backend khởi động lại.",
                    "finished_at": datetime.utcnow(),
                },
                synchronize_session=False,
            )
        )
        db.commit()
        if n:
            logger.info(f"Đánh dấu {n} job phân tích bị ngắt")
    except Exception:
        logger.exception("Không dọn được job cũ")
    finally:
        db.close()
