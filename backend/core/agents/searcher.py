"""搜索 Agent - 执行网络搜索

根据主管 Agent 规划的搜索关键词，调用 Tavily 搜索 API 获取相关信息，
自动去重，并管理搜索轮次。
"""

import logging

from core.graph.state import ResearchState
from core.services.search import search as tavily_search
from core.config import settings

logger = logging.getLogger(__name__)


def searcher_agent(state: ResearchState) -> dict:
    """搜索 Agent：执行一轮搜索查询

    使用当前搜索关键词查询 Tavily，去重后合并到已有搜索结果中，
    并准备下一个搜索关键词。
    """
    logger.info("[searcher] 节点开始: 执行搜索")

    # 获取当前搜索关键词，如果没有指定则使用主题
    query = state.get("current_query", state["topic"])
    round_num = state.get("search_rounds", 0) + 1  # 当前轮次（从 1 开始）
    existing_results = state.get("search_results", [])

    logger.info(f"[searcher] 搜索关键词: {query} | 第 {round_num} 轮")

    # 获取已有结果的 URL 集合，用于去重
    existing_urls = {r.get("url") for r in existing_results}

    # 调用 Tavily 搜索 API
    results = tavily_search(query=query, max_results=settings.results_per_round)

    # 过滤重复 URL，整理搜索结果
    new_results = []
    for r in results:
        url = r.get("url", "")
        if url and url not in existing_urls:
            new_results.append(
                {
                    "url": url,
                    "title": r.get("title", ""),
                    "snippet": r.get("content", "") or r.get("snippet", ""),
                    "search_round": round_num,  # 标记搜索轮次
                    "relevance_score": r.get("score"),  # Tavily 返回的相关性评分
                }
            )

    # 合并已有结果和新结果
    all_results = existing_results + new_results

    logger.info(
        f"[searcher] 搜索完成: 新增 {len(new_results)} 条结果 | 总计 {len(all_results)} 条"
    )

    # 确定下一个搜索关键词
    queries = state.get("search_queries", [])
    next_query_idx = _get_next_query_index(queries, query)
    next_query = queries[next_query_idx] if next_query_idx < len(queries) else None

    if next_query:
        logger.info(f"[searcher] 下一个搜索关键词: {next_query}")

    log_entry = {
        "agent": "searcher",
        "step": f"第 {round_num} 轮搜索",
        "input": {"query": query, "round": round_num},
        "decision": f"搜索关键词: {query}，找到 {len(new_results)} 条新结果（总计 {len(all_results)} 条）",
        "output": [r["title"] for r in new_results[:5]],  # 只记录前 5 条标题
    }

    logger.info("[searcher] 节点完成: 搜索任务结束")
    return {
        "search_results": all_results,
        "search_rounds": round_num,
        "current_step": f"第 {round_num} 轮搜索完成，共找到 {len(all_results)} 条结果",
        "progress": min(10 + round_num * 15, 50),  # 进度：10% 起，每轮 +15%，上限 50%
        "agent_logs": state.get("agent_logs", []) + [log_entry],
        "current_query": next_query or query,  # 下轮搜索词，没有则沿用当前
    }


def _get_next_query_index(queries: list[str], current_query: str) -> int:
    """获取下一个搜索关键词的索引

    在关键词列表中找到当前关键词的位置，返回下一个位置。
    如果找不到，返回列表长度（即无下一个关键词）。
    """
    for i, q in enumerate(queries):
        if q == current_query:
            return i + 1
    return len(queries)
