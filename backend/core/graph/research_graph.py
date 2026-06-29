"""主题搜索调研图谱

使用 LangGraph 编排主题搜索调研流程：
supervisor(规划) → searcher(搜索) → crawler(爬取) → evaluator(评估)
→ 可能回到 searcher 继续搜索，或进入 writer(撰写报告)

评估节点后通过条件路由决定流程走向。
"""

from typing import Literal

from langgraph.graph import StateGraph, START, END

from core.graph.state import ResearchState
from core.agents.supervisor import supervisor_agent
from core.agents.searcher import searcher_agent
from core.agents.crawler import crawler_agent
from core.agents.evaluator import evaluator_agent
from core.agents.writer import writer_agent


def route_after_evaluation(state: ResearchState) -> Literal["searcher", "writer"]:
    """评估后的条件路由：决定继续搜索还是开始撰写

    路由逻辑：
    1. 信息充分 → 写作
    2. 已达最大轮次 → 写作（不再搜索）
    3. 有建议关键词 → 搜索（使用建议关键词）
    4. 无建议关键词 → 写作
    """
    # 信息充分，直接撰写报告
    if state.get("is_sufficient", False):
        return "writer"

    # 未达最大轮次但有搜索建议，继续搜索
    search_rounds = state.get("search_rounds", 0)
    max_rounds = state.get("max_rounds", 3)
    if search_rounds >= max_rounds:
        return "writer"

    # 使用评估建议的关键词继续搜索
    suggested = state.get("suggested_queries", [])
    if suggested:
        state["search_queries"] = state.get("search_queries", []) + suggested
        return "searcher"

    # 无建议关键词，直接撰写
    return "writer"


def build_research_graph() -> StateGraph:
    """构建主题搜索调研的 LangGraph 图

    节点流程：
    START → supervisor → searcher → crawler → evaluator
                                              ├─→ searcher（信息不足，继续搜索）
                                              └─→ writer → END
    """
    builder = StateGraph(ResearchState)

    # 注册 Agent 节点
    builder.add_node("supervisor", supervisor_agent)
    builder.add_node("searcher", searcher_agent)
    builder.add_node("crawler", crawler_agent)
    builder.add_node("evaluator", evaluator_agent)
    builder.add_node("writer", writer_agent)

    # 定义固定边
    builder.add_edge(START, "supervisor")  # 开始 → 主管规划
    builder.add_edge("supervisor", "searcher")  # 规划 → 搜索
    builder.add_edge("searcher", "crawler")  # 搜索 → 爬取
    builder.add_edge("crawler", "evaluator")  # 爬取 → 评估

    # 评估后的条件路由：继续搜索或开始撰写
    builder.add_conditional_edges(
        "evaluator",
        route_after_evaluation,
        {"searcher": "searcher", "writer": "writer"},
    )

    # 撰写完成 → 结束
    builder.add_edge("writer", END)

    return builder.compile()


# 全局单例图谱实例，供 runner 模块调用
research_graph = build_research_graph()
