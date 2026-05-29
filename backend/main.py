import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.database import init_db
from backend.core.runner import set_broadcaster
from backend.api.tasks import router as tasks_router
from backend.api.reports import router as reports_router
from backend.api.config import router as config_router
from backend.api.websocket import router as ws_router, broadcast

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path("./data").mkdir(exist_ok=True)
    init_db()
    set_broadcaster(broadcast)
    logger.info("AI 调研平台启动完成")
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
