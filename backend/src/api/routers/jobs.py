from typing import List, Optional

from croniter import croniter
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

import src.database.crud as crud
import src.database.schemas as schemas
from src.database.core import get_db
from src.database.models import (
    HttpMethod,
    Job,
    JobDependency,
    JobStatus,
    ScheduleType,
    TriggerType,
    UserRole,
)
from src.utils.cycle_detection import has_cycle
from src.worker.executor import dispatch_task

router = APIRouter(prefix="/jobs", tags=["Jobs"])
DEFAULT_OWNER_EMPLOYEE_ID = "demo_owner"


class JobCreateRequest(BaseModel):
    job_name: str
    method: HttpMethod
    endpoint: str
    schedule_type: ScheduleType
    headers: Optional[dict] = None
    body: Optional[dict] = None
    cron_expression: Optional[str] = None
    depends_on: Optional[List[int]] = None

    @model_validator(mode="after")
    def validate_schedule(self):
        if self.schedule_type == ScheduleType.RECURRING:
            if not self.cron_expression:
                raise ValueError("cron_expression is required for recurring jobs")
            if not croniter.is_valid(self.cron_expression):
                raise ValueError("Invalid cron_expression")
        return self


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


def get_or_create_default_owner(db: Session):
    """Temporary owner strategy until authentication is implemented."""
    owner = crud.get_user_by_employee_id(db=db, employee_id=DEFAULT_OWNER_EMPLOYEE_ID)
    if owner is not None:
        return owner

    return crud.create_user(
        db=db,
        user_in=schemas.UserCreate(
            employee_id=DEFAULT_OWNER_EMPLOYEE_ID,
            username="Demo Owner",
            role=UserRole.DEVELOPER,
        ),
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
def register_job(payload: JobCreateRequest, db: Session = Depends(get_db)):
    current_owner = get_or_create_default_owner(db)
    depends_on = payload.depends_on or []

    if depends_on:
        current_graph = fetch_dependency_graph_from_db(db)
        current_graph[0] = depends_on
        if has_cycle(0, current_graph):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot register job: dependency cycle detected.",
            )

    try:
        new_job = crud.create_job(
            db=db,
            owner_id=current_owner.user_id,
            job_in=payload,
            initialize_next_run_time=True,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    for upstream_id in depends_on:
        crud.create_job_dependency(
            db=db,
            dependency_in=schemas.JobDependencyCreate(
                upstream_id=upstream_id,
                downstream_id=new_job.job_id,
            ),
        )

    if depends_on:
        new_job.has_dependency = True
        db.commit()
        db.refresh(new_job)

    return {
        "message": "Job registered successfully",
        "job_id": new_job.job_id,
        "next_run_time": new_job.next_run_time,
    }


@router.post(
    "/{job_id}/trigger",
    response_model=schemas.ManualTriggerResponse,
    status_code=status.HTTP_201_CREATED,
)
def manually_trigger_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Create a manual execution and enqueue it for the worker."""
    job = crud.get_job_by_id(db=db, job_id=job_id)
    if job is None or job.status == JobStatus.DELETED:
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
    dispatch_info = dispatch_task(
        execution_id=execution.execution_id,
        job_dict=crud.job_to_task_dict(job),
    )

    return {
        "execution": execution,
        "dispatch": {
            "queued": True,
            "queue_name": dispatch_info["queue_name"],
            "reason": "Task queued for worker execution.",
            "task_payload": dispatch_info["task_payload"],
        },
    }
