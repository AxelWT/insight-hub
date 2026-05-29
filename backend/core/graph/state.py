from typing import TypedDict


class ResearchState(TypedDict, total=False):
    topic: str
    description: str
    model: str
    depth: str
    max_rounds: int
    search_rounds: int
    search_queries: list[str]
    current_query: str
    search_results: list[dict]
    crawled_content: list[dict]
    evaluation: str
    is_sufficient: bool
    suggested_queries: list[str]
    report: str
    agent_logs: list[dict]
    current_step: str
    progress: int
    evaluator_model: str
    error_message: str
    sources_saved: bool


class WebsiteResearchState(TypedDict, total=False):
    urls: list[str]
    questions: str
    model: str
    crawl_depth: int
    max_pages: int
    crawled_content: list[dict]
    failed_urls: list[dict]
    report: str
    agent_logs: list[dict]
    current_step: str
    progress: int
    error_message: str
    sources_saved: bool
