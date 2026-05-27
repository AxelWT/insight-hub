import enum
from datetime import datetime

from sqlalchemy import String, Text, Integer, Float, DateTime, Enum, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.core.database import Base


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    PLANNING = "planning"
    SEARCHING = "searching"
    EVALUATING = "evaluating"
    WRITING = "writing"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchDepth(str, enum.Enum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class ResearchTask(Base):
    __tablename__ = "research_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    model: Mapped[str] = mapped_column(String(100))
    depth: Mapped[str] = mapped_column(String(20), default="standard")
    status: Mapped[str] = mapped_column(String(20), default=TaskStatus.PENDING)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[str] = mapped_column(Text, default="")
    search_rounds: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    sources: Mapped[list["Source"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    agent_logs: Mapped[list["AgentLog"]] = relationship(back_populates="task", cascade="all, delete-orphan")
    report: Mapped["Report | None"] = relationship(back_populates="task", uselist=False, cascade="all, delete-orphan")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("research_tasks.id"))
    url: Mapped[str] = mapped_column(String(2000))
    title: Mapped[str] = mapped_column(String(500), default="")
    snippet: Mapped[str] = mapped_column(Text, default="")
    content: Mapped[str] = mapped_column(Text, default="")
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    search_round: Mapped[int] = mapped_column(Integer, default=1)
    crawled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    task: Mapped["ResearchTask"] = relationship(back_populates="sources")


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("research_tasks.id"))
    agent_name: Mapped[str] = mapped_column(String(50))
    step: Mapped[str] = mapped_column(String(100))
    input_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    decision: Mapped[str] = mapped_column(Text, default="")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    task: Mapped["ResearchTask"] = relationship(back_populates="agent_logs")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("research_tasks.id"), unique=True)
    content: Mapped[str] = mapped_column(Text)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    task: Mapped["ResearchTask"] = relationship(back_populates="report")
