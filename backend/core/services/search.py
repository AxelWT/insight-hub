"""Tavily 搜索服务

封装 Tavily API 的搜索和内容提取功能，
支持自动重试以应对网络波动和 API 限流。
"""

import logging

from tavily import TavilyClient

from core.config import settings

logger = logging.getLogger(__name__)


def get_client() -> TavilyClient:
    """创建 Tavily API 客户端实例"""
    return TavilyClient(api_key=settings.tavily_api_key)


def search(query: str, max_results: int | None = None, retries: int = 2) -> list[dict]:
    """执行搜索查询

    Args:
        query: 搜索关键词
        max_results: 最大返回结果数，默认使用配置值
        retries: 失败重试次数
    Returns:
        搜索结果列表，每条包含 url、title、content 等字段
    """
    for attempt in range(retries + 1):
        try:
            client = get_client()
            response = client.search(
                query=query,
                max_results=max_results or settings.results_per_round,
                include_raw_content=False,  # 不返回原文，仅摘要
            )
            return response.get("results", [])
        except Exception as e:
            logger.warning(f"Search attempt {attempt + 1} failed for '{query}': {e}")
            if attempt == retries:
                logger.error(f"All search retries failed for '{query}'")
                return []
    return []


def extract(urls: list[str], retries: int = 2) -> dict:
    """提取指定 URL 的正文内容

    使用 Tavily 的 Extract API 批量获取网页正文，
    适合替代爬虫获取结构化内容。

    Args:
        urls: 待提取的 URL 列表
        retries: 失败重试次数
    Returns:
        包含 results（成功）和 failed_results（失败 URL）的字典
    """
    for attempt in range(retries + 1):
        try:
            client = get_client()
            return client.extract(urls=urls)
        except Exception as e:
            logger.warning(f"Extract attempt {attempt + 1} failed: {e}")
            if attempt == retries:
                logger.error("All extract retries failed")
                return {"results": [], "failed_results": urls}
    return {"results": [], "failed_results": urls}
