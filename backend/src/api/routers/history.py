from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

import src.database.crud as crud
import src.database.schemas as schemas
from src.api.dependencies import get_current_user
from src.database.connection import get_db
from src.database.models import (
    Execution,
    ExecutionStatus,
    JobStatus,
    TriggerType,
    User,
    UserRole,
)
from src.utils.logger import (
    read_execution_log,
    validate_log_path,
    validate_log_size,
)
from src.worker.executor import dispatch_task

router = APIRouter(tags=["executions"])


def can_view_all_results(user: User) -> bool:
    return user.role in {UserRole.OPERATOR, UserRole.ADMIN}


def require_owned_job(job_id: int, db: Session, current_user: User):
    job = crud.get_job_by_id(db=db, job_id=job_id)
    if (
        job is None
        or job.status == JobStatus.DELETED
        or (
            job.owner_id != current_user.user_id
            and not can_view_all_results(current_user)
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return job


def require_owned_execution(
    execution_id: int,
    db: Session,
    current_user: User,
):
    execution = crud.get_execution_by_id(db=db, execution_id=execution_id)
    if execution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Execution not found",
        )
    require_owned_job(execution.job_id, db, current_user)
    return execution


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
    db: Annotated[Session, Depends(get_db)] = Depends(),                  
    current_user: Annotated[User, Depends(get_current_user)] = Depends(),
):
    """Return filtered execution history for one job, newest records first."""
    require_owned_job(job_id, db, current_user)

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
    db: Annotated[Session, Depends(get_db)]= None,                  
    current_user: Annotated[User, Depends(get_current_user)]= None,
):
    """Return one execution record by ID."""
    return require_owned_execution(execution_id, db, current_user)


@router.get(
    "/executions",
    response_model=schemas.ExecutionHistoryResponse,
)
def list_executions(
    job_id: int | None = None,
    status_filter: Annotated[
        ExecutionStatus | None,
        Query(alias="status"),
    ] = None,
    trigger_type: TriggerType | None = None,
    worker_id: str | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Annotated[Session, Depends(get_db)] = Depends(),                  
    current_user: Annotated[User, Depends(get_current_user)] = Depends(),
):
    """Return all execution results for operators/admins."""
    if not can_view_all_results(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator permission required",
        )

    conditions = []
    if job_id is not None:
        conditions.append(Execution.job_id == job_id)
    if status_filter is not None:
        conditions.append(Execution.status == status_filter)
    if trigger_type is not None:
        conditions.append(Execution.trigger_type == trigger_type)
    if worker_id is not None:
        conditions.append(Execution.worker_id == worker_id)

    query = (
        select(Execution)
        .where(*conditions)
        .order_by(Execution.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    executions = list(db.scalars(query).all())
    return {
        "items": executions,
        "skip": skip,
        "limit": limit,
        "count": len(executions),
    }


@router.get(
    "/executions/{execution_id}/logs",
    response_model=schemas.ExecutionLogsResponse,
)
def get_execution_logs(
    execution_id: int,
    db: Annotated[Session, Depends(get_db)]= None,                  
    current_user: Annotated[User, Depends(get_current_user)]= None,
):
    """Return log metadata for one execution without reading file content."""
    require_owned_execution(execution_id, db, current_user)

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
    db: Annotated[Session, Depends(get_db)]= None,                  
    current_user: Annotated[User, Depends(get_current_user)]= None,
):
    """Return plain text log content for one execution."""
    require_owned_execution(execution_id, db, current_user)

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


@router.post(
    "/executions/{execution_id}/rerun",
    response_model=schemas.ManualTriggerResponse,
    status_code=status.HTTP_201_CREATED,
)
def rerun_execution(
    execution_id: int,
    db: Annotated[Session, Depends(get_db)]= None,                  
    current_user: Annotated[User, Depends(get_current_user)]= None,
):
    """Let operators/admins rerun the job behind an execution."""
    if not can_view_all_results(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator permission required",
        )
    execution = require_owned_execution(execution_id, db, current_user)
    job = crud.get_job_by_id(db=db, job_id=execution.job_id)
    if job is None or job.status != JobStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job is not executable",
        )
    unsatisfied_dependencies = crud.get_unsatisfied_dependency_ids(
        db=db,
        job_id=job.job_id,
    )
    if unsatisfied_dependencies:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Job dependencies are not satisfied. Waiting for upstream job(s): "
                + ", ".join(str(job_id) for job_id in unsatisfied_dependencies)
            ),
        )

    new_execution = crud.create_execution(
        db=db,
        job_id=job.job_id,
        trigger_type=TriggerType.MANUAL,
        retry_count=execution.retry_count + 1,
    )
    dispatch_info = dispatch_task(
        execution_id=new_execution.execution_id,
        job_dict=crud.job_to_task_dict(job),
    )
    return {
        "execution": new_execution,
        "dispatch": {
            "queued": True,
            "queue_name": dispatch_info["queue_name"],
            "reason": "Task queued for worker execution.",
            "task_payload": dispatch_info["task_payload"],
        },
    }


@router.patch(
    "/executions/{execution_id}/result",
    response_model=schemas.ExecutionResultReportResponse,
)
def report_execution_result(
    execution_id: int,
    update_in: schemas.ExecutionWorkerUpdate,
    db: Annotated[Session, Depends(get_db)]= None,                  
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
