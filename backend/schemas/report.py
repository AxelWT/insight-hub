from datetime import datetime
from pydantic import BaseModel


class SourceResponse(BaseModel):
    id: int
    url: str
    title: str
    snippet: str
    content: str
    relevance_score: float | None = None
    search_round: int
    crawled_at: datetime

    model_config = {"from_attributes": True}


class AgentLogResponse(BaseModel):
    id: int
    agent_name: str
    step: str
    input_data: dict | None = None
    output_data: dict | None = None
    decision: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class ReportResponse(BaseModel):
    id: int
    task_id: int
    content: str
    word_count: int
    source_count: int
    file_path: str | None = None

    model_config = {"from_attributes": True}
