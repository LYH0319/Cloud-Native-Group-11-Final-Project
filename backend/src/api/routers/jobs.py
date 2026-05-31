from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from src.database.core import get_db
from src.database.models import (
    Job,
    JobDependency,
    Execution,
    HttpMethod,
    ScheduleType,
    JobStatus,
    TriggerType,
)
import src.database.crud as crud
import src.database.schemas as schemas

# from src.database.crud import create_job, create_execution
from src.utils.cycle_detection import has_cycle
from src.worker.executor import dispatch_task

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def register_job(payload: schemas.JobCreate, db: Session = Depends(get_db)):
    # 1. 這裡先暫定一個 owner_id (之後整合權限認證時再改成 get_current_user.user_id)
    current_owner_id = 1  # 先hardcode!!!
    depends_on = payload.depends_on or []

    # 2. 有相依性 則進行cycle detection
    if depends_on:
        # 撈出目前全系統的依賴圖
        current_graph = crud.get_active_dependency_graph(db)

        # 模擬將新 Job 的依賴加進圖中測試
        # 這裡用 0 代表尚未建立的全新 JobID 占位符
        current_graph[0] = depends_on

        # 檢查新 Job 是否會導致環狀死鎖
        if has_cycle(0, current_graph):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無法註冊此 Job：偵測到環狀相依關係 (Cycle Detected)！",
            )

    # 3. 呼叫寫好的資料庫建立函式
    new_job = crud.create_job(db=db, owner_id=current_owner_id, job_in=payload)

    # 4. 有相依性且通過檢測，將關聯寫入job_dependencies表
    if depends_on:
        crud.create_job_dependencies(
            db=db, downstream_id=new_job.job_id, upstream_ids=depends_on
        )

    return {"message": "Job 註冊成功", "job_id": new_job.job_id}


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
    metadata database and returns a dispatch payload preview. Queue dispatch
    and real worker execution are future work.
    """
    job = crud.get_job_by_id(db=db, job_id=job_id)
    if job is None or job.status in [JobStatus.DELETED, JobStatus.DISABLED]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
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

    dispatch_task(execution_id=execution.execution_id, job_dict=task_payload)

    return {
        "execution": execution,
        "dispatch": {
            "queued": True,
            "queue_name": "job_priority_queue",
            "reason": "Successfully dispatched to Redis distributed queue.",
            "task_payload": {
                "execution_id": execution.execution_id,
                "job_id": job.job_id,
                "task_type": "http",
                "payload": task_payload,
                "timeout_threshold": 60
            }
        },
    }
