from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import src.database.crud as crud
import src.database.schemas as schemas
from src.database.connection import get_db
from src.database.models import JobStatus, TriggerType

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post(
    "/{job_id}/trigger",
    response_model=schemas.ManualTriggerResponse,
    status_code=status.HTTP_201_CREATED,
)
def manually_trigger_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Create an execution record for a manual trigger.

    The current project version records the manual execution request in the
    metadata database. Queue dispatch and real worker execution are future
    work.
    """
    job = crud.get_job_by_id(db=db, job_id=job_id)
    if job is None or job.status == JobStatus.DELETED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
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
