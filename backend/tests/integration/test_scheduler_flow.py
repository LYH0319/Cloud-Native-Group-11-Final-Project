import pytest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta

# Import models, schemas, and crud functions
from src.database.models import (
    UserRole,
    HttpMethod,
    ScheduleType,
    JobStatus,
    ExecutionStatus,
    TriggerType,
    JobDependency,
)
from src.database import schemas
from src.database import crud

# Import the module to be tested
from src.scheduler.cron_scheduler import (
    check_predecessors_done,
    recover_stale_executions,
    start_cron_scheduler,
)

pytestmark = [pytest.mark.integration, pytest.mark.scheduler]

# ==========================================
# 1. Test: check_predecessors_done
# ==========================================


def test_check_predecessors_done_no_upstream(db_session):
    """Test that a job with no upstream dependencies returns True immediately."""
    # Arrange: Create a job with no dependencies
    user = schemas.UserCreate(
        employee_id="user_001", username="User 1", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    job_data = schemas.JobCreate(
        job_name="independent_job",
        method=HttpMethod.GET,
        endpoint="http://test.com",
        schedule_type=ScheduleType.ONE_TIME,
    )
    job = crud.create_job(db=db_session, owner_id=created_user.user_id, job_in=job_data)

    # Act: Call check_predecessors_done
    result = check_predecessors_done(db=db_session, job_id=job.job_id)

    # Assert: Verify the result is True
    assert result is True


def test_check_predecessors_done_upstream_success(db_session):
    """Test that a job returns True if its upstream job's latest execution is SUCCESS."""
    # Arrange:
    # 1. Create upstream job and downstream job
    user = schemas.UserCreate(
        employee_id="user_002", username="User 2", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    job_data = schemas.JobCreate(
        job_name="upstream",
        method=HttpMethod.GET,
        endpoint="http://test.com/up",
        schedule_type=ScheduleType.ONE_TIME,
    )
    upstream = crud.create_job(
        db=db_session, owner_id=created_user.user_id, job_in=job_data
    )

    downstream_data = schemas.JobCreate(
        job_name="downstream",
        method=HttpMethod.GET,
        endpoint="http://test.com/down",
        schedule_type=ScheduleType.ONE_TIME,
    )
    downstream = crud.create_job(
        db=db_session, owner_id=created_user.user_id, job_in=downstream_data
    )

    # 2. Create JobDependency linking them
    dep = JobDependency(upstream_id=upstream.job_id, downstream_id=downstream.job_id)
    db_session.add(dep)

    # 3. Create an Execution for upstream job with status SUCCESS
    exec_record = crud.create_execution(
        db=db_session, job_id=upstream.job_id, trigger_type=TriggerType.SCHEDULER
    )
    crud.update_execution_status(
        db=db_session,
        execution_id=exec_record.execution_id,
        status=ExecutionStatus.SUCCESS,
    )
    db_session.commit()

    # Act: Call check_predecessors_done on downstream job
    result = check_predecessors_done(db=db_session, job_id=downstream.job_id)

    # Assert: Verify the result is True
    assert result is True


def test_check_predecessors_done_upstream_no_execution(db_session):
    """Test that a job returns False if its upstream job has never been executed."""
    # Arrange:
    # 1. Create upstream job and downstream job
    user = schemas.UserCreate(
        employee_id="user_003", username="User 3", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    job_data = schemas.JobCreate(
        job_name="up",
        method=HttpMethod.GET,
        endpoint="http://a",
        schedule_type=ScheduleType.ONE_TIME,
    )
    upstream = crud.create_job(
        db=db_session, owner_id=created_user.user_id, job_in=job_data
    )

    downstream_data = schemas.JobCreate(
        job_name="down",
        method=HttpMethod.GET,
        endpoint="http://b",
        schedule_type=ScheduleType.ONE_TIME,
    )
    downstream = crud.create_job(
        db=db_session, owner_id=created_user.user_id, job_in=downstream_data
    )

    # 2. Create JobDependency
    dep = JobDependency(upstream_id=upstream.job_id, downstream_id=downstream.job_id)
    db_session.add(dep)

    # 3. DO NOT create any Execution records
    db_session.commit()

    # Act: Call check_predecessors_done on downstream job
    result = check_predecessors_done(db=db_session, job_id=downstream.job_id)

    # Assert: Verify the result is False
    assert result is False


def test_check_predecessors_done_upstream_failed(db_session):
    """Test that a job returns False if its upstream job's latest execution is FAILED."""
    # Arrange:
    # 1. Create upstream job and downstream job
    user = schemas.UserCreate(
        employee_id="user_004", username="User 4", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    job_data = schemas.JobCreate(
        job_name="up",
        method=HttpMethod.GET,
        endpoint="http://a",
        schedule_type=ScheduleType.ONE_TIME,
    )
    upstream = crud.create_job(
        db=db_session, owner_id=created_user.user_id, job_in=job_data
    )

    downstream_data = schemas.JobCreate(
        job_name="down",
        method=HttpMethod.GET,
        endpoint="http://b",
        schedule_type=ScheduleType.ONE_TIME,
    )
    downstream = crud.create_job(
        db=db_session, owner_id=created_user.user_id, job_in=downstream_data
    )

    # 2. Create JobDependency
    dep = JobDependency(upstream_id=upstream.job_id, downstream_id=downstream.job_id)
    db_session.add(dep)

    # 3. Create an Execution for upstream job with status FAILED
    exec_record = crud.create_execution(
        db=db_session, job_id=upstream.job_id, trigger_type=TriggerType.SCHEDULER
    )
    crud.update_execution_status(
        db=db_session,
        execution_id=exec_record.execution_id,
        status=ExecutionStatus.FAILED,
    )
    db_session.commit()

    # Act: Call check_predecessors_done on downstream job
    result = check_predecessors_done(db=db_session, job_id=downstream.job_id)

    # Assert: Verify the result is False
    assert result is False


# ==========================================
# 2. Test: start_cron_scheduler (Main Loop)
# ==========================================
# Note: We use patch on 'time.sleep' to raise StopIteration or InterruptedError
# to break the infinite 'while True' loop after exactly one iteration.
# We also patch 'dispatch_task' to prevent actual worker queue operations during tests.


@patch("src.scheduler.cron_scheduler.dispatch_task")
@patch("time.sleep", side_effect=InterruptedError)
def test_scheduler_processes_one_time_job(mock_sleep, mock_dispatch, db_session):
    """Test that a due ONE_TIME job is dispatched and its next_run_time is cleared to None."""
    # Arrange
    user = schemas.UserCreate(
        employee_id="0002_dev", username="Someone", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    job_data = schemas.JobCreate(
        job_name="trigger_billing_report",
        method=HttpMethod.POST,
        endpoint="https://api.internal.system.com/v1/billing/generate",
        schedule_type=ScheduleType.ONE_TIME,
        headers={"Authorization": "Bearer internal_service_token_123"},
        body={"target_region": "ap-northeast-1"},
    )

    past_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    job = crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=job_data,
        next_run_time=past_time,
    )

    # Act
    try:
        # Prevent the scheduler from closing the test's database session
        with patch.object(db_session, "close"):
            start_cron_scheduler(db_session_factory=lambda: db_session)
    except InterruptedError:
        pass

    # Assert
    mock_dispatch.assert_called_once()

    called_kwargs = mock_dispatch.call_args.kwargs
    assert called_kwargs["job_dict"]["job_id"] == job.job_id
    assert called_kwargs["job_dict"]["method"] == HttpMethod.POST.value

    db_session.refresh(job)
    assert job.next_run_time is None

    executions = crud.get_executions_by_job_id(db=db_session, job_id=job.job_id)
    assert len(executions) == 1
    assert executions[0].trigger_type == TriggerType.SCHEDULER


@patch("src.scheduler.cron_scheduler.dispatch_task")
@patch("time.sleep", side_effect=InterruptedError)
def test_scheduler_processes_recurring_job(mock_sleep, mock_dispatch, db_session):
    """Test that a due RECURRING job is dispatched and its next_run_time is correctly updated based on cron."""
    # Arrange
    user = schemas.UserCreate(
        employee_id="0003_dev", username="RecurringUser", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    job_data = schemas.JobCreate(
        job_name="trigger_billing_report",
        method=HttpMethod.POST,
        endpoint="https://api.internal.system.com/v1/billing/generate",
        schedule_type=ScheduleType.RECURRING,
        cron_expression="0 21 * * *",
        headers={"Authorization": "Bearer internal_service_token_123"},
        body={"target_region": "ap-northeast-1"},
    )

    past_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    job = crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=job_data,
        next_run_time=past_time,
    )

    # Act
    try:
        with patch.object(db_session, "close"):
            start_cron_scheduler(db_session_factory=lambda: db_session)
    except InterruptedError:
        pass

    # Assert
    mock_dispatch.assert_called_once()

    called_kwargs = mock_dispatch.call_args.kwargs
    assert called_kwargs["job_dict"]["job_id"] == job.job_id
    assert called_kwargs["job_dict"]["method"] == HttpMethod.POST.value

    db_session.refresh(job)
    now_utc = datetime.now(timezone.utc)

    assert job.next_run_time is not None
    assert job.next_run_time.replace(tzinfo=timezone.utc) > now_utc

    executions = crud.get_executions_by_job_id(db=db_session, job_id=job.job_id)
    assert len(executions) == 1
    assert executions[0].trigger_type == TriggerType.SCHEDULER


@patch("src.scheduler.cron_scheduler.dispatch_task")
@patch("time.sleep", side_effect=InterruptedError)
def test_scheduler_skips_job_when_dependency_not_met(
    mock_sleep, mock_dispatch, db_session
):
    """Test that a due job is NOT dispatched if its upstream dependencies are not fulfilled."""
    # Arrange
    user = schemas.UserCreate(
        employee_id="0004_dev", username="DepTest", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    upstream_data = schemas.JobCreate(
        job_name="upstream_job",
        method=HttpMethod.GET,
        endpoint="http://test.com/up",
        schedule_type=ScheduleType.ONE_TIME,
    )
    upstream_job = crud.create_job(
        db=db_session, owner_id=created_user.user_id, job_in=upstream_data
    )

    past_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    downstream_data = schemas.JobCreate(
        job_name="downstream_job",
        method=HttpMethod.GET,
        endpoint="http://test.com/down",
        schedule_type=ScheduleType.ONE_TIME,
    )
    downstream_job = crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=downstream_data,
        next_run_time=past_time,
    )

    crud.create_job_dependency(
        db=db_session,
        dependency_in=schemas.JobDependencyCreate(
            upstream_id=upstream_job.job_id, downstream_id=downstream_job.job_id
        ),
    )

    # Act
    try:
        with patch.object(db_session, "close"):
            start_cron_scheduler(db_session_factory=lambda: db_session)
    except InterruptedError:
        pass

    # Assert
    mock_dispatch.assert_not_called()

    db_session.refresh(downstream_job)
    assert downstream_job.next_run_time == past_time.replace(tzinfo=None)


@patch("src.scheduler.cron_scheduler.dispatch_task")
@patch("time.sleep", side_effect=InterruptedError)
def test_scheduler_skips_future_job(mock_sleep, mock_dispatch, db_session):
    user = schemas.UserCreate(
        employee_id="0004_future", username="FutureJob", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)
    crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=schemas.JobCreate(
            job_name="future_job",
            method=HttpMethod.GET,
            endpoint="http://test.com/future",
            schedule_type=ScheduleType.ONE_TIME,
        ),
        next_run_time=future_time,
    )

    try:
        with patch.object(db_session, "close"):
            start_cron_scheduler(db_session_factory=lambda: db_session)
    except InterruptedError:
        pass

    mock_dispatch.assert_not_called()


@patch("src.scheduler.cron_scheduler.dispatch_task")
@patch("time.sleep", side_effect=InterruptedError)
def test_scheduler_skips_inactive_job(mock_sleep, mock_dispatch, db_session):
    user = schemas.UserCreate(
        employee_id="0004_inactive", username="InactiveJob", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)
    past_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    job = crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=schemas.JobCreate(
            job_name="inactive_job",
            method=HttpMethod.GET,
            endpoint="http://test.com/inactive",
            schedule_type=ScheduleType.ONE_TIME,
        ),
        next_run_time=past_time,
    )
    crud.change_job_status(
        db=db_session, job_id=job.job_id, new_status=JobStatus.DISABLED
    )

    try:
        with patch.object(db_session, "close"):
            start_cron_scheduler(db_session_factory=lambda: db_session)
    except InterruptedError:
        pass

    mock_dispatch.assert_not_called()


@patch("src.scheduler.cron_scheduler.dispatch_task")
@patch("time.sleep", side_effect=InterruptedError)
def test_scheduler_dispatches_job_when_dependency_succeeded(
    mock_sleep, mock_dispatch, db_session
):
    user = schemas.UserCreate(
        employee_id="0004_dep_success",
        username="DepSuccess",
        role=UserRole.DEVELOPER,
    )
    created_user = crud.create_user(db=db_session, user_in=user)
    upstream_job = crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=schemas.JobCreate(
            job_name="upstream_done",
            method=HttpMethod.GET,
            endpoint="http://test.com/upstream-done",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )
    past_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    downstream_job = crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=schemas.JobCreate(
            job_name="downstream_ready",
            method=HttpMethod.GET,
            endpoint="http://test.com/downstream-ready",
            schedule_type=ScheduleType.ONE_TIME,
        ),
        next_run_time=past_time,
    )
    crud.create_job_dependency(
        db=db_session,
        dependency_in=schemas.JobDependencyCreate(
            upstream_id=upstream_job.job_id,
            downstream_id=downstream_job.job_id,
        ),
    )
    upstream_execution = crud.create_execution(
        db=db_session,
        job_id=upstream_job.job_id,
        trigger_type=TriggerType.SCHEDULER,
    )
    crud.update_execution_status(
        db=db_session,
        execution_id=upstream_execution.execution_id,
        status=ExecutionStatus.SUCCESS,
    )

    try:
        with patch.object(db_session, "close"):
            start_cron_scheduler(db_session_factory=lambda: db_session)
    except InterruptedError:
        pass

    mock_dispatch.assert_called_once()
    assert mock_dispatch.call_args.kwargs["job_dict"]["job_id"] == downstream_job.job_id


@patch("src.scheduler.cron_scheduler.dispatch_task")
@patch("time.sleep", side_effect=InterruptedError)
def test_scheduler_handles_invalid_cron_expression(
    mock_sleep, mock_dispatch, db_session
):
    """Test that an invalid cron expression prevents crash, dispatches the job, and sets next_run_time to None."""
    # Arrange
    user = schemas.UserCreate(
        employee_id="0005_dev", username="CronFailTest", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    past_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    job_data = schemas.JobCreate(
        job_name="bad_cron_job",
        method=HttpMethod.GET,
        endpoint="http://test.com/bad",
        schedule_type=ScheduleType.RECURRING,
        cron_expression="invalid_cron_format",
    )
    job = crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=job_data,
        next_run_time=past_time,
    )

    # Act
    try:
        with patch.object(db_session, "close"):
            start_cron_scheduler(db_session_factory=lambda: db_session)
    except InterruptedError:
        pass

    # Assert
    mock_dispatch.assert_called_once()

    db_session.refresh(job)
    assert job.next_run_time is None


@patch("src.scheduler.cron_scheduler.dispatch_task")
@patch("time.sleep", side_effect=InterruptedError)
def test_scheduler_db_rollback_on_exception(mock_sleep, mock_dispatch, db_session):
    """Test that if an exception occurs during the iteration, a database rollback is triggered."""
    # Arrange
    user = schemas.UserCreate(
        employee_id="0006_dev", username="RollbackTest", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    past_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    job_data = schemas.JobCreate(
        job_name="rollback_job",
        method=HttpMethod.GET,
        endpoint="http://test.com/rollback",
        schedule_type=ScheduleType.ONE_TIME,
    )
    job = crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=job_data,
        next_run_time=past_time,
    )

    mock_dispatch.side_effect = Exception("Simulated dispatch failure")

    # Act
    try:
        with patch.object(db_session, "close"):
            start_cron_scheduler(db_session_factory=lambda: db_session)
    except InterruptedError:
        pass

    # Assert
    db_session.refresh(job)
    assert job.next_run_time == past_time.replace(tzinfo=None)

    executions = crud.get_executions_by_job_id(db=db_session, job_id=job.job_id)
    assert len(executions) == 1
    assert executions[0].status == ExecutionStatus.PENDING


def test_recover_stale_execution_marks_timeout_and_retries(db_session):
    user = schemas.UserCreate(
        employee_id="0007_stale", username="StaleWorker", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)
    job = crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=schemas.JobCreate(
            job_name="stale_job",
            method=HttpMethod.GET,
            endpoint="http://test.com/stale",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )
    execution = crud.create_execution(
        db=db_session,
        job_id=job.job_id,
        trigger_type=TriggerType.SCHEDULER,
    )
    crud.update_execution_status(
        db=db_session,
        execution_id=execution.execution_id,
        status=ExecutionStatus.RUNNING,
        worker_id="dead-worker",
    )
    stale_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    execution.last_heartbeat = stale_time
    execution.start_time = stale_time
    db_session.commit()

    dispatched = []
    retried = recover_stale_executions(
        db=db_session,
        now_utc=datetime.now(timezone.utc),
        stale_after_seconds=60,
        max_retries=1,
        dispatch_fn=lambda **kwargs: dispatched.append(kwargs),
    )

    db_session.refresh(execution)
    assert execution.status == ExecutionStatus.TIMEOUT
    assert execution.error_message is not None
    assert retried
    assert retried[0].retry_count == 1
    assert dispatched[0]["execution_id"] == retried[0].execution_id
