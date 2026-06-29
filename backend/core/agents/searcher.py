"""
搜索 Agent - 执行网络搜索
根据 Supervisor Agent 规划的搜索关键词，调用 Tavily 搜索 API 获取相关信息，
自动去重，并管理搜索轮次。每轮搜索所有未搜索的关键词。
"""

import logging
from datetime import datetime

from core.graph.state import ResearchState
from core.services.search import search as tavily_search
from core.config import settings

logger = logging.getLogger(__name__)


def _enhance_query_with_time(query: str) -> str:
    now = datetime.now()
    return f"{query} {now.year}年{now.month}月{now.day}日"


def searcher_agent(state: ResearchState) -> dict:
    """搜索 Agent：执行一轮搜索（搜索所有未搜索的关键词）

    每轮搜索会遍历 search_queries 中所有尚未搜索过的关键词，
    逐个调用 Tavily API，去重后合并到已有搜索结果中。
    """
    logger.info("[step-2][searcher] 节点开始: 执行搜索")

    queries = state.get("search_queries", [])
    searched = state.get("searched_queries", [])
    existing_results = state.get("search_results", [])
    round_num = state.get("search_rounds", 0) + 1

    unsearched = [q for q in queries if q not in searched]

    if not unsearched:
        logger.info("[step-2][searcher] 无新的搜索关键词，跳过搜索")
        return {
            "search_rounds": round_num,
            "current_step": "搜索完成，无新的关键词",
            "progress": min(10 + round_num * 15, 50),
            "agent_logs": state.get("agent_logs", []),
        }

    logger.info(
        f"[step-2][searcher] 第 {round_num} 轮，共 {len(unsearched)} 个关键词待搜索: {unsearched}"
    )

    existing_urls = {r.get("url") for r in existing_results}
    all_new_results = []
    new_searched = list(searched)

    for query in unsearched:
        logger.info(f"[step-2][searcher] 搜索关键词: {query}")

        results = tavily_search(
            query=_enhance_query_with_time(query),
            max_results=settings.results_per_round,
        )

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
                existing_urls.add(url)

        all_new_results.extend(new_results)
        new_searched.append(query)

        logger.info(
            f"[step-2][searcher] 关键词 '{query}' 完成: 新增 {len(new_results)} 条结果"
        )

    all_results = existing_results + all_new_results

    log_entry = {
        "agent": "searcher",
        "step": f"第 {round_num} 轮搜索",
        "input": {"queries": unsearched, "round": round_num},
        "decision": f"搜索 {len(unsearched)} 个关键词，找到 {len(all_new_results)} 条新结果（总计 {len(all_results)} 条）",
        "output": [r["title"] for r in all_new_results[:5]],
    }

    logger.info(
        f"[step-2][searcher] 节点完成: 本轮共新增 {len(all_new_results)} 条结果"
    )
    return {
        "search_results": all_results,
        "searched_queries": new_searched,
        "search_rounds": round_num,
        "current_step": f"第 {round_num} 轮搜索完成（{len(unsearched)} 个关键词），共找到 {len(all_results)} 条结果",
        "progress": min(10 + round_num * 15, 50),
        "agent_logs": state.get("agent_logs", []) + [log_entry],
    }
