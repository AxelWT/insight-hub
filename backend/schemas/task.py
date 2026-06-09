"""任务相关 Pydantic 模型

定义任务创建请求和响应的数据结构。
"""

from datetime import datetime
from pydantic import BaseModel


class TaskCreate(BaseModel):
    """创建任务请求模型"""

    topic: str  # 调研主题
    description: str = ""  # 补充说明
    model: str = "deepseek"  # AI 模型标识
    depth: str = "standard"  # 调研深度（quick/standard/deep）
    task_type: str = "search"  # 任务类型（search/website）
    urls: list[str] = []  # 网站调研的目标 URL 列表
    questions: str = ""  # 网站调研的用户问题
    crawl_depth: int = 1  # 网站爬取深度
    max_pages: int = 20  # 最大爬取页面数


class TaskResponse(BaseModel):
    """任务响应模型"""

    id: int
    topic: str
    description: str
    model: str
    depth: str
    task_type: str
    urls: list[str]
    questions: str
    crawl_depth: int
    max_pages: int
    status: str  # 当前状态
    progress: int  # 进度百分比
    current_step: str  # 当前步骤描述
    search_rounds: int  # 已完成搜索轮次
    created_at: datetime  # 创建时间
    completed_at: datetime | None = None  # 完成时间
    error_message: str | None = None  # 错误信息

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    """任务列表响应模型"""

    tasks: list[TaskResponse]
