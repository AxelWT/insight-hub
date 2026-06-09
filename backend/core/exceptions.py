"""自定义异常和全局错误处理

定义应用层异常体系，并注册 FastAPI 全局异常处理器，
确保所有错误都以统一的 JSON 格式返回给前端。
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class AppError(Exception):
    """应用基础异常类

    所有业务异常都应继承此类，提供统一的错误码和 HTTP 状态码。
    """

    def __init__(self, message: str, code: str = "APP_ERROR", status_code: int = 400):
        self.message = message  # 用户可读的错误描述
        self.code = code  # 机器可读的错误码
        self.status_code = status_code  # HTTP 状态码
        super().__init__(message)


class NotFoundError(AppError):
    """资源不存在异常（404）"""

    def __init__(self, resource: str, resource_id: int | str = None):
        msg = f"{resource}不存在"
        if resource_id:
            msg = f"{resource} (ID: {resource_id}) 不存在"
        super().__init__(message=msg, code="NOT_FOUND", status_code=404)


class ValidationError(AppError):
    """数据验证异常（422）"""

    def __init__(self, message: str):
        super().__init__(message=message, code="VALIDATION_ERROR", status_code=422)


class ExternalServiceError(AppError):
    """外部服务调用异常（502），如 AI API 调用失败"""

    def __init__(self, service: str, message: str = "服务调用失败"):
        super().__init__(
            message=f"{service}: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
        )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """处理自定义应用异常，返回统一格式的错误响应"""
    logger.warning(f"AppError: {exc.code} - {exc.message} | Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
            },
        },
    )


async def http_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """处理 FastAPI 内置 HTTP 异常，统一返回格式"""
    logger.warning(f"HTTPException: {exc.status_code} - {exc.detail} | Path: {request.url.path}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
            },
        },
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """处理数据库异常，避免暴露数据库细节给前端"""
    logger.error(f"SQLAlchemyError: {exc} | Path: {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "DATABASE_ERROR",
                "message": "数据库操作失败，请稍后重试",
            },
        },
    )


async def general_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理所有未捕获的异常，作为最后的兜底"""
    logger.error(f"UnhandledException: {type(exc).__name__}: {exc} | Path: {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误，请稍后重试",
            },
        },
    )
