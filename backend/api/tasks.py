import asyncio

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.models import ResearchTask
from backend.core.runner import start_research
from backend.schemas.task import TaskCreate, TaskResponse, TaskListResponse

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=TaskListResponse)
def list_tasks(db: Session = Depends(get_db)):
    tasks = (
        db.query(ResearchTask)
        .order_by(ResearchTask.created_at.desc())
        .limit(50)
        .all()
    )
    return TaskListResponse(tasks=[TaskResponse.model_validate(t) for t in tasks])


@router.post("", response_model=TaskResponse)
async def create_task(body: TaskCreate, db: Session = Depends(get_db)):
    task = ResearchTask(
        topic=body.topic,
        description=body.description,
        model=body.model,
        depth=body.depth,
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Start research in background
    asyncio.create_task(start_research(task.id))

    return TaskResponse.model_validate(task)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    db.delete(task)
    db.commit()
    return {"ok": True}
