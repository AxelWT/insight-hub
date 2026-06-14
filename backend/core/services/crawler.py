"""基础网页爬取服务

使用 httpx 发送 HTTP 请求，BeautifulSoup 解析 HTML
"""

import logging

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

HTML_CONTENT_TYPE = ["text/html", "application/xhtml+xml", "application/xml"]

MAX_CONTENT_LENGTH = 8000


def _is_html_response(response: httpx.Response) -> bool:
    content_type = response.headers.get("content-type", "")
    return any(c in content_type for c in HTML_CONTENT_TYPE)


def _extract_content(url: str, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript", "svg", "canvas"]):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    main = soup.find("main") or soup.find("article") or soup.find("body")
    if main:
        content = main.get_text(separator="\n", strip=True)
    else:
        content = soup.get_text(separator="\n", strip=True)

    content = "\n".join(line for line in content.splitlines() if line.strip())

    logger.debug(
        f"[_extract_content] extract content success: {url} | title: {title} | content length: {len(content)} chars")

    return {"url": url, "title": title, "content": content[:MAX_CONTENT_LENGTH], "error": None}


def _process_response(url: str, response: httpx.Response) -> dict:
    response.raise_for_status()
    if not _is_html_response(response):
        content_type = response.headers.get("content-type", "unknown")
        logger.warning(f"[_process_response] skip non-html: {url} content type: {content_type}")
        return {
            "url": url,
            "title": "",
            "content": "",
            "error": f"non-html content type: {content_type}",
        }
    return _extract_content(url, response.text)


async def crawl_page(url: str, timeout: int = 10, retries: int = 2) -> dict:
    for attempt in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": DEFAULT_USER_AGENT})
                return _process_response(url, resp)
        except Exception as e:
            logger.warning(f"[crawl_page] attempt {attempt + 1} failed for '{url}': {e}")
            if attempt == retries:
                logger.error(f"[crawl_page] all retries failed for '{url}'")
                return {"url": url, "title": "", "content": "", "error": str(e)}
    return {"url": url, "title": "", "content": "", "error": "Fail to crawl"}


def crawl_page_sync(url: str, timeout: int = 10, retries: int = 2) -> dict:
    for attempt in range(retries + 1):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                resp = client.get(url, headers={"User-Agent": DEFAULT_USER_AGENT})
                return _process_response(url, resp)
        except Exception as e:
            logger.warning(f"[crawl_page_sync] attempt {attempt + 1} failed for '{url}': {e}")
            if attempt == retries:
                logger.error(f"[crawl_page_sync] all retries failed for '{url}'")
                return {"url": url, "title": "", "content": "", "error": str(e)}
    return {"url": url, "title": "", "content": "", "error": "Fail to crawl"}
