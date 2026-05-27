import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from app.database import init_db
from app.ui.sidebar import render_sidebar
from app.ui.research_page import render_research_page
from app.ui.report_page import render_report_page

init_db()

st.set_page_config(
    page_title="AI 调研平台",
    page_icon="🔍",
    layout="wide",
)

if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "current_task_id" not in st.session_state:
    st.session_state.current_task_id = None


def main():
    render_sidebar()

    page = st.session_state.current_page

    if page == "research":
        render_research_page()
    elif page == "report":
        render_report_page()
    else:
        render_home_page()


def render_home_page():
    st.title("🔍 AI 调研平台")
    st.markdown("输入调研主题，AI Agent 将自动搜索、分析、整理，生成结构化调研报告。")

    st.markdown("### 使用说明")
    st.markdown("""
1. 在左侧侧边栏输入调研主题
2. 选择 AI 模型和调研深度
3. 点击"开始调研"
4. 实时查看 Agent 的思考和决策过程
5. 调研完成后查看结构化报告

**调研深度说明：**
- **快速**：1 轮搜索，5-8 个来源（低成本）
- **标准**：2-3 轮搜索，10-15 个来源（推荐）
- **深度**：3-5 轮搜索，15-25 个来源（高质量）
""")

    st.divider()
    st.subheader("最近调研")
    from app.database import SessionLocal
    from app.models import ResearchTask

    db = SessionLocal()
    try:
        tasks = (
            db.query(ResearchTask)
            .order_by(ResearchTask.created_at.desc())
            .limit(5)
            .all()
        )
        if not tasks:
            st.info("暂无历史调研记录，请在左侧创建新的调研")
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
            col1, col2, col3 = st.columns([5, 2, 2])
            with col1:
                if st.button(
                    f"{icon} {task.topic}",
                    key=f"home_task_{task.id}",
                    use_container_width=True,
                ):
                    st.session_state.current_task_id = task.id
                    st.session_state.current_page = (
                        "report" if task.status == "completed" else "research"
                    )
                    st.rerun()
            with col2:
                st.caption(depth_labels.get(task.depth, task.depth))
            with col3:
                st.caption(task.created_at.strftime("%m-%d %H:%M"))
    finally:
        db.close()


if __name__ == "__main__":
    main()
