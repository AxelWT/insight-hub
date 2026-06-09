"""调研任务调度与执行模块

负责将调研任务分发到对应的执行流程（搜索调研 / 网站调研），
驱动 LangGraph 图谱逐步执行，并实时更新任务状态和进度。
"""

import asyncio
import logging
from datetime import datetime

from core.database import SessionLocal
from core.models import ResearchTask, TaskType
from core.config import settings
from core.services.report import (
    save_report,
    save_sources,
    save_agent_log,
    update_task_status,
)

logger = logging.getLogger(__name__)

# WebSocket 广播函数引用，在应用启动时通过 set_broadcaster 注入
_broadcast = None


def set_broadcaster(broadcast_fn):
    """注入 WebSocket 广播函数，使任务执行器能推送实时消息"""
    global _broadcast
    _broadcast = broadcast_fn


async def _ws_broadcast(task_id: int, message: dict):
    """向指定任务的 WebSocket 连接广播消息"""
    if _broadcast:
        await _broadcast(task_id, message)


def _get_task_fields(task: ResearchTask) -> dict:
    """从 ORM 对象提取任务执行所需的关键字段，避免在执行过程中持有数据库会话"""
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
    """调研任务入口：读取任务信息，根据类型分发到对应执行流程"""
    # 从数据库读取任务基本信息后立即关闭会话
    db = SessionLocal()
    try:
        task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
        if not task:
            return
        fields = _get_task_fields(task)
    finally:
        db.close()

    task_type = fields["task_type"]

    # 根据任务类型选择执行流程
    if task_type == TaskType.WEBSITE:
        _run_website_research(task_id, fields)
    else:
        _run_search_research(task_id, fields)


def _run_search_research(task_id: int, fields: dict):
    """执行主题搜索调研流程

    流程：supervisor(规划) → searcher(搜索) → crawler(爬取) → evaluator(评估)
    → 可能回到 searcher 继续搜索，或进入 writer(撰写报告)
    """
    from core.graph.research_graph import research_graph

    # 更新任务状态为"规划中"
    db = SessionLocal()
    try:
        update_task_status(db, task_id, "planning", "正在规划搜索策略...", 5)
    finally:
        db.close()

    try:
        # 构建图谱初始状态
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

        # Agent 节点名称 → (任务状态, 步骤描述) 的映射
        status_map = {
            "supervisor": ("planning", "正在规划搜索策略..."),
            "searcher": ("searching", "正在搜索相关信息..."),
            "crawler": ("searching", "正在爬取网页内容..."),
            "evaluator": ("evaluating", "正在评估信息充分性..."),
            "writer": ("writing", "正在撰写调研报告..."),
        }

        # 流式执行图谱，每完成一个节点处理一次
        final_state = {}
        for event in research_graph.stream(initial_state):
            for node_name, node_output in event.items():
                final_state = node_output
                db = SessionLocal()
                try:
                    # 根据当前执行的 Agent 更新任务状态
                    if node_name in status_map:
                        status, step_desc = status_map[node_name]
                        progress = node_output.get("progress", 0)
                        search_rounds = node_output.get("search_rounds")
                        update_task_status(
                            db, task_id, status, step_desc, progress, search_rounds
                        )

                    # 保存最新的 Agent 执行日志
                    logs = node_output.get("agent_logs", [])
                    if logs:
                        latest_log = logs[-1]
                        save_agent_log(db, task_id, latest_log)

                    # 搜索和爬取阶段保存来源信息
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

        # 图谱执行完毕，保存最终报告
        db = SessionLocal()
        try:
            report_content = final_state.get("report", "未能生成报告")
            save_report(db, task_id, report_content)
        finally:
            db.close()

    except Exception as e:
        # 记录异常并标记任务为失败
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
    """执行网站内容调研流程

    流程：website_crawler(爬取网站) → website_writer(分析并撰写报告)
    """
    from core.graph.website_research_graph import website_research_graph

    # 更新任务状态为"爬取中"
    db = SessionLocal()
    try:
        update_task_status(db, task_id, "crawling", "正在爬取网站内容...", 5)
    finally:
        db.close()

    try:
        # 构建网站调研图谱初始状态
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

        # 网站调研的 Agent 节点 → (状态, 描述) 映射
        website_status_map = {
            "website_crawler": ("crawling", "正在爬取网站内容..."),
            "website_writer": ("writing", "正在分析内容并撰写报告..."),
        }

        # 流式执行网站调研图谱
        final_state = {}
        for event in website_research_graph.stream(initial_state):
            for node_name, node_output in event.items():
                final_state = node_output
                db = SessionLocal()
                try:
                    # 更新任务状态
                    if node_name in website_status_map:
                        status, step_desc = website_status_map[node_name]
                        progress = node_output.get("progress", 0)
                        update_task_status(db, task_id, status, step_desc, progress)

                    # 保存 Agent 日志
                    logs = node_output.get("agent_logs", [])
                    if logs:
                        latest_log = logs[-1]
                        save_agent_log(db, task_id, latest_log)

                    # 网站爬取阶段保存来源和爬取内容
                    if node_name == "website_crawler":
                        crawled = node_output.get("crawled_content", [])
                        # 将爬取内容转换为搜索结果格式，便于统一存储
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

        # 保存最终报告
        db = SessionLocal()
        try:
            report_content = final_state.get("report", "未能生成报告")
            save_report(db, task_id, report_content)
        finally:
            db.close()

    except Exception as e:
        # 记录异常并标记任务失败
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
    """异步启动调研任务，将同步的 run_research 放入线程池执行，避免阻塞事件循环"""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_research, task_id)
