"""数据模型定义模块

定义了四个核心 ORM 模型：ResearchTask（调研任务）、Source（信息来源）、
AgentLog（Agent 执行日志）、Report（调研报告），以及相关的枚举类型。
"""

import enum
from datetime import datetime

from sqlalchemy import String, Text, Integer, Float, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class TaskType(str, enum.Enum):
    """任务类型枚举"""

    SEARCH = "search"  # 主题搜索调研
    WEBSITE = "website"  # 网站内容调研


class TaskStatus(str, enum.Enum):
    """任务状态枚举，贯穿调研全生命周期"""

    PENDING = "pending"  # 等待启动
    PLANNING = "planning"  # 正在规划搜索策略
    SEARCHING = "searching"  # 正在搜索信息
    CRAWLING = "crawling"  # 正在爬取网页
    EVALUATING = "evaluating"  # 正在评估信息充分性
    WRITING = "writing"  # 正在撰写报告
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 执行失败


class ResearchDepth(str, enum.Enum):
    """调研深度枚举"""

    QUICK = "quick"  # 快速：1 轮搜索
    STANDARD = "standard"  # 标准：2-3 轮搜索
    DEEP = "deep"  # 深度：3-5 轮搜索


class ResearchTask(Base):
    """调研任务模型，存储每次调研的核心信息"""

    __tablename__ = "research_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str] = mapped_column(String(500))  # 调研主题
    description: Mapped[str] = mapped_column(Text, default="")  # 补充说明
    model: Mapped[str] = mapped_column(String(100))  # 使用的 AI 模型标识
    depth: Mapped[str] = mapped_column(String(20), default="standard")  # 调研深度
    task_type: Mapped[str] = mapped_column(
        String(20), default=TaskType.SEARCH
    )  # 任务类型
    urls: Mapped[list | None] = mapped_column(
        JSON, default=list
    )  # 网站调研的目标 URL 列表
    questions: Mapped[str | None] = mapped_column(
        Text, default=""
    )  # 网站调研的用户问题
    crawl_depth: Mapped[int] = mapped_column(Integer, default=1)  # 网站爬取深度（层数）
    max_pages: Mapped[int] = mapped_column(Integer, default=20)  # 网站爬取最大页面数
    status: Mapped[str] = mapped_column(
        String(20), default=TaskStatus.PENDING
    )  # 当前状态
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 进度百分比（0-100）
    current_step: Mapped[str] = mapped_column(Text, default="")  # 当前步骤描述
    search_rounds: Mapped[int] = mapped_column(Integer, default=0)  # 已完成搜索轮次
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now
    )  # 创建时间
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )  # 完成时间
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # 失败时的错误信息

    # 关联关系：任务 → 来源列表，级联删除
    sources: Mapped[list["Source"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    # 关联关系：任务 → Agent 日志列表，级联删除
    agent_logs: Mapped[list["AgentLog"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )
    # 关联关系：任务 → 报告（一对一），级联删除
    report: Mapped["Report | None"] = relationship(
        back_populates="task", uselist=False, cascade="all, delete-orphan"
    )


class Source(Base):
    """信息来源模型，存储搜索结果和爬取内容"""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("research_tasks.id"))  # 所属任务 ID
    url: Mapped[str] = mapped_column(String(2000))  # 来源 URL
    title: Mapped[str] = mapped_column(String(500), default="")  # 页面标题
    snippet: Mapped[str] = mapped_column(Text, default="")  # 搜索摘要
    content: Mapped[str] = mapped_column(Text, default="")  # 爬取的正文内容
    relevance_score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # 相关性评分
    search_round: Mapped[int] = mapped_column(Integer, default=1)  # 所属搜索轮次
    crawled_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now
    )  # 爬取时间

    # 反向关联：来源 → 任务
    task: Mapped["ResearchTask"] = relationship(back_populates="sources")


class AgentLog(Base):
    """Agent 执行日志模型，记录每个 Agent 的决策和输入输出"""

    __tablename__ = "agent_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("research_tasks.id"))  # 所属任务 ID
    agent_name: Mapped[str] = mapped_column(String(50))  # Agent 名称
    step: Mapped[str] = mapped_column(String(100))  # 执行步骤描述
    input_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 输入数据
    output_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 输出数据
    decision: Mapped[str] = mapped_column(Text, default="")  # Agent 的决策说明
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now
    )  # 记录时间

    # 反向关联：日志 → 任务
    task: Mapped["ResearchTask"] = relationship(back_populates="agent_logs")


class Report(Base):
    """调研报告模型，存储最终生成的报告内容"""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("research_tasks.id"), unique=True
    )  # 关联任务（唯一）
    content: Mapped[str] = mapped_column(Text)  # 报告 Markdown 正文
    word_count: Mapped[int] = mapped_column(Integer, default=0)  # 字数统计
    source_count: Mapped[int] = mapped_column(Integer, default=0)  # 引用来源数
    file_path: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )  # 导出文件路径

    # 反向关联：报告 → 任务·
    task: Mapped["ResearchTask"] = relationship(back_populates="report")
