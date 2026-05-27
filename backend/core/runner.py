import asyncio
import logging
from datetime import datetime

from backend.core.database import SessionLocal
from backend.core.models import ResearchTask
from backend.core.config import settings
from backend.core.services.report import save_report, save_sources, save_agent_log, update_task_status

logger = logging.getLogger(__name__)

_broadcast = None


def set_broadcaster(broadcast_fn):
    global _broadcast
    _broadcast = broadcast_fn


async def _ws_broadcast(task_id: int, message: dict):
    if _broadcast:
        await _broadcast(task_id, message)


def run_research(task_id: int):
    """Run research in a background thread."""
    from backend.core.graph.research_graph import research_graph

    db = SessionLocal()
    try:
        task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
        if not task:
            return
        topic = task.topic
        description = task.description
        model = task.model
        depth = task.depth
    finally:
        db.close()

    db = SessionLocal()
    try:
        update_task_status(db, task_id, "planning", "正在规划搜索策略...", 5)
    finally:
        db.close()

    try:
        initial_state = {
            "topic": topic,
            "description": description,
            "model": model,
            "evaluator_model": settings.evaluator_model,
            "depth": depth,
            "max_rounds": settings.get_max_rounds(depth),
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


async def start_research(task_id: int):
    """Start research task in background."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_research, task_id)
