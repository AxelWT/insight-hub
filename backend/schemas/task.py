from datetime import datetime
from pydantic import BaseModel


class TaskCreate(BaseModel):
    topic: str
    description: str = ""
    model: str = "deepseek"
    depth: str = "standard"
    task_type: str = "search"
    urls: list[str] = []
    questions: str = ""
    crawl_depth: int = 1
    max_pages: int = 20


class TaskResponse(BaseModel):
    id: int
    topic: str
    description: str
    model: str
    depth: str
    task_type: str
    urls: list[str]
    questions: str
    crawl_depth: int
    max_pages: int
    status: str
    progress: int
    current_step: str
    search_rounds: int
    created_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
