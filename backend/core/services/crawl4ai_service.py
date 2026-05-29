import asyncio
import time
import logging
from urllib.parse import urlparse, urljoin
from typing import Set

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
CONTENT_MAX_LENGTH = 8000


def _get_base_domain(url: str) -> str:
    """提取基础域名，用于限制爬取范围"""
    parsed = urlparse(url)
    # 移除 www. 前缀，统一域名
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def _is_same_domain(url: str, base_domain: str) -> bool:
    """检查 URL 是否属于同一域名"""
    return _get_base_domain(url) == base_domain


def _normalize_url(url: str) -> str:
    """标准化 URL，移除 fragment"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}{'?' + parsed.query if parsed.query else ''}"


async def crawl_url(url: str, max_retries: int = MAX_RETRIES) -> dict:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

    base_domain = _get_base_domain(url)
    logger.info(f"[爬虫] 开始爬取: {url} | 限制域名: {base_domain}")

    browser_config = BrowserConfig(headless=True, text_mode=True)
    run_config = CrawlerRunConfig(
        word_count_threshold=10,
        excluded_tags=["nav", "footer", "header", "aside"],
        page_timeout=30000,  # 30秒超时（单位：毫秒）
        # 只爬取同域名的链接，排除外部链接
        exclude_external_links=True,
        # 排除社交媒体链接
        exclude_social_media_links=True,
        # 排除外部图片
        exclude_external_images=True,
    )

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                logger.info(f"[爬虫] 第 {attempt + 1} 次尝试: {url}")

            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url=url, config=run_config)
                if result.success:
                    title = ""
                    if result.metadata:
                        title = result.metadata.get("title", "") or ""
                    content = (result.markdown or "")[:CONTENT_MAX_LENGTH]

                    # 检查爬取的内容是否属于目标域名
                    if result.url and not _is_same_domain(result.url, base_domain):
                        logger.warning(f"[爬虫] 跳过外部重定向: {url} -> {result.url}")
                        return {
                            "url": url,
                            "title": "",
                            "content": "",
                            "success": False,
                            "error": f"重定向到外部网站: {result.url}",
                        }

                    # 提取同域名的链接
                    internal_links = []
                    if hasattr(result, 'links') and result.links:
                        for link in result.links:
                            # 处理不同的链接格式
                            if isinstance(link, dict):
                                href = link.get("href", "")
                            elif isinstance(link, str):
                                href = link
                            else:
                                continue

                            if href:
                                full_url = urljoin(url, href)
                                normalized = _normalize_url(full_url)
                                if _is_same_domain(full_url, base_domain):
                                    internal_links.append(normalized)

                    logger.info(f"[爬虫] 爬取成功: {url} | 标题: {title[:50]} | 内容长度: {len(content)} 字符 | 发现 {len(internal_links)} 个内部链接")
                    return {
                        "url": url,
                        "title": title,
                        "content": content,
                        "success": True,
                        "error": None,
                        "internal_links": internal_links,
                    }
                else:
                    raise Exception(result.error_message or "爬取失败")
        except Exception as e:
            wait = 2**attempt
            logger.warning(f"[爬虫] 爬取失败: {url} | 第 {attempt + 1} 次 | 错误: {e} | {wait}s 后重试")
            if attempt < max_retries - 1:
                time.sleep(wait)
            else:
                logger.error(f"[爬虫] 最终失败: {url} | 已重试 {max_retries} 次")
                return {
                    "url": url,
                    "title": "",
                    "content": "",
                    "success": False,
                    "error": str(e),
                    "internal_links": [],
                }

    return {
        "url": url,
        "title": "",
        "content": "",
        "success": False,
        "error": "未知错误",
        "internal_links": [],
    }


async def crawl_urls_recursive(
    urls: list[str],
    max_depth: int = 1,
    max_pages: int = 20,
    max_retries: int = MAX_RETRIES,
) -> list[dict]:
    """递归爬取 URLs 及其子页面"""
    logger.info(f"[爬虫] 开始递归爬取: {len(urls)} 个 URL | 最大深度: {max_depth} | 最大页面数: {max_pages}")

    all_results = []
    visited: Set[str] = set()
    urls_to_crawl = [(url, 0) for url in urls]  # (url, depth)

    while urls_to_crawl and len(all_results) < max_pages:
        url, depth = urls_to_crawl.pop(0)
        normalized_url = _normalize_url(url)

        if normalized_url in visited:
            continue
        visited.add(normalized_url)

        logger.info(f"[爬虫] 爬取深度 {depth}/{max_depth}: {url} | 已爬取: {len(all_results)}/{max_pages}")

        result = await crawl_url(url, max_retries)
        all_results.append(result)

        # 如果爬取成功且未达到最大深度，添加子链接
        if result["success"] and depth < max_pages:
            internal_links = result.get("internal_links", [])
            for link in internal_links:
                if link not in visited and len(all_results) + len(urls_to_crawl) < max_pages:
                    urls_to_crawl.append((link, depth + 1))
                    logger.debug(f"[爬虫] 添加子链接: {link} (深度 {depth + 1})")

    succeeded = sum(1 for r in all_results if r["success"])
    failed = len(all_results) - succeeded
    logger.info(f"[爬虫] 递归爬取完成: 成功 {succeeded} 个, 失败 {failed} 个, 总计 {len(all_results)} 个")
    return all_results


async def crawl_urls(urls: list[str], max_retries: int = MAX_RETRIES) -> list[dict]:
    """只爬取指定的 URLs，不递归"""
    logger.info(f"[爬虫] 开始批量爬取: 共 {len(urls)} 个 URL")
    results = []
    for i, url in enumerate(urls, 1):
        logger.info(f"[爬虫] 进度: {i}/{len(urls)}")
        result = await crawl_url(url, max_retries)
        results.append(result)

    succeeded = sum(1 for r in results if r["success"])
    failed = len(results) - succeeded
    logger.info(f"[爬虫] 批量爬取完成: 成功 {succeeded} 个, 失败 {failed} 个")
    return results


def crawl_urls_sync(
    urls: list[str],
    max_depth: int = 0,
    max_pages: int = 20,
    max_retries: int = MAX_RETRIES,
) -> list[dict]:
    """同步版本的爬取函数"""
    import concurrent.futures

    def _run_in_thread():
        if max_depth > 0:
            return asyncio.run(crawl_urls_recursive(urls, max_depth, max_pages, max_retries))
        else:
            return asyncio.run(crawl_urls(urls, max_retries))

    try:
        # 检查是否在事件循环中
        loop = asyncio.get_running_loop()
        # 如果在事件循环中，使用线程池执行
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_in_thread)
            return future.result()
    except RuntimeError:
        # 没有运行中的事件循环，直接执行
        return _run_in_thread()
