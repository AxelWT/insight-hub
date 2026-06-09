"""FastAPI 应用入口

初始化 Web 应用、注册路由和中间件、配置 SPA 静态文件托管。
"""

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

# 初始化日志系统（最先执行，确保后续操作有日志记录）
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化资源，关闭时清理"""
    # 确保数据目录存在（SQLite 数据库文件存放位置）
    Path("./data").mkdir(exist_ok=True)
    # 初始化数据库表结构
    init_db()
    # 将 WebSocket 广播函数注入到任务运行器，使运行器能推送实时进度
    set_broadcaster(broadcast)
    logger.info("AI 调研平台启动完成")
    yield


# 创建 FastAPI 应用实例
app = FastAPI(title="AI 调研平台", lifespan=lifespan)

# 注册全局异常处理器，按从具体到通用的顺序匹配
app.add_exception_handler(AppError, app_error_handler)  # 业务异常
app.add_exception_handler(HTTPException, http_error_handler)  # HTTP 异常
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)  # 数据库异常
app.add_exception_handler(Exception, general_error_handler)  # 兜底异常

# 配置 CORS 中间件，允许前端开发服务器跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册各功能模块的路由
app.include_router(tasks_router)  # 任务管理
app.include_router(reports_router)  # 报告查询
app.include_router(config_router)  # 配置查询
app.include_router(ws_router)  # WebSocket 实时通信


@app.get("/health")
async def health_check():
    """健康检查接口，供 Docker 健康检查和监控使用"""
    return {"status": "ok"}


# 前端构建产物的目录路径
STATIC_DIR = Path(__file__).parent.parent / "frontend" / "dist"

# 仅当前端构建产物存在时，启用静态文件服务和 SPA 路由
if STATIC_DIR.exists():
    # 挂载 assets 子目录（JS、CSS、图片等静态资源）
    app.mount(
        "/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets"
    )

    # SPA 路由兜底：所有非 API/WS 请求都返回 index.html，由前端路由处理
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        # API 和 WebSocket 请求不应被 SPA 兜底拦截，直接返回 404
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            raise HTTPException(status_code=404, detail="Not Found")

        # 尝试匹配真实静态文件（如 favicon.ico、robots.txt）
        file_path = STATIC_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))

        # 其他所有路径返回 index.html，交由 Vue Router 处理
        return FileResponse(str(STATIC_DIR / "index.html"))
