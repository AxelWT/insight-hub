from langgraph.graph import StateGraph, START, END

from core.graph.state import WebsiteResearchState
from core.agents.website_crawler import website_crawler_agent
from core.agents.website_writer import website_writer_agent


def build_website_research_graph() -> StateGraph:
    builder = StateGraph(WebsiteResearchState)

    builder.add_node("website_crawler", website_crawler_agent)
    builder.add_node("website_writer", website_writer_agent)

    builder.add_edge(START, "website_crawler")
    builder.add_edge("website_crawler", "website_writer")
    builder.add_edge("website_writer", END)

    return builder.compile()


website_research_graph = build_website_research_graph()
