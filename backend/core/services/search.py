"""Tavily 搜索服务
封装 Tavily API 的搜索和内容提取功能
"""

import logging
from tavily import TavilyClient
from core.config import settings

logger = logging.getLogger(__name__)

_client: TavilyClient | None = None


def _get_client() -> TavilyClient | None:
    global _client
    if _client is None:
        _client = TavilyClient(api_key=settings.tavily_api_key)
    return _client


def search(query: str, max_results: int | None = None, retries: int = 2) -> list[dict]:
    for attempt in range(retries + 1):
        try:
            client = _get_client()
            response = client.search(query=query,
                                     max_results=max_results if max_results is not None else settings.results_per_round,
                                     include_raw_content=False)
            return response.get("results", [])
        except Exception as e:
            logger.warning(f"Search attempt {attempt + 1} failed for '{query}': {e}")
            if attempt == retries:
                logger.error(f"All search retries failed for '{query}'")
                raise


def extract(urls: list[str], retries: int = 2) -> dict | None:
    for attempt in range(retries + 1):
        try:
            client = _get_client()
            return client.extract(urls=urls)
        except Exception as e:
            logger.warning(f"Extract attempt {attempt + 1} failed for '{urls}': {e}")
            if attempt == retries:
                logger.error(f"All extract retries failed for '{urls}'")
                return {"results": [], "failed_results": urls}
