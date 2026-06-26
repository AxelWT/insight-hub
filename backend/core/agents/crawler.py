"""
爬虫 Agent - 爬取网页正文内容
对搜索结果中的 URL 进行内容爬取，优先使用 Tavily Extract API，
失败时回退到基础 HTTP 爬虫，确保最大化内容获取率。
"""

import logging

from core.graph.state import ResearchState
from core.services.search import extract as tavily_extract
from core.services.crawl4ai import crawl_urls_sync
from core.config import settings

logger = logging.getLogger(__name__)


def crawler_agent(state: ResearchState) -> dict:
    """爬虫 Agent：爬取搜索结果中的网页正文

    策略：
    1. 优先使用 Tavily Extract API 批量提取正文
    2. 对 Tavily 提取失败的 URL，回退到 HTTP 爬虫逐个爬取
    3. 自动去重，跳过已爬取的 URL
    """
    logger.info("[step-3][crawler] 节点开始: 爬取网页内容")

    results = state.get("search_results", [])
    existing_content = state.get("crawled_content", [])

    # 收集尚未爬取的 URL
    existing_urls = {c.get("url") for c in existing_content}
    to_crawl = [r for r in results if r.get("url") and r["url"] not in existing_urls]
    to_crawl = to_crawl[: settings.max_crawl_pages]  # 限制最大爬取数

    # 如果没有新 URL 需要爬取，直接返回
    if not to_crawl:
        logger.info("[step-3][crawler] 没有新的网页需要爬取")
        return {
            "crawled_content": existing_content,
            "current_step": "没有新的网页需要爬取",
            "progress": state.get("progress", 40),
            "agent_logs": state.get("agent_logs", []),
        }

    urls = [r["url"] for r in to_crawl]
    logger.info(f"[step-3][crawler] 待爬取 {len(urls)} 个网页")

    crawled = []
    failed_urls = []

    # 第一轮：尝试 Tavily Extract API 批量提取
    try:
        response = tavily_extract(urls)
        for r in response.get("results", []):
            content = r.get("raw_content", "")[:6000]
            if content:
                crawled.append(
                    {
                        "url": r.get("url", ""),
                        "content": content,
                        "source": "tavily",
                    }
                )
        # 收集失败的 URL
        failed_urls = [
            f.get("url", f) if isinstance(f, dict) else f
            for f in response.get("failed_results", [])
        ]
    except Exception as e:
        logger.warning(f"[step-3][crawler] tavily extract failed: {e}")
        failed_urls = urls

    # 第二轮：对失败的 URL 使用基础 HTTP 爬虫逐个回退
    for url in failed_urls:
        if isinstance(url, str) and url:
            pages = crawl_urls_sync([url])
            for page in pages:
                if page.get("content"):
                    crawled.append(
                        {
                            "url": url,
                            "content": page["content"][:6000],
                            "source": "fallback",  # 标记为回退爬取
                        }
                    )

    # 合并已有内容和新爬取的内容
    all_content = existing_content + crawled

    logger.info(f"[step-3][crawler] 爬取完成: 成功 {len(crawled)} 个 | 失败 {len(failed_urls)} 个 | 总计 {len(all_content)} 个")

    log_entry = {
        "agent": "crawler",
        "step": "爬取网页",
        "input": {"urls_count": len(urls)},
        "decision": f"尝试爬取 {len(urls)} 个网页，成功 {len(crawled)} 个",
        "output": [c["url"] for c in crawled],
    }

    logger.info("[step-3][crawler] 节点完成: 网页爬取任务结束")
    return {
        "crawled_content": all_content,
        "current_step": f"已爬取 {len(all_content)} 个网页",
        "progress": min(state.get("progress", 40) + 15, 65),  # 进度 +15%，上限 65%
        "agent_logs": state.get("agent_logs", []) + [log_entry],
    }
