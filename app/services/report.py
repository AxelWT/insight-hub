from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session

from app.config import settings
from app.models import ResearchTask, Report, Source, AgentLog


def save_sources(
    db: Session, task_id: int, search_results: list[dict], crawled_content: list[dict]
):
    existing_urls = {
        s.url for s in db.query(Source).filter(Source.task_id == task_id).all()
    }
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
            relevance_score=r.get("relevance_score"),
            search_round=r.get("search_round", 1),
        )
        db.add(source)
        existing_urls.add(url)
    db.commit()


def save_agent_log(db: Session, task_id: int, log_entry: dict):
    log = AgentLog(
        task_id=task_id,
        agent_name=log_entry.get("agent", ""),
        step=log_entry.get("step", ""),
        input_data=log_entry.get("input"),
        output_data=log_entry.get("output")
        if not isinstance(log_entry.get("output"), str)
        else {"text": log_entry["output"]},
        decision=log_entry.get("decision", ""),
    )
    db.add(log)
    db.commit()


def update_task_status(
    db: Session,
    task_id: int,
    status: str,
    current_step: str = "",
    progress: int | None = None,
    search_rounds: int | None = None,
):
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


def get_report(db: Session, task_id: int) -> Report | None:
    return db.query(Report).filter(Report.task_id == task_id).first()


def delete_report(db: Session, task_id: int) -> bool:
    report = get_report(db, task_id)
    if not report:
        return False
    if report.file_path:
        Path(report.file_path).unlink(missing_ok=True)
    db.delete(report)
    db.commit()
    return True


def export_markdown(task_id: int, topic: str, content: str) -> str:
    filename = f"report_{task_id}_{_safe_filename(topic)}.md"
    path = Path(settings.report_output_dir) / filename
    path.write_text(content, encoding="utf-8")
    return str(path)


def _save_markdown_file(task_id: int, topic: str, content: str) -> str:
    filename = f"report_{task_id}_{_safe_filename(topic)}.md"
    path = Path(settings.report_output_dir) / filename
    path.write_text(content, encoding="utf-8")
    return str(path)


def _safe_filename(name: str) -> str:
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in name[:50])
