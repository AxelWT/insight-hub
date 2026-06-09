"""任务管理 API

提供调研任务的增删查接口，创建任务后自动在后台启动调研流程。
"""

import asyncio

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends

from core.database import get_db
from core.models import ResearchTask
from core.runner import start_research
from schemas.task import TaskCreate, TaskResponse, TaskListResponse

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=TaskListResponse)
def list_tasks(db: Session = Depends(get_db)):
    """获取任务列表，按创建时间倒序，最多返回 50 条"""
    tasks = (
        db.query(ResearchTask).order_by(ResearchTask.created_at.desc()).limit(50).all()
    )
    return TaskListResponse(tasks=[TaskResponse.model_validate(t) for t in tasks])


@router.post("", response_model=TaskResponse)
async def create_task(body: TaskCreate, db: Session = Depends(get_db)):
    """创建调研任务并自动启动后台调研流程"""
    task = ResearchTask(
        topic=body.topic,
        description=body.description,
        model=body.model,
        depth=body.depth,
        task_type=body.task_type,
        urls=body.urls,
        questions=body.questions,
        crawl_depth=body.crawl_depth,
        max_pages=body.max_pages,
        status="pending",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # 异步启动后台调研任务（不阻塞 API 响应）
    asyncio.create_task(start_research(task.id))

    return TaskResponse.model_validate(task)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """获取单个任务详情"""
    task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return TaskResponse.model_validate(task)


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """删除任务及其关联数据（级联删除来源、日志、报告）"""
    task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    db.delete(task)
    db.commit()
    return {"ok": True}
