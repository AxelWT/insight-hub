import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.database import init_db
from backend.core.runner import set_broadcaster
from backend.api.tasks import router as tasks_router
from backend.api.reports import router as reports_router
from backend.api.config import router as config_router
from backend.api.websocket import router as ws_router, broadcast


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    set_broadcaster(broadcast)
    yield


app = FastAPI(title="AI 调研平台", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router)
app.include_router(reports_router)
app.include_router(config_router)
app.include_router(ws_router)
