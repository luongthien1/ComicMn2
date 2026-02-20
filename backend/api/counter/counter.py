from fastapi import APIRouter
from schemas.counter import Counter

router = APIRouter()


@router.get("/")
def step(current: int, step: int):
    counter = Counter(current=current + step, step=step)
    return counter
