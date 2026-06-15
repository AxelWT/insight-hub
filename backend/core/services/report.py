"""
报告的存储和管理
提供调研的来源、Agent 日志、报告的持久化操作以及 Markdown 文件导出功能
"""

import logging
from pathlib import Path
from datetime import datetime

from core.config import settings
from sqlalchemy.orm import Session
from core.models import ResearchTask, Report, Source, AgentLog

logger = logging.getLogger(__name__)


def _safe_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in name[:50])


def _save_markdown_file(task_id: int, topic: str, content: str) -> str:
    filename = f"report_{task_id}_{_safe_filename(topic)}.md"
    path = Path(settings.report_output_dir) / filename
    path.write_text(content, encoding="utf-8")
    return str(path)


def save_sources(db: Session, task_id: int, search_results: list[dict], crawled_content: list[dict]):
    existing_urls = {s.url for s in db.query(Source).filter(Source.task_id == task_id).all()}
    url_to_content = {c.get("url", ""): c.get("content", "") for c in crawled_content}

    for r in search_results:
        url = r.get("url", "")
        if not url or url in existing_urls:
            continue
        source = Source(
            task_id=task_id,
            url=url,
            title=r.get("title", ""),
            snippet=r.get("snippet", "")[:1000],
            content=url_to_content.get(url, "")[:8000],
            relevance_score=r.get("relevance_score", 0),
            search_round=r.get("search_round", 1),
        )
        db.add(source)
        existing_urls.add(url)
    db.commit()


def save_agent_log(db: Session, task_id: int, log_entry: dict):
    """
    保存一条 Agent 执行日志
    db:数据库会话
    task_id:关联的任务 Id
    log_entry:日志条目，包含 Agent、step、input、output、decision 等字段
    """
    log = AgentLog(
        task_id=task_id,
        agent_name=log_entry.get("agent", ""),
        step=log_entry.get("step", ""),
        input_data=log_entry.get("input"),
        output_data=log_entry.get("output")
        if not isinstance(log_entry.get("output"), str) else {"text": log_entry.get("output")},
        decision=log_entry.get("decision", ""),
    )
    db.add(log)
    db.commit()


def update_task_status(db: Session, task_id: int, status: str,
                       current_step: str = "", progress: int | None = None,
                       search_rounds: int | None = None):
    """
    更新任务状态
    """
    task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
    if not task:
        return
    task.status = status
    if current_step:
        task.current_step = current_step
    if progress is not None:
        task.progress = progress
    if search_rounds is not None:
        task.search_rounds = search_rounds
    db.commit()


def save_report(db: Session, task_id: int, content: str) -> Report:
    """
    保存调研报告并更新任务状态为已完成
    """
    task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
    if not task:
        raise ValueError(f"Task {task_id} not found")

    file_path = _save_markdown_file(task_id, task.topic, content)
    word_count = len(content)
    source_count = len(task.sources)
    report = Report(
        task_id=task_id,
        content=content,
        word_count=word_count,
        source_count=source_count,
        file_path=file_path,
    )
    db.add(report)

    task.status = "completed"
    task.progress = 100
    task.completed_at = datetime.now()
    db.commit()
    db.refresh(report)
    return report


def get_report(db: Session, task_id: int) -> type[Report] | None:
    return db.query(Report).filter(Report.task_id == task_id).first()


def delete_report(db: Session, task_id: int) -> bool:
    report = db.query(Report).filter(Report.task_id == task_id).first()
    if not report:
        return False
    if report.file_path:
        Path(report.file_path).unlink(missing_ok=True)
    db.delete(report)
    db.commit()
    return True
