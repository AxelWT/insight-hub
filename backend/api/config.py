"""配置查询 API

提供前端所需的模型列表等配置信息。
"""

from fastapi import APIRouter
from core.config import settings

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/models")
def get_models():
    """获取当前可用的 AI 模型列表

    根据用户配置的 API Key 动态返回可用模型，
    前端据此渲染模型选择下拉框。
    """
    return {"models": settings.available_models}
