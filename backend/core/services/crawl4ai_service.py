"""Crawl4AI 浏览器级爬取服务

基于 Playwright 浏览器引擎爬取网页，能处理 JavaScript 渲染的页面。
支持递归爬取同域名子页面、域名限制、URL 标准化等特性。
"""

import asyncio
import time
import logging
from urllib.parse import urlparse, urljoin
from typing import Set

logger = logging.getLogger(__name__)

# 最大重试次数
MAX_RETRIES = 3
# 单页内容最大保留长度（字符）
CONTENT_MAX_LENGTH = 8000

# 需要过滤的常见无意义路径模式
SKIP_PATH_PATTERNS = [
    "/internal",
    "/external",
    "/login",
    "/register",
    "/signup",
    "/signin",
    "/logout",
    "/admin",
    "/dashboard",
    "/api/",
    "/cdn-cgi/",
    "/wp-admin",
    "/wp-content",
    "/feed",
    "/rss",
    "/sitemap",
    "/robots.txt",
    "/favicon.ico",
]


def _should_skip_url(url: str) -> bool:
    """判断 URL 是否应该跳过，过滤常见的无意义路径"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    path = parsed.path.lower()
    return any(pattern in path for pattern in SKIP_PATH_PATTERNS)


def _get_base_domain(url: str) -> str:
    """提取基础域名，用于限制爬取范围

    移除 www. 前缀，统一域名格式，防止跨子域名爬取。
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def _is_same_domain(url: str, base_domain: str) -> bool:
    """检查 URL 是否属于同一基础域名"""
    return _get_base_domain(url) == base_domain


def _normalize_url(url: str) -> str:
    """标准化 URL，移除 fragment（#后面的部分）以避免重复爬取"""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}{'?' + parsed.query if parsed.query else ''}"


