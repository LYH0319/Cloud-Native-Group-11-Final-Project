from src.database import crud, schemas
from src.database.models import ExecutionStatus, HttpMethod, ScheduleType, TriggerType, UserRole
from src.worker import executor
from src.worker.schemas import TaskPayload


class FakeRedis:
    def set(self, *args, **kwargs):
        return True

    def delete(self, *args, **kwargs):
        return 1


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
