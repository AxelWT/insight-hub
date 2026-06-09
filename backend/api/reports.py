"""报告查询 API

提供调研报告、信息来源和 Agent 日志的查询接口。
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import Report, Source, AgentLog, ResearchTask
from schemas.report import (
    ReportResponse,
    SourceResponse,
    AgentLogResponse,
)

router = APIRouter(prefix="/api/tasks", tags=["reports"])


@router.get("/{task_id}/report", response_model=ReportResponse)
def get_report(task_id: int, db: Session = Depends(get_db)):
    """获取指定任务的调研报告"""
    task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    report = db.query(Report).filter(Report.task_id == task_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return ReportResponse.model_validate(report)


@router.get("/{task_id}/sources", response_model=list[SourceResponse])
def get_sources(task_id: int, db: Session = Depends(get_db)):
    """获取指定任务的信息来源列表，按搜索轮次和 ID 排序"""
    task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    sources = (
        db.query(Source)
        .filter(Source.task_id == task_id)
        .order_by(Source.search_round, Source.id)
        .all()
    )
    return [SourceResponse.model_validate(s) for s in sources]


@router.get("/{task_id}/logs", response_model=list[AgentLogResponse])
def get_agent_logs(task_id: int, db: Session = Depends(get_db)):
    """获取指定任务的 Agent 执行日志，按时间排序"""
    task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    logs = (
        db.query(AgentLog)
        .filter(AgentLog.task_id == task_id)
        .order_by(AgentLog.timestamp)
        .all()
    )
    return [AgentLogResponse.model_validate(l) for l in logs]
