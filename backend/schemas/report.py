"""报告相关 Pydantic 响应模型

定义 API 返回的数据结构，通过 from_attributes=True
支持直接从 SQLAlchemy ORM 对象转换。
"""

from datetime import datetime
from pydantic import BaseModel


class SourceResponse(BaseModel):
    """信息来源响应模型"""

    id: int
    url: str
    title: str
    snippet: str  # 搜索摘要
    content: str  # 爬取的正文
    relevance_score: float | None = None  # 相关性评分（可为空）
    search_round: int  # 所属搜索轮次
    crawled_at: datetime  # 爬取时间

    model_config = {"from_attributes": True}


class AgentLogResponse(BaseModel):
    """Agent 执行日志响应模型"""

    id: int
    agent_name: str  # Agent 名称
    step: str  # 执行步骤
    input_data: dict | None = None  # 输入数据
    output_data: list | dict | None = None  # 输出数据
    decision: str  # 决策说明
    timestamp: datetime  # 记录时间

    model_config = {"from_attributes": True}


class ReportResponse(BaseModel):
    """调研报告响应模型"""

    id: int
    task_id: int  # 关联任务 ID
    content: str  # Markdown 正文
    word_count: int  # 字数统计
    source_count: int  # 引用来源数
    file_path: str | None = None  # 导出文件路径

    model_config = {"from_attributes": True}
