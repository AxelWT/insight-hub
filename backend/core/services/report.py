"""报告存储与管理服务

提供调研来源、Agent 日志、报告的持久化操作，
以及 Markdown 文件导出功能。
"""

from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session

from core.config import settings
from core.models import ResearchTask, Report, Source, AgentLog


def save_sources(
    db: Session, task_id: int, search_results: list[dict], crawled_content: list[dict]
):
    """保存搜索结果和爬取内容为来源记录

    自动去重：已存在的 URL 不会重复插入。
    将爬取的正文内容与搜索结果通过 URL 关联。

    Args:
        db: 数据库会话
        task_id: 关联的任务 ID
        search_results: 搜索 API 返回的结果列表
        crawled_content: 爬取到的正文内容列表
    """
    # 获取已有来源的 URL 集合，用于去重
    existing_urls = {
        s.url for s in db.query(Source).filter(Source.task_id == task_id).all()
    }
    # 构建 URL → 正文内容的映射
    url_to_content = {c.get("url", ""): c.get("content", "") for c in crawled_content}

    for r in search_results:
        url = r.get("url", "")
        if not url or url in existing_urls:
            continue
        source = Source(
            task_id=task_id,
            url=url,
            title=r.get("title", ""),
            snippet=r.get("snippet", "")[:1000],  # 摘要截断
            content=url_to_content.get(url, "")[:8000],  # 正文截断
            relevance_score=r.get("relevance_score"),
            search_round=r.get("search_round", 1),
        )
        db.add(source)
        existing_urls.add(url)  # 加入集合防止同一批内重复
    db.commit()


def save_agent_log(db: Session, task_id: int, log_entry: dict):
    """保存一条 Agent 执行日志

    Args:
        db: 数据库会话
        task_id: 关联的任务 ID
        log_entry: 日志条目，包含 agent、step、input、output、decision 等字段
    """
    log = AgentLog(
        task_id=task_id,
        agent_name=log_entry.get("agent", ""),
        step=log_entry.get("step", ""),
        input_data=log_entry.get("input"),
        # 如果 output 是字符串，包装为 JSON 对象以便前端统一处理
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
    """更新任务状态

    Args:
        db: 数据库会话
        task_id: 任务 ID
        status: 新状态值
        current_step: 当前步骤描述（空字符串不更新）
        progress: 进度百分比（None 不更新）
        search_rounds: 搜索轮次（None 不更新）
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
    """保存调研报告并更新任务状态为已完成

    同时将报告导出为 Markdown 文件，并更新任务的完成时间和进度。

    Args:
        db: 数据库会话
        task_id: 任务 ID
        content: 报告 Markdown 内容
    Returns:
        保存后的 Report ORM 对象
    """
    task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
    if not task:
        raise ValueError(f"Task {task_id} not found")

    # 导出为 Markdown 文件
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

    # 更新任务为已完成状态
    task.status = "completed"
    task.progress = 100
    task.completed_at = datetime.now()
    db.commit()
    db.refresh(report)
    return report


def get_report(db: Session, task_id: int) -> Report | None:
    """查询指定任务的报告"""
    return db.query(Report).filter(Report.task_id == task_id).first()


def delete_report(db: Session, task_id: int) -> bool:
    """删除报告及其关联的 Markdown 文件

    Returns:
        是否删除成功（报告不存在返回 False）
    """
    report = get_report(db, task_id)
    if not report:
        return False
    # 同时删除导出的 Markdown 文件
    if report.file_path:
        Path(report.file_path).unlink(missing_ok=True)
    db.delete(report)
    db.commit()
    return True


def export_markdown(task_id: int, topic: str, content: str) -> str:
    """导出报告为 Markdown 文件

    Returns:
        文件路径
    """
    filename = f"report_{task_id}_{_safe_filename(topic)}.md"
    path = Path(settings.report_output_dir) / filename
    path.write_text(content, encoding="utf-8")
    return str(path)


def _save_markdown_file(task_id: int, topic: str, content: str) -> str:
    """将报告内容保存为 Markdown 文件

    Returns:
        文件路径字符串
    """
    filename = f"report_{task_id}_{_safe_filename(topic)}.md"
    path = Path(settings.report_output_dir) / filename
    path.write_text(content, encoding="utf-8")
    return str(path)


def _safe_filename(name: str) -> str:
    """将字符串转换为安全的文件名，替换特殊字符为下划线，截取前 50 字符"""
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in name[:50])
