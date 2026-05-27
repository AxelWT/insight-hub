from typing import Literal

from langgraph.graph import StateGraph, START, END

from app.graph.state import ResearchState
from app.agents.supervisor import supervisor_agent
from app.agents.searcher import searcher_agent
from app.agents.crawler import crawler_agent
from app.agents.evaluator import evaluator_agent
from app.agents.writer import writer_agent
from app.config import settings


def route_after_evaluation(state: ResearchState) -> Literal["searcher", "writer"]:
    if state.get("is_sufficient", False):
        return "writer"

    search_rounds = state.get("search_rounds", 0)
    max_rounds = state.get("max_rounds", 3)
    if search_rounds >= max_rounds:
        return "writer"

    suggested = state.get("suggested_queries", [])
    if suggested:
        state["current_query"] = suggested[0]
        state["search_queries"] = state.get("search_queries", []) + suggested
        return "searcher"
    return "writer"


def build_research_graph() -> StateGraph:
    builder = StateGraph(ResearchState)

    builder.add_node("supervisor", supervisor_agent)
    builder.add_node("searcher", searcher_agent)
    builder.add_node("crawler", crawler_agent)
    builder.add_node("evaluator", evaluator_agent)
    builder.add_node("writer", writer_agent)

    builder.add_edge(START, "supervisor")
    builder.add_edge("supervisor", "searcher")
    builder.add_edge("searcher", "crawler")
    builder.add_edge("crawler", "evaluator")
    builder.add_conditional_edges(
        "evaluator",
        route_after_evaluation,
        {"searcher": "searcher", "writer": "writer"},
    )
    builder.add_edge("writer", END)

    return builder.compile()


research_graph = build_research_graph()
