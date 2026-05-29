from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from src.database.core import get_db

from src.database.models import Job, JobDependency, Execution, HttpMethod, ScheduleType, JobStatus, TriggerType
import src.database.crud as crud
import src.database.schemas as schemas
#from src.database.crud import create_job, create_execution
from src.utils.cycle_detection import has_cycle
from src.worker.executor import dispatch_task


router = APIRouter(prefix="/jobs", tags=["Jobs"])


# 定義你的 JobCreate Schema (用於 FastAPI Pydantic 驗證)
class JobCreateRequest(BaseModel):
    job_name: str
    method: HttpMethod
    endpoint: str
    schedule_type: ScheduleType
    headers: Optional[dict] = None
    body: Optional[dict] = None
    cron_expression: Optional[str] = None
    depends_on: Optional[List[int]] = None # 前置任務的 job_id 列表


def fetch_dependency_graph_from_db(db: Session) -> dict[int, list[int]]:
    """從資料庫讀取目前的相依性關係，並打包成鄰接串列"""
    graph = {}
    dependencies = db.scalars(select(JobDependency)).all()
    for dep in dependencies:
        if dep.downstream_id not in graph:
            graph[dep.downstream_id] = []
        graph[dep.downstream_id].append(dep.upstream_id)
    return graph


@router.post("/", status_code=status.HTTP_201_CREATED)
def register_job(payload: JobCreateRequest, db: Session = Depends(get_db)):
    # 1. 這裡先暫定一個 owner_id (之後整合權限認證時再改成 get_current_user.user_id)
    current_owner_id = 1  # 先hardcode!!!

    # 2. 有相依性 則進行cycle detection
    if payload.depends_on:
        # 撈出目前全系統的依賴圖
        current_graph = fetch_dependency_graph_from_db(db)

        # 模擬將新 Job 的依賴加進圖中測試
        # 這裡用 0 代表尚未建立的全新 JobID 占位符
        current_graph[0] = payload.depends_on

        # 檢查新 Job 是否會導致環狀死鎖
        if has_cycle(0, current_graph):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無法註冊此 Job：偵測到環狀相依關係 (Cycle Detected)！"
            )

    # 3. 呼叫寫好的資料庫建立函式
    new_job = crud.create_job(db=db, owner_id=current_owner_id, job_in=payload)

    # 4. 有相依性且通過檢測，將關聯寫入job_dependencies表
    if payload.depends_on:
        for upstream_id in payload.depends_on:
            dep_record = JobDependency(upstream_id=upstream_id, downstream_id=new_job.job_id)
            db.add(dep_record)
            # 因為更新了 has_dependency 標記，記得同步更新 Job 表的狀態
            new_job.has_dependency = True
            db.commit()
            db.refresh(new_job)

    return {"message": "Job 註冊成功", "job_id": new_job.job_id}

@router.post(
    "/{job_id}/trigger",
    response_model=schemas.ExecutionResponse,  #response model 規範
    status_code=status.HTTP_201_CREATED,
)
def manual_trigger(job_id: int, db: Session = Depends(get_db)):
    """手動觸發功能：繞過排程直接進入執行佇列"""

    # 1. 檢查job是否存在
    job_record = crud.get_job_by_id(db=db, job_id=job_id)
    if not job_record or job_record.status == JobStatus.DELETED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Job not found"
        )
    
    # 2. 呼叫 create_execution，觸發來源設為 MANUAL
    exec_record = crud.create_execution(db=db, job_id=job_id, trigger_type=TriggerType.MANUAL)

    # 3. 將資料包裝成字典，派發給worker thread
    job_dict = {
        "job_id": job_record.job_id,
        "method": job_record.method.value,
        "endpoint": job_record.endpoint,
        "headers": job_record.headers,
        "body": job_record.body,
        "timeout": 300              # 第一期預設超時 5 分鐘
    }
    dispatch_task(exec_record.execution_id, job_dict)

    #return {"message": "手動任務派發成功", "execution_id": exec_record.execution_id}
    return exec_record