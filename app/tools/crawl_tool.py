from langchain_core.tools import tool

from app.services.search import extract as tavily_extract
from app.services.crawler import crawl_page_sync


@tool
def extract_web_content(urls: str) -> str:
    """提取给定URL列表的网页正文内容。输入为用换行符分隔的URL列表（最多10个）。
    返回每个URL的标题和正文内容。"""
    url_list = [u.strip() for u in urls.strip().split("\n") if u.strip()]
    url_list = url_list[:10]

    if not url_list:
        return "未提供有效的URL。"

    try:
        response = tavily_extract(url_list)
        results = response.get("results", [])
        failed = response.get("failed_results", [])
    except Exception:
        results = []
        failed = url_list

    output_parts = []
    for r in results:
        url = r.get("url", "")
        content = r.get("raw_content", "")[:6000]
        output_parts.append(f"URL: {url}\n内容:\n{content}")

    if not results and failed:
        for url in failed:
            if isinstance(url, str):
                page = crawl_page_sync(url)
                if page.get("content"):
                    output_parts.append(f"URL: {page['url']}\n内容:\n{page['content'][:6000]}")

    if not output_parts:
        return "未能提取任何网页内容。"

    return "\n\n---\n\n".join(output_parts)
