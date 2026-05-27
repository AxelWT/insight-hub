import streamlit as st

from app.database import SessionLocal
from app.models import ResearchTask
from app.config import settings


def render_sidebar():
    with st.sidebar:
        st.header("🔍 AI 调研平台")

        with st.expander("📝 新建调研", expanded=True):
            with st.form("research_form"):
                topic = st.text_input(
                    "调研主题", placeholder="例如：2024年中国新能源汽车市场分析"
                )
                description = st.text_area(
                    "补充说明（可选）",
                    placeholder="重点关注比亚迪、特斯拉的市占率变化",
                    height=80,
                )

                col1, col2 = st.columns(2)
                with col1:
                    models = settings.available_models
                    model_names = [m["name"] for m in models]
                    model_ids = [m["id"] for m in models]
                    selected_idx = st.selectbox(
                        "AI 模型",
                        range(len(model_names)),
                        format_func=lambda i: model_names[i],
                    )
                with col2:
                    depth = st.selectbox(
                        "调研深度",
                        ["quick", "standard", "deep"],
                        format_func=lambda x: {
                            "quick": "快速（1轮搜索）",
                            "standard": "标准（2-3轮搜索）",
                            "deep": "深度（3-5轮搜索）",
                        }[x],
                    )

                submitted = st.form_submit_button(
                    "开始调研", type="primary", use_container_width=True
                )

                if submitted and topic.strip():
                    db = SessionLocal()
                    try:
                        task = ResearchTask(
                            topic=topic.strip(),
                            description=description.strip(),
                            model=model_ids[selected_idx],
                            depth=depth,
                            status="pending",
                        )
                        db.add(task)
                        db.commit()
                        st.session_state.current_task_id = task.id
                        st.session_state.current_page = "research"
                        st.rerun()
                    finally:
                        db.close()

        st.divider()

        st.subheader("历史调研")
        db = SessionLocal()
        try:
            tasks = (
                db.query(ResearchTask)
                .order_by(ResearchTask.created_at.desc())
                .limit(20)
                .all()
            )
            if not tasks:
                st.info("暂无历史调研记录")
            for task in tasks:
                status_icons = {
                    "pending": "⏳",
                    "planning": "🤔",
                    "searching": "🔍",
                    "evaluating": "📊",
                    "writing": "✍️",
                    "completed": "✅",
                    "failed": "❌",
                }
                icon = status_icons.get(task.status, "❓")
                depth_labels = {"quick": "快速", "standard": "标准", "deep": "深度"}
                label = (
                    f"{icon} {task.topic[:30]}{'...' if len(task.topic) > 30 else ''}"
                )
                if st.button(
                    label, key=f"sidebar_task_{task.id}", use_container_width=True
                ):
                    st.session_state.current_task_id = task.id
                    st.session_state.current_page = (
                        "report" if task.status == "completed" else "research"
                    )
                    st.rerun()
                st.caption(
                    f"{depth_labels.get(task.depth, task.depth)} | {task.created_at.strftime('%m-%d %H:%M')}"
                )
        finally:
            db.close()
