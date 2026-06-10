from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
import src.database.crud as crud
import src.database.schemas as schemas
# from src.api import metrics
from src.api.dependencies import get_current_user
from src.database.core import get_db
from src.database.models import JobStatus, TriggerType, User, UserRole
from src.utils.cycle_detection import has_cycle
from src.worker.executor import dispatch_task

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def can_operate_all_jobs(user: User) -> bool:
    return user.role in {UserRole.OPERATOR, UserRole.ADMIN}


def serialize_job(db: Session, job) -> dict:
    data = schemas.JobResponse.model_validate(job).model_dump()
    data["depends_on"] = crud.get_upstream_dependency_ids(db=db, job_id=job.job_id)
    data["timeout_seconds"] = crud.get_job_timeout_seconds(job)
    return data


def require_accessible_job(job_id: int, db: Session, current_user: User):
    job = crud.get_job_by_id(db=db, job_id=job_id)
    if job is None or job.status == JobStatus.DELETED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    if job.owner_id != current_user.user_id and not can_operate_all_jobs(current_user):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return job


@router.get("/", response_model=list[schemas.JobResponse])
def list_jobs(
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """List own jobs for developers and all jobs for operators/admins."""
    if can_operate_all_jobs(current_user):
        jobs = crud.get_all_jobs(db=db)
    else:
        jobs = crud.get_jobs_by_owner_id(db=db, owner_id=current_user.user_id)
    return [serialize_job(db=db, job=job) for job in jobs]


@router.get("/{job_id}", response_model=schemas.JobResponse)
def get_job(
    job_id: int,
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """Return one job if it belongs to the authenticated user."""
    job = require_accessible_job(job_id, db, current_user)
    return serialize_job(db=db, job=job)


@router.post("/", status_code=status.HTTP_201_CREATED)
def register_job(
    payload: schemas.JobCreate,
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
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

        current_graph = crud.get_active_dependency_graph(db)
        current_graph[0] = depends_on
        if has_cycle(0, current_graph):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot register job: dependency cycle detected.",
            )

    try:
        new_job = crud.create_job(
            db=db,
            owner_id=current_user.user_id,
            job_in=payload,
            initialize_next_run_time=True,
        )
        # metrics.job_creations_total.inc()
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    if depends_on:
        crud.create_job_dependencies(
            db=db,
            downstream_id=new_job.job_id,
            upstream_ids=depends_on,
        )
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
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """Create a manual execution and enqueue it for worker execution."""
    job = require_accessible_job(job_id, db, current_user)
    if job.status != JobStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job is not executable",
        )
    unsatisfied_dependencies = crud.get_unsatisfied_dependency_ids(db=db, job_id=job_id)
    if unsatisfied_dependencies:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Job dependencies are not satisfied. Waiting for upstream job(s): "
                + ", ".join(str(job_id) for job_id in unsatisfied_dependencies)
            ),
        )

    execution = crud.create_execution(
        db=db,
        job_id=job_id,
        trigger_type=TriggerType.MANUAL,
    )
    # metrics.job_triggers_total.inc()
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


@router.patch("/{job_id}/status", response_model=schemas.JobResponse)
def update_job_status(
    job_id: int,
    payload: schemas.JobStatusUpdate,
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """Allow operators/admins to pause or resume jobs."""
    if not can_operate_all_jobs(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator permission required",
        )
    require_accessible_job(job_id, db, current_user)
    updated = crud.change_job_status(
        db=db,
        job_id=job_id,
        new_status=payload.status,
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return updated
