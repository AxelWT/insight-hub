import logging

from core.graph.state import ResearchState
from core.services.search import search as tavily_search
from core.config import settings

logger = logging.getLogger(__name__)


def searcher_agent(state: ResearchState) -> dict:
    logger.info("[searcher] 节点开始: 执行搜索")

    query = state.get("current_query", state["topic"])
    round_num = state.get("search_rounds", 0) + 1
    existing_results = state.get("search_results", [])

    logger.info(f"[searcher] 搜索关键词: {query} | 第 {round_num} 轮")

    existing_urls = {r.get("url") for r in existing_results}

    results = tavily_search(query=query, max_results=settings.results_per_round)

    new_results = []
    for r in results:
        url = r.get("url", "")
        if url and url not in existing_urls:
            new_results.append(
                {
                    "url": url,
                    "title": r.get("title", ""),
                    "snippet": r.get("content", "") or r.get("snippet", ""),
                    "search_round": round_num,
                    "relevance_score": r.get("score"),
                }
            )

    all_results = existing_results + new_results

    logger.info(f"[searcher] 搜索完成: 新增 {len(new_results)} 条结果 | 总计 {len(all_results)} 条")

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
        "output": [r["title"] for r in new_results[:5]],
    }

    logger.info("[searcher] 节点完成: 搜索任务结束")
    return {
        "search_results": all_results,
        "search_rounds": round_num,
        "current_step": f"第 {round_num} 轮搜索完成，共找到 {len(all_results)} 条结果",
        "progress": min(10 + round_num * 15, 50),
        "agent_logs": state.get("agent_logs", []) + [log_entry],
        "current_query": next_query or query,
    }


def _get_next_query_index(queries: list[str], current_query: str) -> int:
    for i, q in enumerate(queries):
        if q == current_query:
            return i + 1
    return len(queries)