async def crawl_url(url: str, max_retries: int = MAX_RETRIES) -> dict:
    """使用 Crawl4AI 爬取单个 URL

    配置无头浏览器模式，排除导航栏/页脚等干扰标签，
    自动提取同域名的内部链接用于递归爬取。

    Args:
        url: 目标 URL
        max_retries: 最大重试次数，失败后指数退避
    Returns:
        包含 url、title、content、success、error、internal_links 的字典
    """
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

    base_domain = _get_base_domain(url)
    logger.info(f"[爬虫] 开始爬取: {url} | 限制域名: {base_domain}")

    # 浏览器配置：无头模式、纯文本模式（不加载图片等资源）
    browser_config = BrowserConfig(headless=True, text_mode=True)
    # 爬取配置：过滤干扰标签、限制同域名、设置超时
    run_config = CrawlerRunConfig(
        word_count_threshold=10,  # 过滤短文本块
        excluded_tags=["nav", "footer", "header", "aside"],  # 排除导航等干扰标签
        page_timeout=30000,  # 页面加载超时 30 秒
        exclude_external_links=True,  # 排除外部链接
        exclude_social_media_links=True,  # 排除社交媒体链接
        exclude_external_images=True,  # 排除外部图片
    )

    for attempt in range(max_retries):
        try:
            if attempt > 0:
                logger.info(f"[爬虫] 第 {attempt + 1} 次尝试: {url}")

            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url=url, config=run_config)
                if result.success:
                    # 提取页面标题
                    title = ""
                    if result.metadata:
                        title = result.metadata.get("title", "") or ""
                    # 截取内容，避免过长
                    content = (result.markdown or "")[:CONTENT_MAX_LENGTH]

                    # 检测是否被重定向到外部域名（防止跟踪重定向）
                    if result.url and not _is_same_domain(result.url, base_domain):
                        logger.warning(f"[爬虫] 跳过外部重定向: {url} -> {result.url}")
                        return {
                            "url": url,
                            "title": "",
                            "content": "",
                            "success": False,
                            "error": f"重定向到外部网站: {result.url}",
                        }

                    # 提取同域名的内部链接，用于递归爬取
                    internal_links = []
                    if hasattr(result, "links") and result.links:
                        for link in result.links:
                            # 处理不同的链接数据格式
                            if isinstance(link, dict):
                                href = link.get("href", "")
                            elif isinstance(link, str):
                                href = link
                            else:
                                continue

                            if href:
                                # 将相对链接转换为绝对链接
                                full_url = urljoin(url, href)
                                normalized = _normalize_url(full_url)
                                # 只保留同域名的链接，且过滤掉无意义路径
                                if _is_same_domain(full_url, base_domain) and not _should_skip_url(full_url):
                                    internal_links.append(normalized)

                    logger.info(
                        f"[爬虫] 爬取成功: {url} | 标题: {title[:50]} | 内容长度: {len(content)} 字符 | 发现 {len(internal_links)} 个内部链接"
                    )
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
            # 指数退避重试：2^attempt 秒
            wait = 2**attempt
            logger.warning(
                f"[爬虫] 爬取失败: {url} | 第 {attempt + 1} 次 | 错误: {e} | {wait}s 后重试"
            )
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

    # 理论上不会到达此处，作为兜底返回
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
    """递归爬取 URLs 及其子页面

    使用广度优先策略逐层爬取，直到达到最大深度或页面数上限。

    Args:
        urls: 起始 URL 列表
        max_depth: 最大爬取深度（0 表示只爬起始 URL）
        max_pages: 最大爬取页面总数
        max_retries: 每个页面的最大重试次数
    Returns:
        所有爬取结果的列表
    """
    logger.info(
        f"[爬虫] 开始递归爬取: {len(urls)} 个 URL | 最大深度: {max_depth} | 最大页面数: {max_pages}"
    )

    all_results = []
    visited: Set[str] = set()
    # 待爬取队列，每个元素为 (url, 当前深度)
    urls_to_crawl = [(url, 0) for url in urls]

    while urls_to_crawl and len(all_results) < max_pages:
        url, depth = urls_to_crawl.pop(0)
        normalized_url = _normalize_url(url)

        # 跳过已访问的 URL
        if normalized_url in visited:
            continue
        visited.add(normalized_url)

        logger.info(
            f"[爬虫] 爬取深度 {depth}/{max_depth}: {url} | 已爬取: {len(all_results)}/{max_pages}"
        )

        result = await crawl_url(url, max_retries)
        all_results.append(result)

        # 如果爬取成功且未达到最大深度，将发现的内部链接加入队列
        if result["success"] and depth < max_depth:
            internal_links = result.get("internal_links", [])
            for link in internal_links:
                if (
                    link not in visited
                    and not _should_skip_url(link)
                    and len(all_results) + len(urls_to_crawl) < max_pages
                ):
                    urls_to_crawl.append((link, depth + 1))
                    logger.debug(f"[爬虫] 添加子链接: {link} (深度 {depth + 1})")

    succeeded = sum(1 for r in all_results if r["success"])
    failed = len(all_results) - succeeded
    logger.info(
        f"[爬虫] 递归爬取完成: 成功 {succeeded} 个, 失败 {failed} 个, 总计 {len(all_results)} 个"
    )
    return all_results


async def crawl_urls(urls: list[str], max_retries: int = MAX_RETRIES) -> list[dict]:
    """批量爬取指定 URLs（不递归，仅爬取输入的 URL 列表）

    Args:
        urls: 待爬取的 URL 列表
        max_retries: 每个页面的最大重试次数
    Returns:
        所有爬取结果的列表
    """
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
    """同步版本的爬取函数

    在异步上下文（如 FastAPI）中，通过线程池执行异步爬取；
    在非异步上下文中，直接运行事件循环。

    Args:
        urls: URL 列表
        max_depth: 最大爬取深度（0 表示不递归）
        max_pages: 最大页面数
        max_retries: 重试次数
    Returns:
        爬取结果列表
    """
    import concurrent.futures

    def _run_in_thread():
        if max_depth > 0:
            return asyncio.run(
                crawl_urls_recursive(urls, max_depth, max_pages, max_retries)
            )
        else:
            return asyncio.run(crawl_urls(urls, max_retries))

    try:
        # 检测是否已在事件循环中（FastAPI 请求处理时通常如此）
        loop = asyncio.get_running_loop()
        # 在事件循环中无法直接 asyncio.run()，改用线程池
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_in_thread)
            return future.result()
    except RuntimeError:
        # 没有运行中的事件循环，可以直接执行
        return _run_in_thread()
