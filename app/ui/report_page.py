import streamlit as st

from app.database import SessionLocal
from app.models import ResearchTask, Report, Source, AgentLog
from app.config import settings


def render_report_page():
    task_id = st.session_state.current_task_id

    db = SessionLocal()
    try:
        task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
        report = db.query(Report).filter(Report.task_id == task_id).first()

        if not task:
            st.error("任务不存在")
            return

        col_back, col_title = st.columns([1, 10])
        with col_back:
            if st.button("←"):
                st.session_state.current_page = "home"
                st.rerun()
        with col_title:
            st.title(task.topic)

        depth_labels = {"quick": "快速", "standard": "标准", "deep": "深度"}
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("字数", report.word_count if report else 0)
        with col2:
            st.metric("来源数", report.source_count if report else 0)
        with col3:
            st.metric("搜索轮次", task.search_rounds)
        with col4:
            st.metric("深度", depth_labels.get(task.depth, task.depth))

        if not report:
            st.warning("报告尚未生成")
            return

        tab_report, tab_sources, tab_logs = st.tabs(
            ["📄 报告", "📚 来源", "🤖 Agent 日志"]
        )

        with tab_report:
            _render_report_content(report, task)

        with tab_sources:
            _render_sources(task_id)

        with tab_logs:
            _render_agent_logs(task_id)

    finally:
        db.close()


def _render_report_content(report: Report, task: ResearchTask):
    col1, col2 = st.columns([1, 4])

    with col1:
        st.markdown("### 目录")
        toc = _extract_toc(report.content)
        for title, level in toc:
            indent = "  " * (level - 1)
            st.markdown(f"{indent}- {title}")

    with col2:
        st.markdown(report.content)

    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "📥 下载 Markdown",
            report.content,
            file_name=f"report_{task.id}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col2:
        if st.button("📋 复制到剪贴板", use_container_width=True):
            st.code(report.content, language="markdown")
    with col3:
        if st.button("🔄 继续深入调研", use_container_width=True):
            _continue_research(task)


def _render_sources(task_id: int):
    db = SessionLocal()
    try:
        sources = (
            db.query(Source)
            .filter(Source.task_id == task_id)
            .order_by(Source.search_round, Source.id)
            .all()
        )
        if not sources:
            st.info("无来源信息")
            return

        rounds = sorted(set(s.search_round for s in sources))
        for round_num in rounds:
            st.markdown(f"#### 第 {round_num} 轮搜索")
            round_sources = [s for s in sources if s.search_round == round_num]
            for i, source in enumerate(round_sources, 1):
                with st.expander(f"[{i}] {source.title or source.url[:60]}"):
                    st.markdown(f"**URL**: {source.url}")
                    if source.snippet:
                        st.markdown(f"**摘要**: {source.snippet[:500]}")
                    if source.relevance_score:
                        st.markdown(f"**相关性**: {source.relevance_score:.2f}")
                    if source.content:
                        with st.expander("查看正文"):
                            st.markdown(source.content[:3000])
                st.caption("")
    finally:
        db.close()


def _render_agent_logs(task_id: int):
    db = SessionLocal()
    try:
        logs = (
            db.query(AgentLog)
            .filter(AgentLog.task_id == task_id)
            .order_by(AgentLog.timestamp)
            .all()
        )
        if not logs:
            st.info("无 Agent 日志")
            return

        for log in logs:
            agent_icons = {
                "supervisor": "🧠",
                "searcher": "🔍",
                "crawler": "🕷️",
                "evaluator": "📊",
                "writer": "✍️",
            }
            icon = agent_icons.get(log.agent_name, "⚙️")
            with st.expander(
                f"{icon} [{log.agent_name}] {log.step} — {log.timestamp.strftime('%H:%M:%S')}"
            ):
                if log.decision:
                    st.markdown(f"**决策**: {log.decision}")
                if log.input_data:
                    st.markdown("**输入**:")
                    st.json(log.input_data)
                if log.output_data:
                    st.markdown("**输出**:")
                    st.json(log.output_data)
    finally:
        db.close()


def _extract_toc(markdown_text: str) -> list[tuple[str, int]]:
    toc = []
    for line in markdown_text.split("\n"):
        if line.startswith("#"):
            level = len(line.split(" ")[0])
            if level <= 4:
                title = line.lstrip("#").strip()
                toc.append((title, level))
    return toc


def _continue_research(task: ResearchTask):
    db = SessionLocal()
    try:
        existing_sources = db.query(Source).filter(Source.task_id == task.id).all()
        description = f"基于之前的调研继续深入。原始主题: {task.topic}"
        if task.description:
            description += f"\n原始补充说明: {task.description}"

        new_task = ResearchTask(
            topic=task.topic,
            description=description,
            model=task.model,
            depth="deep",
            status="pending",
        )
        db.add(new_task)
        db.commit()

        for source in existing_sources:
            new_source = Source(
                task_id=new_task.id,
                url=source.url,
                title=source.title,
                snippet=source.snippet,
                content=source.content,
                relevance_score=source.relevance_score,
                search_round=0,
            )
            db.add(new_source)
        db.commit()

        st.session_state.current_task_id = new_task.id
        st.session_state.current_page = "research"
        st.rerun()
    finally:
        db.close()
