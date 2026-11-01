import os
import uuid

from core.config import settings
from fastapi import APIRouter, File, UploadFile
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


@router.get("/files/{file_path:path}")
def get_file(file_path: str):
    path = os.path.join(settings.media_dir, file_path)
    return FileResponse(path)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "")[1] or ".bin"
    filename = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(settings.media_dir, filename)
    os.makedirs(settings.media_dir, exist_ok=True)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    return {"url": f"/api/files/{filename}", "filename": filename}
