import asyncio
import logging
from datetime import datetime

from backend.core.database import SessionLocal
from backend.core.models import ResearchTask, TaskType
from backend.core.config import settings
from backend.core.services.report import (
    save_report,
    save_sources,
    save_agent_log,
    update_task_status,
)

logger = logging.getLogger(__name__)

_broadcast = None


def set_broadcaster(broadcast_fn):
    global _broadcast
    _broadcast = broadcast_fn


async def _ws_broadcast(task_id: int, message: dict):
    if _broadcast:
        await _broadcast(task_id, message)


def _get_task_fields(task: ResearchTask) -> dict:
    return {
        "topic": task.topic,
        "description": task.description,
        "model": task.model,
        "depth": task.depth,
        "task_type": task.task_type or TaskType.SEARCH,
        "urls": task.urls or [],
        "questions": task.questions or "",
        "crawl_depth": task.crawl_depth or 1,
        "max_pages": task.max_pages or 20,
    }


def run_research(task_id: int):
    db = SessionLocal()
    try:
        task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
        if not task:
            return
        fields = _get_task_fields(task)
    finally:
        db.close()

    task_type = fields["task_type"]

    if task_type == TaskType.WEBSITE:
        _run_website_research(task_id, fields)
    else:
        _run_search_research(task_id, fields)


def _run_search_research(task_id: int, fields: dict):
    from backend.core.graph.research_graph import research_graph

    db = SessionLocal()
    try:
        update_task_status(db, task_id, "planning", "正在规划搜索策略...", 5)
    finally:
        db.close()

    try:
        initial_state = {
            "topic": fields["topic"],
            "description": fields["description"],
            "model": fields["model"],
            "evaluator_model": settings.evaluator_model,
            "depth": fields["depth"],
            "max_rounds": settings.get_max_rounds(fields["depth"]),
            "search_rounds": 0,
            "search_results": [],
            "crawled_content": [],
            "agent_logs": [],
            "progress": 0,
            "sources_saved": False,
        }

        status_map = {
            "supervisor": ("planning", "正在规划搜索策略..."),
            "searcher": ("searching", "正在搜索相关信息..."),
            "crawler": ("searching", "正在爬取网页内容..."),
            "evaluator": ("evaluating", "正在评估信息充分性..."),
            "writer": ("writing", "正在撰写调研报告..."),
        }

        final_state = {}
        for event in research_graph.stream(initial_state):
            for node_name, node_output in event.items():
                final_state = node_output
                db = SessionLocal()
                try:
                    if node_name in status_map:
                        status, step_desc = status_map[node_name]
                        progress = node_output.get("progress", 0)
                        search_rounds = node_output.get("search_rounds")
                        update_task_status(
                            db, task_id, status, step_desc, progress, search_rounds
                        )

                    logs = node_output.get("agent_logs", [])
                    if logs:
                        latest_log = logs[-1]
                        save_agent_log(db, task_id, latest_log)

                    if node_name in ("searcher", "crawler") and node_output.get(
                        "search_results"
                    ):
                        save_sources(
                            db,
                            task_id,
                            node_output.get("search_results", []),
                            node_output.get("crawled_content", []),
                        )
                finally:
                    db.close()

        db = SessionLocal()
        try:
            report_content = final_state.get("report", "未能生成报告")
            save_report(db, task_id, report_content)
        finally:
            db.close()

    except Exception as e:
        logger.exception(f"Research task {task_id} failed")
        db = SessionLocal()
        try:
            task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
            if task:
                task.status = "failed"
                task.error_message = str(e)
                db.commit()
        finally:
            db.close()


def _run_website_research(task_id: int, fields: dict):
    from backend.core.graph.website_research_graph import website_research_graph

    db = SessionLocal()
    try:
        update_task_status(db, task_id, "crawling", "正在爬取网站内容...", 5)
    finally:
        db.close()

    try:
        initial_state = {
            "urls": fields["urls"],
            "questions": fields["questions"],
            "model": fields["model"],
            "crawl_depth": fields["crawl_depth"],
            "max_pages": fields["max_pages"],
            "crawled_content": [],
            "failed_urls": [],
            "agent_logs": [],
            "progress": 0,
            "sources_saved": False,
        }

        website_status_map = {
            "website_crawler": ("crawling", "正在爬取网站内容..."),
            "website_writer": ("writing", "正在分析内容并撰写报告..."),
        }

        final_state = {}
        for event in website_research_graph.stream(initial_state):
            for node_name, node_output in event.items():
                final_state = node_output
                db = SessionLocal()
                try:
                    if node_name in website_status_map:
                        status, step_desc = website_status_map[node_name]
                        progress = node_output.get("progress", 0)
                        update_task_status(db, task_id, status, step_desc, progress)

                    logs = node_output.get("agent_logs", [])
                    if logs:
                        latest_log = logs[-1]
                        save_agent_log(db, task_id, latest_log)

                    if node_name == "website_crawler":
                        crawled = node_output.get("crawled_content", [])
                        search_results = [
                            {
                                "url": c.get("url", ""),
                                "title": c.get("title", ""),
                                "snippet": c.get("content", "")[:200],
                            }
                            for c in crawled
                        ]
                        save_sources(db, task_id, search_results, crawled)
                finally:
                    db.close()

        db = SessionLocal()
        try:
            report_content = final_state.get("report", "未能生成报告")
            save_report(db, task_id, report_content)
        finally:
            db.close()

    except Exception as e:
        logger.exception(f"Website research task {task_id} failed")
        db = SessionLocal()
        try:
            task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
            if task:
                task.status = "failed"
                task.error_message = str(e)
                db.commit()
        finally:
            db.close()


async def start_research(task_id: int):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_research, task_id)
