"""网站内容调研图谱

使用 LangGraph 编排网站调研流程，线性执行两个步骤：
website_crawler(爬取网站) → website_writer(分析并撰写报告)

相比主题搜索调研，网站调研无需搜索和评估循环，
流程更加简单直接。
"""

from langgraph.graph import StateGraph, START, END

from core.graph.state import WebsiteResearchState
from core.agents.website_crawler import website_crawler_agent
from core.agents.website_writer import website_writer_agent


def build_website_research_graph() -> StateGraph:
    """构建网站调研的 LangGraph 图

    节点流程：
    START → website_crawler → website_writer → END
    """
    builder = StateGraph(WebsiteResearchState)

    # 注册 Agent 节点
    builder.add_node("website_crawler", website_crawler_agent)
    builder.add_node("website_writer", website_writer_agent)

    # 定义线性执行边
    builder.add_edge(START, "website_crawler")  # 开始 → 爬取网站
    builder.add_edge("website_crawler", "website_writer")  # 爬取 → 撰写报告
    builder.add_edge("website_writer", END)  # 撰写 → 结束

    return builder.compile()


# 全局单例图谱实例，供 runner 模块调用
website_research_graph = build_website_research_graph()
