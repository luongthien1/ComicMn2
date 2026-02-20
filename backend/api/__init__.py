import os

from core.config import Settings
from fastapi import APIRouter
from fastapi.responses import FileResponse

from .counter import router as counter_router

router = APIRouter()
router.include_router(counter_router, prefix="/counter", tags=["Counter"])


@router.get("/files/{file_path}")
def get_image(file_path: str):
    path = os.path.join(Settings.media_dir, file_path)
    return FileResponse(path)
