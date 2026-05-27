from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.models import Report, Source, AgentLog
from backend.schemas.report import (
    ReportResponse,
    SourceResponse,
    AgentLogResponse,
)

router = APIRouter(prefix="/api/tasks", tags=["reports"])


@router.get("/{task_id}/report", response_model=ReportResponse)
def get_report(task_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.task_id == task_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    return ReportResponse.model_validate(report)


@router.get("/{task_id}/sources", response_model=list[SourceResponse])
def get_sources(task_id: int, db: Session = Depends(get_db)):
    sources = (
        db.query(Source)
        .filter(Source.task_id == task_id)
        .order_by(Source.search_round, Source.id)
        .all()
    )
    return [SourceResponse.model_validate(s) for s in sources]


@router.get("/{task_id}/logs", response_model=list[AgentLogResponse])
def get_agent_logs(task_id: int, db: Session = Depends(get_db)):
    logs = (
        db.query(AgentLog)
        .filter(AgentLog.task_id == task_id)
        .order_by(AgentLog.timestamp)
        .all()
    )
    return [AgentLogResponse.model_validate(l) for l in logs]
