from app.graph.state import ResearchState
from app.services.search import search as tavily_search
from app.config import settings


def searcher_agent(state: ResearchState) -> dict:
    query = state.get("current_query", state["topic"])
    round_num = state.get("search_rounds", 0) + 1
    existing_results = state.get("search_results", [])

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

    queries = state.get("search_queries", [])
    next_query_idx = _get_next_query_index(queries, query)
    next_query = queries[next_query_idx] if next_query_idx < len(queries) else None

    log_entry = {
        "agent": "searcher",
        "step": f"第 {round_num} 轮搜索",
        "input": {"query": query, "round": round_num},
        "decision": f"搜索关键词: {query}，找到 {len(new_results)} 条新结果（总计 {len(all_results)} 条）",
        "output": [r["title"] for r in new_results[:5]],
    }

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
