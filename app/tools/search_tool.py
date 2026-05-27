from langchain_core.tools import tool

from app.services.search import search as tavily_search


@tool
def web_search(query: str, max_results: int = 8) -> str:
    """搜索互联网获取与查询相关的网页信息。返回搜索结果列表，每条包含标题、URL和摘要。"""
    results = tavily_search(query=query, max_results=max_results)
    if not results:
        return "未找到相关搜索结果。请尝试调整关键词。"

    output_parts = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "无标题")
        url = r.get("url", "")
        snippet = r.get("content", "") or r.get("snippet", "")
        output_parts.append(f"[{i}] {title}\nURL: {url}\n摘要: {snippet}")

    return "\n\n".join(output_parts)
