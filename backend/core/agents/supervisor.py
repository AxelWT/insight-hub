from backend.core.graph.state import ResearchState
from backend.core.services.ai import completion_with_system


def supervisor_agent(state: ResearchState) -> dict:
    topic = state["topic"]
    description = state.get("description", "")
    depth = state.get("depth", "standard")

    depth_guide = {
        "quick": "生成 2-3 个搜索关键词，聚焦最核心的方面",
        "standard": "生成 4-6 个搜索关键词，覆盖主要方面",
        "deep": "生成 6-8 个搜索关键词，全面覆盖各个维度",
    }

    system_prompt = f"""你是一个资深调研主管。用户想调研一个主题，你需要制定系统性的搜索策略。

请完成以下任务：
1. 分析调研主题，拆解为多个关键子主题/方面
2. 为每个子主题生成具体的搜索关键词
3. 按优先级排序（最重要的搜索先做）

要求：
- {depth_guide.get(depth, depth_guide["standard"])}
- 搜索关键词要具体、有针对性，避免过于宽泛
- 中英文关键词混合使用以获取更全面的信息
- 包含数据型搜索关键词（如"销量""数据""报告"）和观点型搜索关键词

请用以下格式输出（每行一个搜索关键词，按优先级排序）：
搜索关键词1
搜索关键词2
...

不要输出其他内容，只输出搜索关键词列表。"""

    user_prompt = f"调研主题: {topic}"
    if description:
        user_prompt += f"\n补充说明: {description}"

    response = completion_with_system(
        model=state.get("model", "openai/gpt-4o"),
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=0.3,
    )

    queries = [
        q.strip().lstrip("0123456789.-) ")
        for q in response.strip().split("\n")
        if q.strip() and not q.strip().startswith("#")
    ]

    log_entry = {
        "agent": "supervisor",
        "step": "规划搜索策略",
        "input": {"topic": topic, "description": description, "depth": depth},
        "decision": f"拆解主题为 {len(queries)} 个搜索方向",
        "output": queries,
    }

    return {
        "search_queries": queries,
        "current_query": queries[0] if queries else topic,
        "current_step": "规划完成，开始搜索",
        "progress": 10,
        "agent_logs": state.get("agent_logs", []) + [log_entry],
    }
