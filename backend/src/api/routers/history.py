from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

import src.database.crud as crud
import src.database.schemas as schemas
from src.database.connection import get_db
from src.database.models import ExecutionStatus, JobStatus, TriggerType
from src.utils.logger import read_execution_log, validate_log_path, validate_log_size

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


@router.get(
    "/executions/{execution_id}/logs",
    response_model=schemas.ExecutionLogsResponse,
)
def get_execution_logs(
    execution_id: int,
    db: Session = Depends(get_db),
):
    """Return log metadata for one execution without reading file content."""
    execution = crud.get_execution_by_id(db=db, execution_id=execution_id)
    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )

    log_reference = crud.get_log_reference_by_execution_id(
        db=db,
        execution_id=execution_id,
    )
    return {
        "execution_id": execution_id,
        "logs": [log_reference] if log_reference is not None else [],
    }


@router.get("/executions/{execution_id}/logs/content")
def get_execution_log_content(
    execution_id: int,
    db: Session = Depends(get_db),
):
    """Return plain text log content for one execution."""
    execution = crud.get_execution_by_id(db=db, execution_id=execution_id)
    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )

    log_reference = crud.get_log_reference_by_execution_id(
        db=db,
        execution_id=execution_id,
    )
    if log_reference is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log reference not found",
        )

    try:
        content = read_execution_log(log_reference.log_path)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log file not found",
        ) from error

    return Response(content=content, media_type="text/plain")


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
    try:
        validate_log_size(update_in.log_size)
        if update_in.log_path is not None:
            validate_log_path(update_in.log_path)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

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
