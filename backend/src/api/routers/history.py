from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

import src.database.crud as crud
import src.database.schemas as schemas
from src.database.connection import get_db
from src.database.models import ExecutionStatus, JobStatus, TriggerType

router = APIRouter(tags=["executions"])


@router.get(
    "/jobs/{job_id}/executions",
    response_model=schemas.ExecutionHistoryResponse,
)
def list_job_executions(
    job_id: int,
    status_filter: Annotated[
        ExecutionStatus | None,
        Query(alias="status"),
    ] = None,
    trigger_type: TriggerType | None = None,
    worker_id: str | None = None,
    start_time_from: datetime | None = None,
    start_time_to: datetime | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    order_by: Literal[
        "created_at",
        "start_time",
        "end_time",
        "duration",
        "execution_id",
    ] = "created_at",
    order_direction: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db),
):
    """Return filtered execution history for one job, newest records first."""
    job = crud.get_job_by_id(db=db, job_id=job_id)
    if job is None or job.status == JobStatus.DELETED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    executions = crud.get_execution_history(
        db=db,
        job_id=job_id,
        status=status_filter,
        trigger_type=trigger_type,
        worker_id=worker_id,
        start_time_from=start_time_from,
        start_time_to=start_time_to,
        skip=skip,
        limit=limit,
        order_by=order_by,
        order_direction=order_direction,
    )
    return {
        "items": executions,
        "skip": skip,
        "limit": limit,
        "count": len(executions),
    }


@router.get(
    "/executions/{execution_id}",
    response_model=schemas.ExecutionResponse,
)
def get_execution(
    execution_id: int,
    db: Session = Depends(get_db),
):
    """Return one execution record by ID."""
    execution = crud.get_execution_by_id(db=db, execution_id=execution_id)
    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )

    return execution


@router.patch(
    "/executions/{execution_id}/result",
    response_model=schemas.ExecutionResultReportResponse,
)
def report_execution_result(
    execution_id: int,
    update_in: schemas.ExecutionWorkerUpdate,
    db: Session = Depends(get_db),
):
    """Store the structured result reported by a worker after execution."""
    result = crud.report_execution_result(
        db=db,
        execution_id=execution_id,
        report=update_in,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found or job_id does not match",
        )

    execution, log_reference = result
    return {
        "execution": execution,
        "log_reference": log_reference,
    }
