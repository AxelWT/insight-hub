"""基础网页爬取服务

使用 httpx 发送 HTTP 请求，BeautifulSoup 解析 HTML，
提取页面的标题和正文内容。适用于简单页面的快速爬取。
"""

import logging

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# 更真实的 User-Agent，避免被识别为爬虫
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

# 只处理 HTML 内容类型
HTML_CONTENT_TYPES = ["text/html", "application/xhtml+xml"]

# 默认最大内容长度
MAX_CONTENT_LENGTH = 8000


def _is_html_response(response: httpx.Response) -> bool:
    """检查响应是否为 HTML 内容"""
    content_type = response.headers.get("content-type", "")
    return any(ct in content_type for ct in HTML_CONTENT_TYPES)


async def crawl_page(url: str, timeout: int = 10) -> dict:
    """异步爬取单个网页

    Args:
        url: 目标页面 URL
        timeout: 请求超时时间（秒）
    Returns:
        包含 url、title、content、error 的字典
    """
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": DEFAULT_USER_AGENT})
            resp.raise_for_status()

            # 检查是否为 HTML 内容
            if not _is_html_response(resp):
                content_type = resp.headers.get("content-type", "unknown")
                logger.warning(f"[爬虫] 跳过非 HTML 内容: {url} | Content-Type: {content_type}")
                return {
                    "url": url,
                    "title": "",
                    "content": "",
                    "error": f"非 HTML 内容: {content_type}",
                }

            return _extract_content(url, resp.text)
    except Exception as e:
        logger.warning(f"[爬虫] 爬取失败: {url} | 错误: {e}")
        return {"url": url, "title": "", "content": "", "error": str(e)}


def crawl_page_sync(url: str, timeout: int = 10) -> dict:
    """同步爬取单个网页，供非异步上下文使用"""
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": DEFAULT_USER_AGENT})
            resp.raise_for_status()

            # 检查是否为 HTML 内容
            if not _is_html_response(resp):
                content_type = resp.headers.get("content-type", "unknown")
                logger.warning(f"[爬虫] 跳过非 HTML 内容: {url} | Content-Type: {content_type}")
                return {
                    "url": url,
                    "title": "",
                    "content": "",
                    "error": f"非 HTML 内容: {content_type}",
                }

            return _extract_content(url, resp.text)
    except Exception as e:
        logger.warning(f"[爬虫] 爬取失败: {url} | 错误: {e}")
        return {"url": url, "title": "", "content": "", "error": str(e)}


def _extract_content(url: str, html: str) -> dict:
    """从 HTML 中提取标题和正文

    策略：
    1. 移除 script、style、导航栏等干扰标签
    2. 优先提取 <main>、<article> 标签内容，回退到 <body>
    3. 清理空行，截取前 8000 字符避免过长
    """
    soup = BeautifulSoup(html, "html.parser")

    # 移除干扰性标签，减少噪音内容
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    # 提取页面标题
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    # 按优先级查找正文容器：<main> → <article> → <body>
    main = soup.find("main") or soup.find("article") or soup.find("body")
    if main:
        content = main.get_text(separator="\n", strip=True)
    else:
        content = soup.get_text(separator="\n", strip=True)

    # 移除空行，使内容更紧凑
    content = "\n".join(line for line in content.splitlines() if line.strip())

    logger.debug(f"[爬虫] 提取成功: {url} | 标题: {title[:50]} | 内容长度: {len(content)} 字符")

    # 截取前 8000 字符，防止内容过长导致 AI 上下文溢出
    return {"url": url, "title": title, "content": content[:MAX_CONTENT_LENGTH], "error": None}
