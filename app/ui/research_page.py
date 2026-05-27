import streamlit as st

from app.database import SessionLocal
from app.models import ResearchTask
from app.services.report import (
    save_report,
    save_sources,
    save_agent_log,
    update_task_status,
)
from app.config import settings
from app.ui.agent_visual import render_agent_timeline


def render_research_page():
    task_id = st.session_state.current_task_id

    db = SessionLocal()
    try:
        task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
        if not task:
            st.error("任务不存在")
            st.session_state.current_page = "home"
            st.rerun()
            return
    finally:
        db.close()

    st.title("🔍 调研进行中")
    st.subheader(task.topic)
    depth_labels = {"quick": "快速", "standard": "标准", "deep": "深度"}
    st.caption(
        f"模型: {task.model} | 深度: {depth_labels.get(task.depth, task.depth)} | 创建时间: {task.created_at.strftime('%H:%M:%S')}"
    )

    if task.status == "pending":
        st.info("即将开始调研...")
        _run_research_stream(
            task_id, task.topic, task.description, task.model, task.depth
        )
        st.rerun()

    elif task.status == "completed":
        st.success("调研完成！")
        if st.button("📄 查看报告", type="primary", use_container_width=True):
            st.session_state.current_page = "report"
            st.rerun()

    elif task.status == "failed":
        st.error(f"调研失败: {task.error_message or '未知错误'}")
        if st.button("← 返回首页"):
            st.session_state.current_page = "home"
            st.rerun()

    else:
        progress = task.progress or 0
        st.progress(progress / 100)

        agent_logs = _get_agent_logs(task_id)
        render_agent_timeline(agent_logs, task.current_step or task.status)

        if st.button("🔄 刷新状态"):
            st.rerun()


def _get_agent_logs(task_id: int) -> list[dict]:
    db = SessionLocal()
    try:
        from app.models import AgentLog

        logs = (
            db.query(AgentLog)
            .filter(AgentLog.task_id == task_id)
            .order_by(AgentLog.timestamp)
            .all()
        )
        return [
            {
                "agent": log.agent_name,
                "step": log.step,
                "decision": log.decision,
                "output": log.output_data,
            }
            for log in logs
        ]
    finally:
        db.close()


def _run_research_stream(
    task_id: int, topic: str, description: str, model: str, depth: str
):
    from app.graph.research_graph import research_graph

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
        db = SessionLocal()
        try:
            task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
            task.status = "failed"
            task.error_message = str(e)
            db.commit()
        finally:
            db.close()
