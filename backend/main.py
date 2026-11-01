from contextlib import asynccontextmanager

from api import router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from libs.story_graph import get_retriever
from services.chapter_analysis import fail_interrupted_jobs


@asynccontextmanager
async def lifespan(app: FastAPI):
    await run_in_threadpool(fail_interrupted_jobs)
    yield
    get_retriever().close()


app = FastAPI(title="ComicMn2", lifespan=lifespan)

# Include REST API
app.include_router(router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn

    # Chỉ nghe localhost — API không có xác thực
    uvicorn.run(app, host="127.0.0.1", port=8010)
