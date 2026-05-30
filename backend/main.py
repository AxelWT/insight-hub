import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

from core.database import init_db
from core.runner import set_broadcaster
from core.logging_config import setup_logging
from core.exceptions import (
    AppError,
    app_error_handler,
    http_error_handler,
    sqlalchemy_error_handler,
    general_error_handler,
)
from api.tasks import router as tasks_router
from api.reports import router as reports_router
from api.config import router as config_router
from api.websocket import router as ws_router, broadcast

# 初始化日志系统
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path("./data").mkdir(exist_ok=True)
    init_db()
    set_broadcaster(broadcast)
    logger.info("AI 调研平台启动完成")
    yield


app = FastAPI(title="AI 调研平台", lifespan=lifespan)

# 注册异常处理器
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(HTTPException, http_error_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
app.add_exception_handler(Exception, general_error_handler)

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


@app.get("/health")
async def health_check():
    return {"status": "ok"}
