"""网站爬虫 Agent - 深度爬取指定网站

使用 Crawl4AI 浏览器引擎爬取用户指定的网站 URL，
支持递归爬取子页面，适合对特定网站进行深入内容分析。
"""

import logging

from core.graph.state import WebsiteResearchState
from core.services.crawl4ai_service import crawl_urls_sync

logger = logging.getLogger(__name__)


def website_crawler_agent(state: WebsiteResearchState) -> dict:
    """网站爬虫 Agent：爬取用户指定的网站内容

    根据用户配置的爬取深度和最大页面数，
    使用浏览器引擎递归爬取目标网站及其子页面。
    """
    urls = state.get("urls", [])
    crawl_depth = state.get("crawl_depth", 1)
    max_pages = state.get("max_pages", 20)

    logger.info(
        f"[website_crawler] 收到爬取任务: {len(urls)} 个 URL | 爬取深度: {crawl_depth} | 最大页面数: {max_pages}"
    )

    # 如果没有提供 URL，跳过爬取
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
    # 调用 Crawl4AI 同步爬取服务
    results = crawl_urls_sync(urls, max_depth=crawl_depth, max_pages=max_pages)

    # 分离成功和失败的结果
    succeeded = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    logger.info(
        f"[website_crawler] 爬取完成: 成功 {len(succeeded)} 个, 失败 {len(failed)} 个"
    )

    if succeeded:
        logger.info(f"[website_crawler] 成功 URL: {[r['url'] for r in succeeded]}")
    if failed:
        logger.warning(
            f"[website_crawler] 失败 URL: {[(r['url'], r['error']) for r in failed]}"
        )

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

    # 构建步骤描述
    step = f"已爬取 {len(succeeded)}/{len(urls)} 个网站，共 {len(results)} 个页面"
    if failed:
        step += f"，{len(failed)} 个页面爬取失败"

    return {
        "crawled_content": succeeded,  # 仅返回成功的结果
        "failed_urls": failed,
        "current_step": step,
        "progress": 60,  # 爬取完成后进度到 60%
        "agent_logs": state.get("agent_logs", []) + [log_entry],
    }
