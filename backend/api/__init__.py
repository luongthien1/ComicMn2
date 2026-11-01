import os
import uuid
from pathlib import Path

from core.config import settings
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from .ai import router as ai_router
from .ai_settings import router as ai_settings_router
from .comics import router as comics_router
from .counter import router as counter_router

router = APIRouter()
router.include_router(counter_router, prefix="/counter", tags=["Counter"])
router.include_router(comics_router, prefix="/comics", tags=["Comics"])
router.include_router(ai_router, prefix="/ai", tags=["AI"])
router.include_router(ai_settings_router, prefix="/ai-settings", tags=["AI Settings"])

# Chỉ nhận ảnh — upload dùng cho ảnh bìa và ảnh chèn trong chương
ALLOWED_UPLOAD_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".bmp"}
_CHUNK = 1024 * 1024


def _media_root() -> Path:
    return Path(settings.media_dir).resolve()


@router.get("/files/{file_path:path}")
def get_file(file_path: str):
    root = _media_root()
    path = (root / file_path).resolve()
    # Chặn "../" — trước đây /api/files/../.env đọc được file cấu hình chứa khoá API
    if not path.is_relative_to(root) or not path.is_file():
        raise HTTPException(status_code=404, detail="Không tìm thấy file")
    return FileResponse(path)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_UPLOAD_EXT:
        raise HTTPException(
            status_code=415,
            detail=f"Chỉ nhận ảnh ({', '.join(sorted(ALLOWED_UPLOAD_EXT))}).",
        )
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="File không phải ảnh.")

    root = _media_root()
    root.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    path = root / filename
    limit = settings.MAX_UPLOAD_MB * 1024 * 1024

    size = 0
    try:
        with open(path, "wb") as f:
            while chunk := await file.read(_CHUNK):
                size += len(chunk)
                if size > limit:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File quá lớn (tối đa {settings.MAX_UPLOAD_MB} MB).",
                    )
                f.write(chunk)
    except BaseException:
        path.unlink(missing_ok=True)
        raise

    return {"url": f"/api/files/{filename}", "filename": filename}
