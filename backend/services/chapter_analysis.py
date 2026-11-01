from datetime import datetime

from db.model.ai_settings import AiSettings
from db.model.chapter import Chapter
from db.model.chapter_analysis_job import ChapterAnalysisJob
from libs.database.connect import SessionMaker
from libs.logger.log import get_logger
from libs.mcp_client.client import McpClientError, mcp_client

logger = get_logger(__name__)


async def run_chapter_analysis(job_id: int):
    """Chạy nền: ingest_chapter (+ check_chapter ở Phase 4) qua comic-graphrag-mcp, cập nhật job."""
    db = SessionMaker()
    try:
        job = db.query(ChapterAnalysisJob).filter(ChapterAnalysisJob.id == job_id).first()
        if not job:
            return

        chapter = db.query(Chapter).filter(Chapter.id == job.chapter_id).first()
        if not chapter:
            job.status = "error"
            job.error_message = "Không tìm thấy chương."
            job.finished_at = datetime.utcnow()
            db.commit()
            return

        ai_settings = db.query(AiSettings).filter(AiSettings.id == 1).first()
        ollama_endpoint = ai_settings.ollama_endpoint if ai_settings else None
        ollama_model = ai_settings.ollama_model if ai_settings else "qwen2.5:14b"

        if not ollama_endpoint:
            job.status = "error"
            job.error_message = "Chưa cấu hình Ollama endpoint (vào trang Cài đặt)."
            job.finished_at = datetime.utcnow()
            db.commit()
            return

        job.status = "running"
        db.commit()

        try:
            ingest_result = await mcp_client.call_tool(
                "ingest_chapter",
                {
                    "comic_id": chapter.comic_id,
                    "chapter_id": chapter.id,
                    "chapter_number": chapter.number,
                    "title": chapter.title,
                    "content_html": chapter.content or "",
                    "ollama_endpoint": ollama_endpoint,
                    "ollama_model": ollama_model,
                },
            )
        except McpClientError as e:
            job.status = "error"
            job.error_message = str(e)
            job.finished_at = datetime.utcnow()
            db.commit()
            return

        job.ingest_result = ingest_result
        if ingest_result.get("status") == "error":
            job.status = "error"
            job.error_message = ingest_result.get("error_message")
        else:
            job.status = "done"
        job.finished_at = datetime.utcnow()
        db.commit()

    except Exception:
        logger.exception("Loi khong xac dinh khi chay chapter analysis job")
        try:
            job = db.query(ChapterAnalysisJob).filter(ChapterAnalysisJob.id == job_id).first()
            if job:
                job.status = "error"
                job.error_message = "Lỗi hệ thống không xác định."
                job.finished_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
