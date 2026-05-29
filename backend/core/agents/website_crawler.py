import logging

from backend.core.graph.state import WebsiteResearchState
from backend.core.services.crawl4ai_service import crawl_urls_sync

logger = logging.getLogger(__name__)


def website_crawler_agent(state: WebsiteResearchState) -> dict:
    urls = state.get("urls", [])
    crawl_depth = state.get("crawl_depth", 1)
    max_pages = state.get("max_pages", 20)

    logger.info(f"[website_crawler] 收到爬取任务: {len(urls)} 个 URL | 爬取深度: {crawl_depth} | 最大页面数: {max_pages}")

    if not urls:
        logger.warning("[website_crawler] 未提供任何 URL，跳过爬取")
        return {
            "crawled_content": [],
            "failed_urls": [],
            "current_step": "未提供网站 URL",
            "progress": 60,
            "agent_logs": state.get("agent_logs", []),
        }

    logger.info(f"[website_crawler] 开始爬取: {urls}")
    results = crawl_urls_sync(urls, max_depth=crawl_depth, max_pages=max_pages)

    succeeded = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    logger.info(f"[website_crawler] 爬取完成: 成功 {len(succeeded)} 个, 失败 {len(failed)} 个")

    if succeeded:
        logger.info(f"[website_crawler] 成功 URL: {[r['url'] for r in succeeded]}")
    if failed:
        logger.warning(f"[website_crawler] 失败 URL: {[(r['url'], r['error']) for r in failed]}")

    log_entry = {
        "agent": "website_crawler",
        "step": "爬取网站",
        "input": {
            "url_count": len(urls),
            "crawl_depth": crawl_depth,
            "max_pages": max_pages,
        },
        "decision": f"爬取 {len(urls)} 个网站（深度 {crawl_depth}），成功 {len(succeeded)} 个，共 {len(results)} 个页面"
        + (f"，失败 {len(failed)} 个" if failed else ""),
        "output": {
            "success_urls": [r["url"] for r in succeeded],
            "failed_urls": [{"url": r["url"], "error": r["error"]} for r in failed],
            "total_pages": len(results),
        },
    }

    step = f"已爬取 {len(succeeded)}/{len(urls)} 个网站，共 {len(results)} 个页面"
    if failed:
        step += f"，{len(failed)} 个页面爬取失败"

    return {
        "crawled_content": succeeded,
        "failed_urls": failed,
        "current_step": step,
        "progress": 60,
        "agent_logs": state.get("agent_logs", []) + [log_entry],
    }
