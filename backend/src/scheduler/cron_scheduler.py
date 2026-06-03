import time
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import select

from config.setting import settings

# 1. 引入core.py的連線設定
from src.database.core import SessionLocal

# 2. 引入models.py的模型
from src.database.models import (
    JobDependency,
    Execution,
    ExecutionStatus,
    JobStatus,
    ScheduleType,
    TriggerType,
)

# 3. 引入crud.py的邏輯函式
from src.database.crud import (
    as_utc_naive,
    compute_next_recurring_run_time,
    create_execution,
    get_active_jobs,
    job_to_task_dict,
    utc_now,
)
from src.worker.executor import dispatch_task


def recover_stale_executions(
    db: Session,
    now_utc: datetime | None = None,
    stale_after_seconds: int | None = None,
    max_retries: int | None = None,
    dispatch_fn=dispatch_task,
) -> list[Execution]:
    """Mark stale running executions timed out and retry eligible jobs."""
    now_utc = as_utc_naive(now_utc) or utc_now()
    stale_after = stale_after_seconds or settings.HEARTBEAT_TIMEOUT
    retry_limit = settings.MAX_EXECUTION_RETRIES if max_retries is None else max_retries
    cutoff = now_utc - timedelta(seconds=stale_after)

    stale_executions = list(
        db.scalars(
            select(Execution)
            .where(Execution.status == ExecutionStatus.RUNNING)
            .where(
                (Execution.last_heartbeat.is_(None))
                | (Execution.last_heartbeat < cutoff)
            )
        ).all()
    )

    retried_executions: list[Execution] = []
    for execution in stale_executions:
        execution.status = ExecutionStatus.TIMEOUT
        execution.end_time = now_utc
        execution.last_heartbeat = now_utc
        execution.error_message = (
            f"Execution heartbeat stale for more than {stale_after} seconds"
        )
        if execution.start_time:
            execution.duration = max(
                1,
                int((now_utc - as_utc_naive(execution.start_time)).total_seconds()),
            )
        db.commit()
        db.refresh(execution)

        if execution.retry_count >= retry_limit:
            continue
        if execution.job is None or execution.job.status != JobStatus.ACTIVE:
            continue
        if not check_predecessors_done(db=db, job_id=execution.job_id):
            continue

        retry_execution = create_execution(
            db=db,
            job_id=execution.job_id,
            trigger_type=execution.trigger_type,
            retry_count=execution.retry_count + 1,
        )
        dispatch_fn(
            execution_id=retry_execution.execution_id,
            job_dict=job_to_task_dict(execution.job),
        )
        retried_executions.append(retry_execution)

    return retried_executions


def check_predecessors_done(db: Session, job_id: int) -> bool:
    """
    【相依性管理核心】
    檢查當前 Job 的所有前置任務（Upstream）是否都在 executions 表中最後一次執行成功。
    """
    # 撈出該任務的所有upstream
    upstream_dependencies = db.scalars(
        select(JobDependency).where(JobDependency.downstream_id == job_id)
    ).all()

    # 如果沒有upstream，可以直接過關
    if not upstream_dependencies:
        return True

    for dep in upstream_dependencies:
        # 撈出該upstream最新的一筆執行紀錄
        latest_execution = db.scalar(
            select(Execution)
            .where(Execution.job_id == dep.upstream_id)
            .order_by(Execution.created_at.desc())
            .limit(1)
        )

        # 如果前置任務從未跑過，或者最後一次狀態不是 SUCCESS，代表前置未完成
        if not latest_execution or latest_execution.status != ExecutionStatus.SUCCESS:
            print(
                f" 任務(ID: {job_id})無法執行: upstream任務(ID: {dep.upstream_id})尚未成功完成。"
            )
            return False

    return True


def start_cron_scheduler(db_session_factory: sessionmaker = SessionLocal):
    """
    【自動任務派發核心進程】
    背景主迴圈。每 60 秒輪詢掃描一次資料庫，處理時間到的 One-time 任務。
    """
    print("[Scheduler] 自動排程與相依性管理背景服務啟動成功...")

    while True:
        # 每輪都開啟一個獨立的資料庫Session
        db: Session = db_session_factory()
        try:
            # 統一取得當下的 UTC 時間
            now_utc = utc_now()

            recover_stale_executions(db=db, now_utc=now_utc)

            # 呼叫 get_active_jobs 撈出時間到的 ACTIVE 任務 (one-time & cron)
            due_jobs = get_active_jobs(
                db=db, schedule_type=None, target_time=now_utc, for_update=False
            )

            for job in due_jobs:
                # 相依性驗證
                # 1. 前置未完成，跳過這次，等下一分鐘輪詢再試
                if not check_predecessors_done(db=db, job_id=job.job_id):
                    continue

                print(
                    f" [Scheduler] 偵測到其任務: '{job.job_name}' (ID: {job.job_id}) 通過相依性檢查"
                )

                # 2. 建立自動排程觸發的 Execution 紀錄 (預設狀態為 PENDING)
                exec_record = create_execution(
                    db=db, job_id=job.job_id, trigger_type=TriggerType.SCHEDULER
                )

                if job.schedule_type == ScheduleType.ONE_TIME:
                    # 3-1. 【One-time 核心邏輯】：因為是單次任務，跑完這輪後，必須清除 next_run_time 防止重複觸發
                    job.next_run_time = None
                elif job.schedule_type == ScheduleType.RECURRING:
                    job.next_run_time = compute_next_recurring_run_time(
                        job.cron_expression,
                        now_utc,
                    )

                db.flush()

                # 4. 任務封裝：將 SQLAlchemy 物件轉成普通的 Python 字典
                job_dict = job_to_task_dict(job)

                # 5. 派發交棒：呼叫dispatch_task，正式put進task_queue
                dispatch_task(execution_id=exec_record.execution_id, job_dict=job_dict)

            # 批次更新完所有 Job 的時間後，統一 commit 存檔
            db.commit()

        except Exception as e:
            db.rollback()
            print(f" [Scheduler] 背景輪巡發生錯誤: {e}")
        finally:
            db.close()  # 務必關閉連線，避免 MySQL 連線數爆掉

        # 背景每 60 秒掃描一次資料庫
        time.sleep(60)


if __name__ == "__main__":
    start_cron_scheduler()
