from contextlib import asynccontextmanager

from api import router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from libs.mcp_client.client import mcp_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    await mcp_client.start()
    yield
    await mcp_client.stop()


app = FastAPI(title="My FastAPI App", lifespan=lifespan)

# Include REST API
app.include_router(router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010)
