import pytest

from src.database import crud, schemas
from src.database.models import (
    ExecutionStatus,
    HttpMethod,
    ScheduleType,
    TriggerType,
    UserRole,
)
from src.worker import executor
from src.worker.schemas import TaskPayload

pytestmark = [pytest.mark.integration, pytest.mark.worker]


class FakeRedis:
    def __init__(self, acquire_lock=True):
        self.acquire_lock = acquire_lock
        self.deleted_keys = []

    def set(self, *args, **kwargs):
        return self.acquire_lock

    def delete(self, *args, **kwargs):
        self.deleted_keys.extend(args)
        return 1


class FakeQueueRedis(FakeRedis):
    def __init__(self, messages):
        super().__init__()
        self.messages = list(messages)
        self.blpop_calls = 0

    def blpop(self, *args, **kwargs):
        self.blpop_calls += 1
        if not self.messages:
            raise KeyboardInterrupt
        return ("job_priority_queue", self.messages.pop(0))


class FakeHeartbeat:
    def __init__(self, r_client, task):
        self.r_client = r_client
        self.task = task

    def start(self):
        return None

    def stop(self):
        return None

    def join(self):
        return None


def test_worker_process_task_updates_execution_and_log_reference(
    db_session,
    monkeypatch,
):
    user = crud.create_user(
        db=db_session,
        user_in=schemas.UserCreate(
            employee_id="worker_exec_user",
            username="WorkerUser",
            role=UserRole.DEVELOPER,
        ),
    )
    job = crud.create_job(
        db=db_session,
        owner_id=user.user_id,
        job_in=schemas.JobCreate(
            job_name="Worker HTTP",
            method=HttpMethod.GET,
            endpoint="http://test.com/worker",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )
    execution = crud.create_execution(
        db=db_session,
        job_id=job.job_id,
        trigger_type=TriggerType.MANUAL,
    )

    monkeypatch.setattr(executor, "SessionLocal", lambda: db_session)
    monkeypatch.setattr(db_session, "close", lambda: None)
    monkeypatch.setattr(
        executor,
        "run_http_task",
        lambda payload, timeout: {
            "status": "Success",
            "error_message": "",
            "log": "worker completed",
        },
    )
    monkeypatch.setattr(
        executor,
        "write_execution_log",
        lambda execution_id, content: (
            f"/app/logs/executions/exec-{execution_id}.log",
            len(content),
        ),
    )

    task = TaskPayload(
        execution_id=execution.execution_id,
        job_id=job.job_id,
        task_type="http",
        payload=crud.job_to_task_dict(job),
        timeout_threshold=60,
    )

    executor.process_task(task, FakeRedis())

    updated = crud.get_execution_by_id(db=db_session, execution_id=execution.execution_id)
    log_reference = crud.get_log_reference_by_execution_id(
        db=db_session,
        execution_id=execution.execution_id,
    )
    assert updated.status == ExecutionStatus.SUCCESS
    assert updated.start_time is not None
    assert updated.end_time is not None
    assert log_reference is not None
    assert log_reference.log_path.endswith(f"exec-{execution.execution_id}.log")


def _task_for_status(status):
    return TaskPayload(
        execution_id=9001,
        job_id=42,
        task_type="http",
        payload={
            "job_id": 42,
            "method": "GET",
            "endpoint": "http://test.com/status",
            "headers": {},
            "body": {},
            "timeout": 60,
        },
        timeout_threshold=60,
    )


def test_worker_reports_failed_status_on_task_failure(monkeypatch):
    reported_statuses = []
    monkeypatch.setattr(executor, "HeartbeatThread", FakeHeartbeat)
    monkeypatch.setattr(
        executor,
        "report_to_database",
        lambda execution_id, status, **kwargs: reported_statuses.append(status),
    )
    monkeypatch.setattr(
        executor,
        "run_http_task",
        lambda payload, timeout: {
            "status": "Failed",
            "error_message": "downstream failed",
        },
    )

    executor.process_task(_task_for_status("Failed"), FakeRedis())

    assert reported_statuses == [ExecutionStatus.RUNNING, ExecutionStatus.FAILED]


def test_worker_reports_timeout_status_on_task_timeout(monkeypatch):
    reported_statuses = []
    monkeypatch.setattr(executor, "HeartbeatThread", FakeHeartbeat)
    monkeypatch.setattr(
        executor,
        "report_to_database",
        lambda execution_id, status, **kwargs: reported_statuses.append(status),
    )
    monkeypatch.setattr(
        executor,
        "run_http_task",
        lambda payload, timeout: {"status": "Timeout", "error_message": "too slow"},
    )

    executor.process_task(_task_for_status("Timeout"), FakeRedis())

    assert reported_statuses == [ExecutionStatus.RUNNING, ExecutionStatus.TIMEOUT]


def test_worker_idempotency_lock_prevents_double_processing(monkeypatch):
    reported_statuses = []
    monkeypatch.setattr(
        executor,
        "report_to_database",
        lambda execution_id, status, **kwargs: reported_statuses.append(status),
    )
    monkeypatch.setattr(
        executor,
        "run_http_task",
        lambda payload, timeout: pytest.fail("duplicate task should not run"),
    )

    executor.process_task(_task_for_status("Success"), FakeRedis(acquire_lock=False))

    assert reported_statuses == []


def test_worker_loop_discards_invalid_json_and_keeps_listening(monkeypatch):
    fake_redis = FakeQueueRedis(["not-json"])
    monkeypatch.setattr(executor.Base.metadata, "create_all", lambda bind: None)
    monkeypatch.setattr(executor, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(
        executor,
        "process_task",
        lambda task, r_client: pytest.fail("invalid JSON should be discarded"),
    )

    with pytest.raises(KeyboardInterrupt):
        executor.worker_loop()

    assert fake_redis.blpop_calls == 2


def test_worker_loop_handles_invalid_task_payload_without_processing(monkeypatch):
    fake_redis = FakeQueueRedis(['{"execution_id": 1}'])
    monkeypatch.setattr(executor.Base.metadata, "create_all", lambda bind: None)
    monkeypatch.setattr(executor, "get_redis_client", lambda: fake_redis)
    monkeypatch.setattr(
        executor,
        "process_task",
        lambda task, r_client: pytest.fail("invalid payload should not run"),
    )
    monkeypatch.setattr(
        executor.time,
        "sleep",
        lambda seconds: (_ for _ in ()).throw(KeyboardInterrupt),
    )

    with pytest.raises(KeyboardInterrupt):
        executor.worker_loop()

    assert fake_redis.blpop_calls == 1
