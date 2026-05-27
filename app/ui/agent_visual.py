import streamlit as st


_STEP_ICONS = {
    "supervisor": "🧠",
    "searcher": "🔍",
    "crawler": "🕷️",
    "evaluator": "📊",
    "writer": "✍️",
}

_STATUS_ORDER = ["supervisor", "searcher", "crawler", "evaluator", "writer"]


def render_agent_timeline(agent_logs: list[dict], current_step: str = ""):
    if not agent_logs and not current_step:
        st.info("Agent 尚未开始工作...")
        return

    completed_agents = set()
    for log in agent_logs:
        completed_agents.add(log.get("agent", ""))

    _render_current_status(current_step, agent_logs)
    st.divider()

    st.subheader("📋 执行时间线")

    for i, log in enumerate(agent_logs):
        agent = log.get("agent", "unknown")
        step = log.get("step", "")
        decision = log.get("decision", "")
        output = log.get("output", "")
        icon = _STEP_ICONS.get(agent, "⚙️")

        with st.expander(f"{icon} {step}", expanded=(i == len(agent_logs) - 1)):
            if decision:
                st.markdown(f"**决策**: {decision}")
            if output:
                if isinstance(output, list):
                    for item in output:
                        st.markdown(f"- {item}")
                elif isinstance(output, dict):
                    st.json(output)
                else:
                    st.markdown(f"**输出**: {str(output)[:500]}")

    remaining = [a for a in _STATUS_ORDER if a not in completed_agents]
    if remaining and current_step not in ("报告撰写完成", ""):
        for agent in remaining:
            icon = _STEP_ICONS.get(agent, "⚙️")
            st.markdown(f"{icon} ⏳ {_step_label(agent)}")


def _render_current_status(current_step: str, agent_logs: list[dict]):
    status_map = {
        "规划": ("🤔 规划中", "Agent 正在制定搜索策略..."),
        "搜索": ("🔍 搜索中", "Agent 正在搜索相关信息..."),
        "爬取": ("🕷️ 爬取中", "Agent 正在爬取网页内容..."),
        "评估": ("📊 评估中", "Agent 正在评估信息充分性..."),
        "撰写": ("✍️ 撰写中", "Agent 正在撰写调研报告..."),
        "完成": ("✅ 已完成", "调研报告已生成！"),
    }

    matched_key = "规划"
    for key in status_map:
        if key in current_step:
            matched_key = key
            break

    title, desc = status_map.get(matched_key, ("🔄 进行中", current_step))

    st.markdown(f"## {title}")
    st.caption(desc)

    search_rounds = set()
    for log in agent_logs:
        if log.get("agent") == "searcher":
            step = log.get("step", "")
            if "第" in step and "轮" in step:
                try:
                    num = int(step.split("第")[1].split("轮")[0])
                    search_rounds.add(num)
                except (ValueError, IndexError):
                    pass

    if search_rounds:
        rounds_str = ", ".join(f"第{r}轮" for r in sorted(search_rounds))
        st.caption(f"已完成搜索轮次: {rounds_str}")


def _step_label(agent: str) -> str:
    labels = {
        "supervisor": "规划搜索策略",
        "searcher": "搜索相关信息",
        "crawler": "爬取网页内容",
        "evaluator": "评估信息充分性",
        "writer": "撰写调研报告",
    }
    return labels.get(agent, agent)
