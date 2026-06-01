import pytest
import redis
import json
import time
from src.worker.schemas import TaskPayload
from src.worker.executor import process_task, get_redis_client
from src.database.models import ExecutionStatus, UserRole, HttpMethod, ScheduleType, TriggerType
from src.database import schemas, crud
from config.setting import settings

# ==================================================================
# 1. 整合測試專用 Fixture 設定 (維持純淨，測試完自動 rollback)
# ==================================================================

@pytest.fixture
def real_redis():
    """連線到真實的測試環境 Redis，並在測試前後清理 Queue"""
    client = get_redis_client()
    client.delete(settings.JOB_QUEUE_NAME)
    yield client
    client.delete(settings.JOB_QUEUE_NAME)
    client.close()


@pytest.fixture
def integration_user(db_session):
    """在真實資料庫中建立一個測試用使用者"""
    user_data = schemas.UserCreate(
        employee_id="9999_worker_test", 
        username="WorkerIntegrationTester", 
        role=UserRole.DEVELOPER
    )
    return crud.create_user(db=db_session, user_in=user_data)


# ==================================================================
# 2. 核心五大狀態完整整合測試案例
# ==================================================================

def test_worker_integration_http_success(db_session, real_redis, integration_user):
    """【整合測試】驗證正常情境：Worker 執行真實 HTTP 請求成功，同步更新 DB 為 SUCCESS"""
    # ─── Arrange ───
    job_data = schemas.JobCreate(
        job_name="int_success", 
        method=HttpMethod.GET, 
        endpoint="https://httpbin.org/get", 
        schedule_type=ScheduleType.ONE_TIME,
        headers={"X-Test-Header": "IntegrationWorker"},
        body={}
    )
    job = crud.create_job(db=db_session, owner_id=integration_user.user_id, job_in=job_data)
    execution = crud.create_execution(db=db_session, job_id=job.job_id, trigger_type=TriggerType.MANUAL)
    db_session.commit()  # 確保初始 PENDING 狀態成功落地入庫

    task_payload = TaskPayload(
        execution_id=execution.execution_id, 
        job_id=job.job_id, 
        task_type="http",
        payload={
            "method": job.method.value,
            "endpoint": job.endpoint,
            "headers": job.headers or {},
            "body": job.body or {}
        }, 
        timeout_threshold=15
    )

    # ─── Act ───
    process_task(task_payload, real_redis, db=db_session)
    
    # ─── Assert ───
    db_session.refresh(execution)
    # 1. 驗證狀態機 (成功時，error_message 必須不具備真值，即為 None 或 "")
    assert execution.status == ExecutionStatus.SUCCESS
    assert not execution.error_message  # ✨ 修正：使用 not 確保相容 None 或 ""
    
    # 2. 驗證自動計算執行耗時（Duration）
    assert execution.duration is not None and execution.duration > 0
    
    # 3. 驗證日誌落實與可觀測性（Observability）
    #assert execution.log_path is not None
    #assert execution.log_size > 0

    # 4. 驗證 Redis 內部暫存資源是否有被優雅釋放
    assert real_redis.exists(f"exec_active:{execution.execution_id}") == 0
    assert real_redis.exists(f"heartbeat:exec_{execution.execution_id}") == 0


def test_worker_integration_http_failed(db_session, real_redis, integration_user):
    """【整合測試】驗證業務失敗：當真實請求遭遇 404，Worker 應正確將狀態轉為 FAILED"""
    # ─── Arrange ───
    job_data = schemas.JobCreate(
        job_name="int_404", method=HttpMethod.GET, endpoint="https://httpbin.org/status/404", schedule_type=ScheduleType.ONE_TIME
    )
    job = crud.create_job(db=db_session, owner_id=integration_user.user_id, job_in=job_data)
    execution = crud.create_execution(db=db_session, job_id=job.job_id, trigger_type=TriggerType.MANUAL)
    db_session.commit()

    task_payload = TaskPayload(
        execution_id=execution.execution_id, job_id=job.job_id, task_type="http",
        payload={"method": job.method.value, "endpoint": job.endpoint}, timeout_threshold=10
    )

    # ─── Act ───
    process_task(task_payload, real_redis, db=db_session)
    
    # ─── Assert ───
    db_session.refresh(execution)
    assert execution.status == ExecutionStatus.FAILED
    assert execution.error_message is not None


