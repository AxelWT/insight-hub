from app.graph.state import ResearchState
from app.services.search import extract as tavily_extract
from app.services.crawler import crawl_page_sync
from app.config import settings


def crawler_agent(state: ResearchState) -> dict:
    results = state.get("search_results", [])
    existing_content = state.get("crawled_content", [])

    existing_urls = {c.get("url") for c in existing_content}
    to_crawl = [r for r in results if r.get("url") and r["url"] not in existing_urls]
    to_crawl = to_crawl[: settings.max_crawl_pages]

    if not to_crawl:
        return {
            "crawled_content": existing_content,
            "current_step": "没有新的网页需要爬取",
            "progress": state.get("progress", 40),
            "agent_logs": state.get("agent_logs", []),
        }

    urls = [r["url"] for r in to_crawl]

    crawled = []
    failed_urls = []
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
        failed_urls = [
            f.get("url", f) if isinstance(f, dict) else f
            for f in response.get("failed_results", [])
        ]
    except Exception:
        failed_urls = urls

    for url in failed_urls:
        if isinstance(url, str) and url:
            page = crawl_page_sync(url)
            if page.get("content"):
                crawled.append(
                    {
                        "url": url,
                        "content": page["content"][:6000],
                        "source": "fallback",
                    }
                )

    all_content = existing_content + crawled

    log_entry = {
        "agent": "crawler",
        "step": "爬取网页",
        "input": {"urls_count": len(urls)},
        "decision": f"尝试爬取 {len(urls)} 个网页，成功 {len(crawled)} 个",
        "output": [c["url"] for c in crawled],
    }

    return {
        "crawled_content": all_content,
        "current_step": f"已爬取 {len(all_content)} 个网页",
        "progress": min(state.get("progress", 40) + 15, 65),
        "agent_logs": state.get("agent_logs", []) + [log_entry],
    }
