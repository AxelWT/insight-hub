import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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


# 静态文件目录
STATIC_DIR = Path(__file__).parent.parent / "frontend" / "dist"

# 挂载静态文件（JS、CSS、图片等）
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    # SPA 路由 - 所有非 API 请求返回 index.html
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        # 如果是 API 或 WebSocket 请求，返回 404
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            raise HTTPException(status_code=404, detail="Not Found")

        # 尝试返回静态文件
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))

        # 否则返回 index.html（SPA 路由）
        return FileResponse(str(STATIC_DIR / "index.html"))