def test_worker_integration_http_timeout(db_session, real_redis, integration_user):
    """【整合測試】驗證超時機制（TIMEOUT）：當目標伺服器回應過慢，Worker 應精準判定超時並更新 DB"""
    # ─── Arrange ───
    job_data = schemas.JobCreate(
        job_name="int_timeout", method=HttpMethod.GET, 
        endpoint="https://httpbin.org/delay/5",  # 故意讓伺服器延遲 5 秒回應
        schedule_type=ScheduleType.ONE_TIME
    )
    job = crud.create_job(db=db_session, owner_id=integration_user.user_id, job_in=job_data)
    execution = crud.create_execution(db=db_session, job_id=job.job_id, trigger_type=TriggerType.MANUAL)
    db_session.commit()

    task_payload = TaskPayload(
        execution_id=execution.execution_id, job_id=job.job_id, task_type="http",
        payload={"method": job.method.value, "endpoint": job.endpoint}, 
        timeout_threshold=1  # 門檻只給 1 秒，強迫引發超時！
    )

    # ─── Act ───
    process_task(task_payload, real_redis, db=db_session)

    # ─── Assert ───
    db_session.refresh(execution)
    assert execution.status == ExecutionStatus.TIMEOUT


def test_worker_integration_idempotency_blocked(db_session, real_redis, integration_user):
    """【整合測試】驗證分散式防重鎖（Idempotency）：當鎖已被佔用，任務應直接丟棄，資料庫維持 PENDING"""
    # ─── Arrange ───
    job_data = schemas.JobCreate(
        job_name="int_idem", method=HttpMethod.GET, endpoint="https://httpbin.org/get", schedule_type=ScheduleType.ONE_TIME
    )
    job = crud.create_job(db=db_session, owner_id=integration_user.user_id, job_in=job_data)
    execution = crud.create_execution(db=db_session, job_id=job.job_id, trigger_type=TriggerType.MANUAL)
    db_session.commit()  # 確立這一筆任務在 DB 是純潔的 PENDING

    # 關鍵情境模擬：在主執行序開跑前，Redis 內對該真實 ID 的防重鎖就已經被另一個節點佔用了
    idempotency_key = f"exec_active:{execution.execution_id}"
    real_redis.set(idempotency_key, "RUNNING", ex=60)

    task_payload = TaskPayload(
        execution_id=execution.execution_id, job_id=job.job_id, task_type="http",
        payload={"method": job.method.value, "endpoint": job.endpoint}, timeout_threshold=10
    )

    # ─── Act ───
    process_task(task_payload, real_redis, db=db_session)

    # ─── Assert ───
    db_session.refresh(execution)
    # 因為搶鎖失敗，Worker 必須直接 return，此任務在資料庫不可被更動，必須穩穩維持原本的 PENDING 狀態！
    assert execution.status == ExecutionStatus.PENDING
    
    # 清理測試資源
    real_redis.delete(idempotency_key)


def test_worker_integration_inner_crash(db_session, real_redis, integration_user):
    """【整合測試】驗證系統級異常：當任務類型不支援引發 Worker 內核崩潰時，安全網機制應確保 DB 寫入 FAILED"""
    # ─── Arrange ───
    job_data = schemas.JobCreate(
        job_name="int_crash", method=HttpMethod.GET, endpoint="https://httpbin.org/get", schedule_type=ScheduleType.ONE_TIME
    )
    job = crud.create_job(db=db_session, owner_id=integration_user.user_id, job_in=job_data)
    execution = crud.create_execution(db=db_session, job_id=job.job_id, trigger_type=TriggerType.MANUAL)
    db_session.commit()

    task_payload = TaskPayload(
        execution_id=execution.execution_id, job_id=job.job_id, 
        task_type="INVALID_TASK_TYPE",  # 故意給予不支援的類型引發 Exception
        payload={"method": job.method.value, "endpoint": job.endpoint}, timeout_threshold=10
    )

    # ─── Act ───
    process_task(task_payload, real_redis, db=db_session)

    # ─── Assert ───
    db_session.refresh(execution)
    assert execution.status == ExecutionStatus.FAILED
    assert "Worker Inner Crash" in execution.error_message