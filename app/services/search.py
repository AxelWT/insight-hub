import logging

from tavily import TavilyClient

from app.config import settings

logger = logging.getLogger(__name__)


def get_client() -> TavilyClient:
    return TavilyClient(api_key=settings.tavily_api_key)


def search(query: str, max_results: int | None = None, retries: int = 2) -> list[dict]:
    for attempt in range(retries + 1):
        try:
            client = get_client()
            response = client.search(
                query=query,
                max_results=max_results or settings.results_per_round,
                include_raw_content=False,
            )
            return response.get("results", [])
        except Exception as e:
            logger.warning(f"Search attempt {attempt + 1} failed for '{query}': {e}")
            if attempt == retries:
                logger.error(f"All search retries failed for '{query}'")
                return []
    return []


def extract(urls: list[str], retries: int = 2) -> dict:
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
