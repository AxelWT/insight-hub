"""基础网页爬取服务

使用 httpx 发送 HTTP 请求，BeautifulSoup 解析 HTML，
提取页面的标题和正文内容。适用于简单页面的快速爬取。
"""

import httpx
from bs4 import BeautifulSoup


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
            resp = await client.get(
                url, headers={"User-Agent": "Mozilla/5.0 Research Bot"}
            )
            resp.raise_for_status()
            return _extract_content(url, resp.text)
    except Exception as e:
        return {"url": url, "title": "", "content": "", "error": str(e)}


def crawl_page_sync(url: str, timeout: int = 10) -> dict:
    """同步爬取单个网页，供非异步上下文使用"""
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": "Mozilla/5.0 Research Bot"})
            resp.raise_for_status()
            return _extract_content(url, resp.text)
    except Exception as e:
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
    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    # 按优先级查找正文容器：<main> → <article> → <body>
    main = soup.find("main") or soup.find("article") or soup.find("body")
    if main:
        content = main.get_text(separator="\n", strip=True)
    else:
        content = soup.get_text(separator="\n", strip=True)

    # 移除空行，使内容更紧凑
    content = "\n".join(line for line in content.splitlines() if line.strip())

    # 截取前 8000 字符，防止内容过长导致 AI 上下文溢出
    return {"url": url, "title": title, "content": content[:8000], "error": None}
