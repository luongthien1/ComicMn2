from fastapi import APIRouter

from .counter import router as counter_router

router = APIRouter()
router.include_router(counter_router)
