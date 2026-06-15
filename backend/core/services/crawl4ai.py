"""
Crawl4AI 浏览器级爬取服务
基于 Playwright 浏览器引擎爬取网页，能处理 JavaScript 渲染的页面
"""

import asyncio
import logging
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)

MAX_RETRIES = 3

CONTENT_MAX_LENGTH = 8000

SKIP_PATH_PATTERNS = []


def _should_skip_url(url: str) -> bool:
    parsed_url = urlparse(url)
    path = parsed_url.path.lower()
    return any(pattern in path for pattern in SKIP_PATH_PATTERNS)


def _get_base_domain(url: str) -> str:
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def _is_same_domain(url: str, base_domain: str) -> bool:
    return _get_base_domain(url) == base_domain


def _normalize_url(url: str) -> str:
    parsed_url = urlparse(url)
    scheme = parsed_url.scheme or "https"
    netloc = parsed_url.netloc
    if not netloc:
        return url
    path = parsed_url.path or "/"
    result = f"{scheme}://{netloc}{path}"
    if parsed_url.query:
        result += f"?{parsed_url.query}"
    return result


async def crawl_url(url: str, max_retries: int = MAX_RETRIES) -> dict:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    base_domain = _get_base_domain(url)
    logger.info(f"[crawl_url] start to crawl, base_domain: {base_domain}")

    browser_config = BrowserConfig(headless=True, text_mode=True)
    run_config = CrawlerRunConfig(
        word_count_threshold=10,
        excluded_tags=["nav", "footer", "header", "aside"],
        page_timeout=30000,
        exclude_external_links=True,
        exclude_social_media_links=True,
        exclude_external_images=True,
    )

    for attempt in range(max_retries):
        try:
            logger.info(f"[crawl_url] attempt {attempt + 1} url: {url}")

            async with AsyncWebCrawler(config=browser_config, run_config=run_config) as crawler:
                result = await crawler.crawl(url=url, config=run_config)
                if result is not None and result.success:
                    title = ""
                    if result.metadata:
                        title = result.metadata.get("title", "")
                    content = (result.markdown or "")[:CONTENT_MAX_LENGTH]
                    if result.url and not _is_same_domain(result.url, base_domain):
                        logger.warning(f"[crawl_url] skip url: {result.url}\n original url: {url}")
                        return {"url": url, "title": "", "content": "", "success": False,
                                "error": f"Redirect to outside web: {result.url}"}

                    internal_links = []
                    if hasattr(result, "links") and result.links:
                        for link in result.links:
                            if isinstance(link, dict):
                                href = link.get("href", "")
                            elif isinstance(link, str):
                                href = link
                            else:
                                continue
                            if href:
                                full_url = urljoin(url, href)
                                if _is_same_domain(full_url, base_domain) and not _should_skip_url(full_url):
                                    normalized_url = _normalize_url(full_url)
                                    internal_links.append(normalized_url)
                    logger.info(f"[crawl_url] internal links: {internal_links}")
                    return {"url": url, "title": title, "content": content, "success": True, "error": None,
                            "internal_links": internal_links}
                else:
                    logger.error(f"[crawl_url] fail to crawl url: {url}")
                    raise Exception(result.error_message or f"[crawl_url] fail to crawl url: {url}")
        except Exception as e:
            wait = 2 * (attempt + 1)
            logger.warning(
                f"[crawl_url] fail to crawl url: {url}, attempt: {attempt + 1}, error: {e}, wait: {wait}s and retry")
            if attempt < max_retries - 1:
                await asyncio.sleep(wait)
            else:
                logger.error(f"[crawl_url] fail to crawl url: {url}, finish attempt: {attempt + 1}, error: {e}")
                return {"url": url, "title": "", "content": "", "success": False, "error": str(e), "internal_links": []}


async def crawl_urls_recursive(urls: list[str], max_depth: int = 1, max_pages: int = 20,
                               max_retries: int = MAX_RETRIES) -> list[dict]:
    logger.info(
        f"[crawl_urls_recursive] start to crawl, urls: {urls}, max_depth: {max_depth}, max_pages: {max_pages}, max_retries: {max_retries}")
    all_results = []
    visited_urls = set()
    urls_to_crawl = [(url, 0) for url in urls]

    while urls_to_crawl and len(all_results) < max_pages:
        url, depth = urls_to_crawl.pop(0)
        normalized_url = _normalize_url(url)

        if normalized_url in visited_urls:
            continue
        visited_urls.add(normalized_url)
        logger.info(
            f"[crawl_urls_recursive] visited url: {normalized_url}, crawl depth: {depth}/{max_depth} | visited urls: {len(all_results)}/{max_pages}")

        result = await crawl_url(url, max_retries=max_retries)
        all_results.append(result)

        if result["success"] and depth < max_depth:
            internal_links = result.get("internal_links", [])
            for link in internal_links:
                if (link not in visited_urls) and not _should_skip_url(link) and len(all_results) + len(
                        urls_to_crawl) < max_pages:
                    urls_to_crawl.append((link, depth + 1))
                    logger.debug(f"[crawl_urls_recursive] add internal link: {link}, depth:{depth + 1}")

    succeeded = sum(1 for r in all_results if r["success"])
    failed = len(all_results) - succeeded
    logger.info(f"[crawl_urls_recursive] succeeded: {succeeded}, failed: {failed}, total: {len(all_results)}")
    return all_results


async def crawl_urls(urls: list[str], max_retries: int = MAX_RETRIES) -> list[dict]:
    logger.info(f"[crawl_urls] start to crawl, urls: {urls}")
    results = []
    for i, url in enumerate(urls, 1):
        logger.info(f"[crawl_urls] crawl step: {i}/{len(urls)}")
        result = await crawl_url(url, max_retries=max_retries)
        results.append(result)
    succeeded = sum(1 for r in results if r["success"])
    failed = len(results) - succeeded
    logger.info(f"[crawl_urls] succeeded: {succeeded}, failed: {failed}")
    return results


def crawl_urls_sync(urls: list[str], max_depth: int = 0, max_pages: int = 20, max_retries: int = MAX_RETRIES) -> list[dict]:
    import concurrent.futures

    def _run_in_thread():
        if max_depth > 0:
            return asyncio.run(crawl_urls_recursive(urls, max_depth, max_pages, max_retries))
        else:
            return asyncio.run(crawl_urls(urls, max_retries))

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_in_thread)
            return future.result()
    except RuntimeError as e:
        if "no running event loop" in str(e):
            return _run_in_thread()
        raise
