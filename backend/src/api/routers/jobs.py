from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

import src.database.crud as crud
import src.database.schemas as schemas
from src.api.dependencies import get_current_user
from src.database.core import get_db
from src.database.models import (
    HttpMethod,
    Job,
    JobDependency,
    JobStatus,
    ScheduleType,
    TriggerType,
    User,
)
from src.utils.cycle_detection import has_cycle

router = APIRouter(prefix="/jobs", tags=["Jobs"])


class JobCreateRequest(BaseModel):
    job_name: str
    method: HttpMethod
    endpoint: str
    schedule_type: ScheduleType
    headers: Optional[dict] = None
    body: Optional[dict] = None
    cron_expression: Optional[str] = None
    depends_on: Optional[List[int]] = None


def fetch_dependency_graph_from_db(db: Session) -> dict[int, list[int]]:
    """Read active job dependency edges as an adjacency list."""
    graph: dict[int, list[int]] = {}
    stm = (
        select(JobDependency)
        .join(Job, JobDependency.downstream_id == Job.job_id)
        .where(Job.status == JobStatus.ACTIVE)
    )
    dependencies = db.scalars(stm).all()
    for dep in dependencies:
        graph.setdefault(dep.downstream_id, []).append(dep.upstream_id)
    return graph


@router.get("/", response_model=list[schemas.JobResponse])
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List jobs owned by the authenticated user."""
    return crud.get_jobs_by_owner_id(db=db, owner_id=current_user.user_id)


@router.get("/{job_id}", response_model=schemas.JobResponse)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return one job if it belongs to the authenticated user."""
    job = crud.get_job_by_id(db=db, job_id=job_id)
    if job is None or job.status == JobStatus.DELETED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    if job.owner_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return job


@router.post("/", status_code=status.HTTP_201_CREATED)
def register_job(
    payload: JobCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    depends_on = payload.depends_on or []

    if depends_on:
        for upstream_id in depends_on:
            upstream = crud.get_job_by_id(db=db, job_id=upstream_id)
            if upstream is None or upstream.owner_id != current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dependency job not found",
                )

        current_graph = fetch_dependency_graph_from_db(db)
        current_graph[0] = depends_on
        if has_cycle(0, current_graph):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot register job: dependency cycle detected.",
            )

    new_job = crud.create_job(db=db, owner_id=current_user.user_id, job_in=payload)

    if depends_on:
        for upstream_id in depends_on:
            crud.create_job_dependency(
                db=db,
                dependency_in=schemas.JobDependencyCreate(
                    upstream_id=upstream_id,
                    downstream_id=new_job.job_id,
                ),
            )
        new_job.has_dependency = True
        db.commit()
        db.refresh(new_job)

    return {"message": "Job registered successfully", "job_id": new_job.job_id}


@router.post(
    "/{job_id}/trigger",
    response_model=schemas.ManualTriggerResponse,
    status_code=status.HTTP_201_CREATED,
)
def manually_trigger_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create an execution record for a manual trigger.

    The current project version records the manual execution request in the
    metadata database and returns a dispatch payload preview.
    """
    job = crud.get_job_by_id(db=db, job_id=job_id)
    if job is None or job.status == JobStatus.DELETED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    if job.owner_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    if job.status != JobStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job is not executable",
        )

    execution = crud.create_execution(
        db=db,
        job_id=job_id,
        trigger_type=TriggerType.MANUAL,
    )
    task_payload = {
        "execution_id": execution.execution_id,
        "job_id": job.job_id,
        "task_type": "http",
        "payload": {
            "method": job.method.value,
            "endpoint": job.endpoint,
            "headers": job.headers or {},
            "body": job.body or {},
        },
        "timeout_threshold": 60,
    }

    return {
        "execution": execution,
        "dispatch": {
            "queued": False,
            "queue_name": None,
            "reason": "Queue dispatch is not implemented yet.",
            "task_payload": task_payload,
        },
    }
