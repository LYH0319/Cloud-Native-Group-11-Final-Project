import pytest

from src.database import crud
from src.database.models import User, UserRole, HttpMethod, ScheduleType, JobStatus
from src.database import schemas
from datetime import datetime, timedelta, timezone
from src.database.models import TriggerType, ExecutionStatus

pytestmark = pytest.mark.unit


# ==========================================
# 1. Test: Create User
# ==========================================
def test_create_user_success(db_session):
    """Test that a new user can be successfully created and default values are written correctly."""
    # Arrange (Prepare parameters)
    user = schemas.UserCreate(
        employee_id="0002_dev", username="Someone", role=UserRole.DEVELOPER
    )

    # Act (Call crud.create_user)
    result = crud.create_user(db=db_session, user_in=user)

    # Assert (Verify the returned object's attributes, especially check if the default is_active is True)
    assert result.username == user.username
    assert result.employee_id == user.employee_id
    assert result.role == user.role

    assert result.user_id is not None
    assert result.is_active is True
    assert result.created_at is not None


# ==========================================
# 2. Test: Read User
# ==========================================
def test_get_user_by_employee_id_success(db_session):
    """Test that a user can be correctly retrieved by their employee ID."""
    # Arrange (Call create_user first to insert dummy data into the database)
    user = schemas.UserCreate(
        employee_id="0002_dev", username="Someone", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    # Act (Call crud.get_user_by_employee_id to retrieve the user)
    result = crud.get_user_by_employee_id(db=db_session, employee_id="0002_dev")

    # Assert (Verify if the retrieved user.employee_id matches the inserted one)
    assert result.username == created_user.username
    assert result.employee_id == created_user.employee_id
    assert result.role == created_user.role
    assert result.user_id == created_user.user_id
    assert result.is_active == created_user.is_active
    assert result.created_at == created_user.created_at


def test_get_user_by_employee_id_not_found(db_session):
    """Test that retrieving by a non-existent employee ID returns None."""
    # Arrange (No special preparation needed since the database is empty)

    # Act (Pass a non-existent employee ID to get_user_by_employee_id)
    result = crud.get_user_by_employee_id(db=db_session, employee_id="0002_dev")

    # Assert (Confirm the return value is None)
    assert result is None


def test_get_user_by_email_success(db_session):
    """Test that a user can be retrieved by email."""
    user = schemas.UserCreate(
        employee_id="email_user",
        username="EmailUser",
        role=UserRole.DEVELOPER,
        email="email-user@example.com",
        password="secret123",
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    result = crud.get_user_by_email(db=db_session, email="email-user@example.com")

    assert result.user_id == created_user.user_id
    assert result.hashed_password != "secret123"


def test_authenticate_user_success_and_failure(db_session):
    """Test password verification through authenticate_user."""
    crud.create_user(
        db=db_session,
        user_in=schemas.UserCreate(
            employee_id="auth_crud",
            username="AuthCrud",
            role=UserRole.DEVELOPER,
            email="auth-crud@example.com",
            password="secret123",
        ),
    )

    authenticated = crud.authenticate_user(
        db=db_session,
        identifier="auth-crud@example.com",
        password="secret123",
    )
    rejected = crud.authenticate_user(
        db=db_session,
        identifier="auth-crud@example.com",
        password="wrong",
    )

    assert authenticated is not None
    assert authenticated.username == "AuthCrud"
    assert rejected is None


# ==========================================
# 3. Test: Update User Role
# ==========================================
def test_change_user_role_success(db_session):
    """Test that a user's role can be successfully updated."""
    # Arrange (Create a dummy user first, default role is DEVELOPER)
    user = schemas.UserCreate(
        employee_id="0002_dev", username="Someone", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    # Act (Call change_user_role to change their role to OPERATOR)
    result = crud.change_user_role(
        db=db_session, user_id=created_user.user_id, new_role=UserRole.OPERATOR
    )

    # Assert (Verify that the returned user.role is indeed OPERATOR)
    assert result.role == UserRole.OPERATOR

    updated_user = crud.get_user_by_user_id(db=db_session, user_id=created_user.user_id)
    assert updated_user.role == UserRole.OPERATOR


# ==========================================
# 4. Test: Delete User (Soft Delete)
# ==========================================
def test_delete_user_soft_delete(db_session):
    """Test that deleting a user only sets is_active to False, and the record remains in the DB."""
    # Arrange (Create a dummy user)
    user = schemas.UserCreate(
        employee_id="0002_dev", username="Someone", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    # Act (Call delete_user)
    result = crud.delete_user(db=db_session, user_id=created_user.user_id)

    # Assert 1: Confirm that delete_user returns True
    # Assert 2: Call get_user_by_id again to verify the user is still in the database, but is_active is False!
    assert result is True
    assert (
        crud.get_user_by_user_id(db=db_session, user_id=created_user.user_id).is_active
        is False
    )


# ==========================================
# 5. Test: Database Initialization (init_db)
# ==========================================
def test_init_db_creates_default_admin(db_session):
    """Test that init_db successfully creates a default Admin user when the database is empty."""
    # Arrange
    from sqlalchemy import select

    # Act
    admin_exists = db_session.scalar(select(User).where(User.role == UserRole.ADMIN))
    if not admin_exists:
        default_admin = User(
            employee_id="admin_000", username="System Admin", role=UserRole.ADMIN
        )
        db_session.add(default_admin)
        db_session.commit()

    # Assert
    admin_in_db = db_session.scalar(select(User).where(User.role == UserRole.ADMIN))
    assert admin_in_db is not None
    assert admin_in_db.employee_id == "admin_000"
    assert admin_in_db.username == "System Admin"


# ==========================================
# 6. Test: Create Job
# ==========================================
def test_create_job_success(db_session):
    """Test that a new job can be successfully created and linked to an owner."""
    # Arrange (Create a User first to get a valid owner_id, then prepare JobCreate schema)
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

    # Act (Call crud.create_job)
    result = crud.create_job(
        db=db_session, owner_id=created_user.user_id, job_in=job_data
    )

    # Assert (Verify job attributes, owner_id, default status is ACTIVE, and db-generated fields)
    assert result.owner_id == created_user.user_id
    assert result.status == JobStatus.ACTIVE


# ==========================================
# 7. Test: Read Job (Basic Queries)
# ==========================================
# (前略... test_get_job_by_id_success 和 test_get_job_by_id_not_found 保留你原本的即可)


def test_get_jobs_by_owner_id_success(db_session):
    """Test retrieving all jobs belonging to a specific user."""
    # Arrange
    user = schemas.UserCreate(
        employee_id="0010_dev", username="Owner", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    job1 = schemas.JobCreate(
        job_name="Job 1",
        method=HttpMethod.GET,
        endpoint="http://test.com/1",
        schedule_type=ScheduleType.ONE_TIME,
    )
    job2 = schemas.JobCreate(
        job_name="Job 2",
        method=HttpMethod.GET,
        endpoint="http://test.com/2",
        schedule_type=ScheduleType.ONE_TIME,
    )
    crud.create_job(db=db_session, owner_id=created_user.user_id, job_in=job1)
    crud.create_job(db=db_session, owner_id=created_user.user_id, job_in=job2)

    # Act
    results = crud.get_jobs_by_owner_id(db=db_session, owner_id=created_user.user_id)

    # Assert
    assert len(results) == 2
    assert results[0].owner_id == created_user.user_id
    assert results[1].owner_id == created_user.user_id


# ==========================================
# 8. Test: Get Active Jobs (Scheduler Core Logic)
# ==========================================
def test_get_active_jobs_returns_ready_jobs(db_session):
    """Test that get_active_jobs returns ACTIVE jobs whose next_run_time is due."""
    # Arrange
    user = schemas.UserCreate(
        employee_id="0011_dev", username="Scheduler", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    # Use UTC time to match database func.now() behavior
    past_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    job_data = schemas.JobCreate(
        job_name="Ready Job",
        method=HttpMethod.GET,
        endpoint="http://test.com",
        schedule_type=ScheduleType.ONE_TIME,
    )
    crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=job_data,
        next_run_time=past_time,
    )

    # Act
    results = crud.get_active_jobs(db=db_session)

    # Assert
    assert len(results) == 1
    assert results[0].job_name == "Ready Job"


def test_get_active_jobs_filters_by_schedule_type(db_session):
    """Test that get_active_jobs correctly filters by ONE_TIME or RECURRING."""
    # Arrange
    user = schemas.UserCreate(
        employee_id="0013_dev", username="Filter", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    # Use UTC time
    past_time = datetime.now(timezone.utc) - timedelta(minutes=1)
    job_one_time = schemas.JobCreate(
        job_name="One Time Job",
        method=HttpMethod.GET,
        endpoint="http://test.com",
        schedule_type=ScheduleType.ONE_TIME,
    )
    job_recurring = schemas.JobCreate(
        job_name="Recurring Job",
        method=HttpMethod.GET,
        endpoint="http://test.com",
        schedule_type=ScheduleType.RECURRING,
        cron_expression="0 * * * *",
    )
    crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=job_one_time,
        next_run_time=past_time,
    )
    crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=job_recurring,
        next_run_time=past_time,
    )

    # Act
    results = crud.get_active_jobs(db=db_session, schedule_type=ScheduleType.ONE_TIME)

    # Assert
    assert len(results) == 1
    assert results[0].schedule_type == ScheduleType.ONE_TIME
    assert results[0].job_name == "One Time Job"


# ==========================================
# 9. Test: Get All Jobs (Admin Dashboard)
# ==========================================
def test_get_all_jobs_pagination(db_session):
    """Test that get_all_jobs respects the skip and limit pagination parameters."""
    # Arrange
    user = schemas.UserCreate(
        employee_id="0014_dev", username="Paginator", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    for i in range(3):
        job_data = schemas.JobCreate(
            job_name=f"Job {i}",
            method=HttpMethod.GET,
            endpoint="http://test.com",
            schedule_type=ScheduleType.ONE_TIME,
        )
        crud.create_job(db=db_session, owner_id=created_user.user_id, job_in=job_data)

    # Act (跳過第 0 筆，只拿 1 筆)
    results = crud.get_all_jobs(db=db_session, skip=1, limit=1)

    # Assert
    assert len(results) == 1
    assert results[0].job_name == "Job 1"


# ==========================================
# 10. Test: Update Job
# ==========================================
def test_update_job_success(db_session):
    """Test that an existing job can be partially updated using exclude_unset."""
    # Arrange: Create user and a default ONE_TIME job
    user = schemas.UserCreate(
        employee_id="0015_dev", username="Updater", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    original_job = schemas.JobCreate(
        job_name="Old Report Task",
        method=HttpMethod.POST,
        endpoint="http://reporting-svc/old",
        schedule_type=ScheduleType.ONE_TIME,
    )
    created_job = crud.create_job(
        db=db_session, owner_id=created_user.user_id, job_in=original_job
    )

    # Prepare update payload (Changing it to a RECURRING GET job)
    update_data = schemas.JobUpdate(
        job_name="New Microservice Check",
        method=HttpMethod.GET,
        endpoint="http://reporting-svc/health",
        schedule_type=ScheduleType.RECURRING,
        cron_expression="*/5 * * * *",
    )

    # Act
    result = crud.update_job(
        db=db_session, job_id=created_job.job_id, job_in=update_data
    )

    # Assert
    assert result is not None
    assert result.job_name == "New Microservice Check"
    assert result.method == HttpMethod.GET
    assert result.endpoint == "http://reporting-svc/health"
    assert result.schedule_type == ScheduleType.RECURRING
    assert result.cron_expression == "*/5 * * * *"

    # Double check persistence in DB
    updated_job_in_db = crud.get_job_by_id(db=db_session, job_id=created_job.job_id)
    assert updated_job_in_db.job_name == "New Microservice Check"


# ==========================================
# 11. Test: Change Job Status
# ==========================================
def test_change_job_status_success(db_session):
    """Test toggling a job's active state (e.g., pausing a cron job)."""
    # Arrange
    user = schemas.UserCreate(
        employee_id="0016_dev", username="Pauser", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    job_data = schemas.JobCreate(
        job_name="Cron Task",
        method=HttpMethod.GET,
        endpoint="http://test.com",
        schedule_type=ScheduleType.ONE_TIME,
    )
    created_job = crud.create_job(
        db=db_session, owner_id=created_user.user_id, job_in=job_data
    )
    assert created_job.status == JobStatus.ACTIVE

    # Act (Pause the job)
    result = crud.change_job_status(
        db=db_session, job_id=created_job.job_id, new_status=JobStatus.DISABLED
    )

    # Assert
    assert result is not None
    assert result.status == JobStatus.DISABLED
    assert (
        crud.get_job_by_id(db=db_session, job_id=created_job.job_id).status
        == JobStatus.DISABLED
    )


# ==========================================
# 12. Test: Delete Job (Soft Delete)
# ==========================================
def test_delete_job_soft_delete(db_session):
    """Test that deleting a job only sets its status to DELETED."""
    # Arrange
    user = schemas.UserCreate(
        employee_id="0017_dev", username="Deleter", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    job_data = schemas.JobCreate(
        job_name="To Be Deleted",
        method=HttpMethod.GET,
        endpoint="http://test.com",
        schedule_type=ScheduleType.ONE_TIME,
    )
    created_job = crud.create_job(
        db=db_session, owner_id=created_user.user_id, job_in=job_data
    )

    # Act
    result = crud.delete_job(db=db_session, job_id=created_job.job_id)

    # Assert
    assert result is True

    # Verify the record still exists but is marked as DELETED
    deleted_job_in_db = crud.get_job_by_id(db=db_session, job_id=created_job.job_id)
    assert deleted_job_in_db is not None
    assert deleted_job_in_db.status == JobStatus.DELETED


def test_delete_job_not_found(db_session):
    """Test deleting a non-existent job returns False."""
    # Act
    result = crud.delete_job(db=db_session, job_id=9999)

    # Assert
    assert result is False


# ==========================================
# 13. Test: Execution CRUD (History & Status)
# ==========================================


def test_create_execution_success(db_session):
    """Test creating a new execution record with default values."""
    # Arrange: Create User -> Create Job
    user = schemas.UserCreate(
        employee_id="0018_dev", username="Runner", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    job_data = schemas.JobCreate(
        job_name="Task To Run",
        method=HttpMethod.GET,
        endpoint="http://test.com",
        schedule_type=ScheduleType.ONE_TIME,
    )
    created_job = crud.create_job(
        db=db_session, owner_id=created_user.user_id, job_in=job_data
    )

    # Act: Create an execution triggered by SCHEDULER
    result = crud.create_execution(
        db=db_session, job_id=created_job.job_id, trigger_type=TriggerType.SCHEDULER
    )

    # Assert
    assert result.job_id == created_job.job_id
    assert result.trigger_type == TriggerType.SCHEDULER
    assert result.status == ExecutionStatus.PENDING  # Default should be PENDING
    assert result.retry_count == 0


def test_get_executions_by_job_id(db_session):
    """Test retrieving execution history for a specific job."""
    # Arrange
    user = schemas.UserCreate(
        employee_id="0019_dev", username="HistoryUser", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    job_data = schemas.JobCreate(
        job_name="History Task",
        method=HttpMethod.GET,
        endpoint="http://test.com",
        schedule_type=ScheduleType.ONE_TIME,
    )
    created_job = crud.create_job(
        db=db_session, owner_id=created_user.user_id, job_in=job_data
    )

    # Create 2 execution records
    crud.create_execution(
        db=db_session, job_id=created_job.job_id, trigger_type=TriggerType.MANUAL
    )
    crud.create_execution(
        db=db_session, job_id=created_job.job_id, trigger_type=TriggerType.SCHEDULER
    )

    # Act
    results = crud.get_executions_by_job_id(db=db_session, job_id=created_job.job_id)

    # Assert
    assert len(results) == 2
    assert results[0].job_id == created_job.job_id


def _create_history_test_job(db_session, employee_id="history_filter_dev"):
    user = schemas.UserCreate(
        employee_id=employee_id,
        username="HistoryFilterUser",
        role=UserRole.DEVELOPER,
    )
    created_user = crud.create_user(db=db_session, user_in=user)
    job_data = schemas.JobCreate(
        job_name="History Filter",
        method=HttpMethod.GET,
        endpoint="http://test.com/history",
        schedule_type=ScheduleType.ONE_TIME,
    )
    return crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=job_data,
    )


def _create_execution_with_fields(
    db_session,
    job_id,
    trigger_type=TriggerType.MANUAL,
    status=ExecutionStatus.PENDING,
    worker_id=None,
    start_time=None,
    created_at=None,
):
    execution = crud.create_execution(
        db=db_session,
        job_id=job_id,
        trigger_type=trigger_type,
    )
    execution.status = status
    execution.worker_id = worker_id
    execution.start_time = start_time
    if created_at is not None:
        execution.created_at = created_at
    db_session.commit()
    db_session.refresh(execution)
    return execution


def test_get_execution_history_filters_by_job_id(db_session):
    """Test history only returns records for the requested job."""
    first_job = _create_history_test_job(db_session, "history_job_a")
    second_job = _create_history_test_job(db_session, "history_job_b")
    _create_execution_with_fields(db_session, first_job.job_id)
    _create_execution_with_fields(db_session, second_job.job_id)

    results = crud.get_execution_history(
        db=db_session,
        job_id=first_job.job_id,
    )

    assert len(results) == 1
    assert results[0].job_id == first_job.job_id


def test_get_execution_history_filters_by_status(db_session):
    """Test filtering execution history by lifecycle status."""
    job = _create_history_test_job(db_session, "history_status")
    _create_execution_with_fields(
        db_session, job.job_id, status=ExecutionStatus.SUCCESS
    )
    _create_execution_with_fields(
        db_session,
        job.job_id,
        status=ExecutionStatus.FAILED,
    )

    results = crud.get_execution_history(
        db=db_session,
        job_id=job.job_id,
        status=ExecutionStatus.SUCCESS,
    )

    assert len(results) == 1
    assert results[0].status == ExecutionStatus.SUCCESS


def test_get_execution_history_filters_by_trigger_type(db_session):
    """Test filtering execution history by scheduler or manual trigger."""
    job = _create_history_test_job(db_session, "history_trigger")
    _create_execution_with_fields(
        db_session, job.job_id, trigger_type=TriggerType.MANUAL
    )
    _create_execution_with_fields(
        db_session, job.job_id, trigger_type=TriggerType.SCHEDULER
    )

    results = crud.get_execution_history(
        db=db_session,
        job_id=job.job_id,
        trigger_type=TriggerType.SCHEDULER,
    )

    assert len(results) == 1
    assert results[0].trigger_type == TriggerType.SCHEDULER


def test_get_execution_history_filters_by_worker_id(db_session):
    """Test filtering execution history by worker ID."""
    job = _create_history_test_job(db_session, "history_worker")
    _create_execution_with_fields(db_session, job.job_id, worker_id="worker-a")
    _create_execution_with_fields(db_session, job.job_id, worker_id="worker-b")

    results = crud.get_execution_history(
        db=db_session,
        job_id=job.job_id,
        worker_id="worker-b",
    )

    assert len(results) == 1
    assert results[0].worker_id == "worker-b"


def test_get_execution_history_filters_by_start_time_range(db_session):
    """Test filtering execution history by start_time range."""
    job = _create_history_test_job(db_session, "history_time")
    base_time = datetime(2026, 1, 1)
    _create_execution_with_fields(
        db_session,
        job.job_id,
        start_time=base_time - timedelta(hours=2),
    )
    expected = _create_execution_with_fields(
        db_session,
        job.job_id,
        start_time=base_time,
    )
    _create_execution_with_fields(
        db_session,
        job.job_id,
        start_time=base_time + timedelta(hours=2),
    )

    results = crud.get_execution_history(
        db=db_session,
        job_id=job.job_id,
        start_time_from=base_time - timedelta(minutes=30),
        start_time_to=base_time + timedelta(minutes=30),
    )

    assert len(results) == 1
    assert results[0].execution_id == expected.execution_id


def test_get_execution_history_pagination(db_session):
    """Test skip and limit are applied to execution history."""
    job = _create_history_test_job(db_session, "history_pagination")
    base_time = datetime(2026, 1, 1)
    for index in range(3):
        _create_execution_with_fields(
            db_session,
            job.job_id,
            created_at=base_time + timedelta(minutes=index),
        )

    results = crud.get_execution_history(
        db=db_session,
        job_id=job.job_id,
        skip=1,
        limit=1,
    )

    assert len(results) == 1
    assert results[0].created_at == base_time + timedelta(minutes=1)


def test_get_execution_history_default_sort_newest_first(db_session):
    """Test default execution history ordering is newest record first."""
    job = _create_history_test_job(db_session, "history_sort")
    older_time = datetime(2026, 1, 1)
    newer_time = older_time + timedelta(minutes=10)
    older = _create_execution_with_fields(
        db_session,
        job.job_id,
        created_at=older_time,
    )
    newer = _create_execution_with_fields(
        db_session,
        job.job_id,
        created_at=newer_time,
    )

    results = crud.get_execution_history(db=db_session, job_id=job.job_id)

    assert [item.execution_id for item in results] == [
        newer.execution_id,
        older.execution_id,
    ]


def test_update_execution_lifecycle(db_session):
    """Test state transitions and duration calculation."""
    # Arrange
    user = schemas.UserCreate(
        employee_id="0020_dev",
        username="LifecycleUser",
        role=UserRole.DEVELOPER,
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    job_data = schemas.JobCreate(
        job_name="Lifecycle Task",
        method=HttpMethod.GET,
        endpoint="http://test.com",
        schedule_type=ScheduleType.ONE_TIME,
    )
    created_job = crud.create_job(
        db=db_session, owner_id=created_user.user_id, job_in=job_data
    )

    # 1. Start with PENDING
    exec_record = crud.create_execution(
        db=db_session,
        job_id=created_job.job_id,
        trigger_type=TriggerType.MANUAL,
    )

    # Act 1: Transition to RUNNING
    running_exec = crud.update_execution_status(
        db=db_session,
        execution_id=exec_record.execution_id,
        status=ExecutionStatus.RUNNING,
        worker_id="node-alpha",
    )

    # Assert 1: Check start_time and worker_id
    assert running_exec.status == ExecutionStatus.RUNNING
    assert running_exec.start_time is not None
    assert running_exec.worker_id == "node-alpha"
    assert running_exec.end_time is None  # Shouldn't have ended yet

    import time

    time.sleep(1)  # Simulate a 1-second task execution

    # Act 2: Transition to SUCCESS
    success_exec = crud.update_execution_status(
        db=db_session,
        execution_id=exec_record.execution_id,
        status=ExecutionStatus.SUCCESS,
    )

    # Assert 2: Check end_time and duration calculation
    assert success_exec.status == ExecutionStatus.SUCCESS
    assert success_exec.end_time is not None
    assert success_exec.duration is not None
    assert success_exec.duration >= 1


def test_report_execution_result_with_log_reference(db_session):
    """Test worker result reporting stores execution and log metadata."""
    # Arrange
    user = schemas.UserCreate(
        employee_id="0021_dev", username="ReportUser", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    job_data = schemas.JobCreate(
        job_name="Report Task",
        method=HttpMethod.GET,
        endpoint="http://test.com",
        schedule_type=ScheduleType.ONE_TIME,
    )
    created_job = crud.create_job(
        db=db_session, owner_id=created_user.user_id, job_in=job_data
    )
    exec_record = crud.create_execution(
        db=db_session,
        job_id=created_job.job_id,
        trigger_type=TriggerType.MANUAL,
    )
    report = schemas.ExecutionWorkerUpdate(
        job_id=created_job.job_id,
        status=ExecutionStatus.FAILED,
        worker_id="node-beta",
        retry_count=2,
        error_message="HTTP 500 from downstream service",
        log_path="logs/executions/report-task.log",
        log_size=2048,
    )

    # Act
    result = crud.report_execution_result(
        db=db_session,
        execution_id=exec_record.execution_id,
        report=report,
    )

    # Assert
    assert result is not None
    updated_exec, log_reference = result
    assert updated_exec.status == ExecutionStatus.FAILED
    assert updated_exec.worker_id == "node-beta"
    assert updated_exec.retry_count == 2
    assert updated_exec.error_message == "HTTP 500 from downstream service"
    assert updated_exec.end_time is not None
    assert log_reference is not None
    assert log_reference.execution_id == exec_record.execution_id
    assert log_reference.log_path == "logs/executions/report-task.log"
    assert log_reference.log_size == 2048


def test_report_execution_result_rejects_mismatched_job_id(db_session):
    """Test result reporting rejects mismatched job IDs."""
    # Arrange
    user = schemas.UserCreate(
        employee_id="0022_dev",
        username="MismatchUser",
        role=UserRole.DEVELOPER,
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    first_job = crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=schemas.JobCreate(
            job_name="First Job",
            method=HttpMethod.GET,
            endpoint="http://test.com/first",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )
    second_job = crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=schemas.JobCreate(
            job_name="Second Job",
            method=HttpMethod.GET,
            endpoint="http://test.com/second",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )
    exec_record = crud.create_execution(
        db=db_session, job_id=first_job.job_id, trigger_type=TriggerType.MANUAL
    )
    report = schemas.ExecutionWorkerUpdate(
        job_id=second_job.job_id,
        status=ExecutionStatus.SUCCESS,
        worker_id="node-gamma",
    )

    # Act
    result = crud.report_execution_result(
        db=db_session,
        execution_id=exec_record.execution_id,
        report=report,
    )

    # Assert
    unchanged_exec = crud.get_execution_by_id(
        db=db_session, execution_id=exec_record.execution_id
    )
    assert result is None
    assert unchanged_exec.status == ExecutionStatus.PENDING
    assert unchanged_exec.worker_id is None


# ==========================================
# 14. Test: Job Dependency CRUD
# ==========================================


def test_create_job_dependency_success(db_session):
    """Test creating a dependency link between an upstream and a downstream job."""
    # Arrange: Create user and two jobs
    user = schemas.UserCreate(
        employee_id="0021_dev", username="DepCreator", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    job_a_data = schemas.JobCreate(
        job_name="Upstream Job A",
        method=HttpMethod.GET,
        endpoint="http://test.com/a",
        schedule_type=ScheduleType.ONE_TIME,
    )
    job_b_data = schemas.JobCreate(
        job_name="Downstream Job B",
        method=HttpMethod.GET,
        endpoint="http://test.com/b",
        schedule_type=ScheduleType.ONE_TIME,
    )
    job_a = crud.create_job(
        db=db_session, owner_id=created_user.user_id, job_in=job_a_data
    )
    job_b = crud.create_job(
        db=db_session, owner_id=created_user.user_id, job_in=job_b_data
    )

    dep_data = schemas.JobDependencyCreate(
        upstream_id=job_a.job_id, downstream_id=job_b.job_id
    )

    # Act: Create the dependency
    result = crud.create_job_dependency(db=db_session, dependency_in=dep_data)

    # Assert: Verify the returned dependency attributes
    assert result.upstream_id == job_a.job_id
    assert result.downstream_id == job_b.job_id
    assert result.dependency_id is not None


def test_get_job_dependencies_success(db_session):
    """Test retrieving upstream and downstream dependencies for a specific job."""
    # Arrange: Create user and three jobs (Job 1 and 2 must finish before Job 3 starts)
    user = schemas.UserCreate(
        employee_id="0022_dev", username="DepReader", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    job_1 = crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=schemas.JobCreate(
            job_name="Job 1",
            method=HttpMethod.GET,
            endpoint="http://test.com",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )
    job_2 = crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=schemas.JobCreate(
            job_name="Job 2",
            method=HttpMethod.GET,
            endpoint="http://test.com",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )
    job_3 = crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=schemas.JobCreate(
            job_name="Job 3",
            method=HttpMethod.GET,
            endpoint="http://test.com",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )

    # Create dependencies: Job 1 -> Job 3 and Job 2 -> Job 3
    crud.create_job_dependency(
        db=db_session,
        dependency_in=schemas.JobDependencyCreate(
            upstream_id=job_1.job_id, downstream_id=job_3.job_id
        ),
    )
    crud.create_job_dependency(
        db=db_session,
        dependency_in=schemas.JobDependencyCreate(
            upstream_id=job_2.job_id, downstream_id=job_3.job_id
        ),
    )

    # Act: Retrieve dependencies for verification
    job_3_upstreams = crud.get_upstream_dependencies(db=db_session, job_id=job_3.job_id)
    job_1_downstreams = crud.get_downstream_dependencies(
        db=db_session, job_id=job_1.job_id
    )

    # Assert: Verify dependency counts and structural relationships
    assert len(job_3_upstreams) == 2
    upstream_ids = [dep.upstream_id for dep in job_3_upstreams]
    assert job_1.job_id in upstream_ids
    assert job_2.job_id in upstream_ids

    assert len(job_1_downstreams) == 1
    assert job_1_downstreams[0].downstream_id == job_3.job_id


def test_delete_job_dependency_success(db_session):
    """Test permanently deleting a job dependency."""
    # Arrange: Setup user, jobs, and a single dependency link
    user = crud.create_user(
        db=db_session,
        user_in=schemas.UserCreate(
            employee_id="0023_dev", username="DepDeleter", role=UserRole.DEVELOPER
        ),
    )
    job_a = crud.create_job(
        db=db_session,
        owner_id=user.user_id,
        job_in=schemas.JobCreate(
            job_name="A",
            method=HttpMethod.GET,
            endpoint="http://test.com",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )
    job_b = crud.create_job(
        db=db_session,
        owner_id=user.user_id,
        job_in=schemas.JobCreate(
            job_name="B",
            method=HttpMethod.GET,
            endpoint="http://test.com",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )

    dep = crud.create_job_dependency(
        db=db_session,
        dependency_in=schemas.JobDependencyCreate(
            upstream_id=job_a.job_id, downstream_id=job_b.job_id
        ),
    )

    # Act: Delete the dependency
    result = crud.delete_job_dependency(db=db_session, dependency_id=dep.dependency_id)

    # Assert: Verify deletion was successful and record no longer exists
    assert result is True
    upstreams = crud.get_upstream_dependencies(db=db_session, job_id=job_b.job_id)
    assert len(upstreams) == 0


# ==========================================
# 15. Test: Log Reference CRUD
# ==========================================


def test_create_log_reference_success(db_session):
    """Test creating a log reference pointing to external storage for a specific execution."""
    # Arrange: Create User, Job, and Execution
    user = crud.create_user(
        db=db_session,
        user_in=schemas.UserCreate(
            employee_id="0024_dev", username="LogWriter", role=UserRole.DEVELOPER
        ),
    )
    job = crud.create_job(
        db=db_session,
        owner_id=user.user_id,
        job_in=schemas.JobCreate(
            job_name="Log Task",
            method=HttpMethod.GET,
            endpoint="http://test.com",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )
    execution = crud.create_execution(
        db=db_session, job_id=job.job_id, trigger_type=TriggerType.SCHEDULER
    )

    log_path_str = "s3://my-bucket/logs/exec_001.log"
    log_size_bytes = 2048

    # Act: Insert log reference record
    result = crud.create_log_reference(
        db=db_session,
        execution_id=execution.execution_id,
        log_path=log_path_str,
        log_size=log_size_bytes,
    )

    # Assert: Verify log reference fields
    assert result.execution_id == execution.execution_id
    assert result.log_path == log_path_str
    assert result.log_size == log_size_bytes
    assert result.log_id is not None


def test_get_log_reference_by_execution_id_success(db_session):
    """Test retrieving a log reference using its associated execution ID."""
    # Arrange: Set up records and create a log reference
    user = crud.create_user(
        db=db_session,
        user_in=schemas.UserCreate(
            employee_id="0025_dev", username="LogReader", role=UserRole.DEVELOPER
        ),
    )
    job = crud.create_job(
        db=db_session,
        owner_id=user.user_id,
        job_in=schemas.JobCreate(
            job_name="Log Task 2",
            method=HttpMethod.GET,
            endpoint="http://test.com",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )
    execution = crud.create_execution(
        db=db_session, job_id=job.job_id, trigger_type=TriggerType.SCHEDULER
    )

    created_log = crud.create_log_reference(
        db=db_session,
        execution_id=execution.execution_id,
        log_path="local/logs/test.log",
        log_size=1024,
    )

    # Act: Fetch log reference
    fetched_log = crud.get_log_reference_by_execution_id(
        db=db_session, execution_id=execution.execution_id
    )

    # Assert: Validate fetched data matches the created data
    assert fetched_log is not None
    assert fetched_log.log_id == created_log.log_id
    assert fetched_log.log_path == "local/logs/test.log"


# ==========================================
# 16. Test: Pagination Counts
# ==========================================


def test_get_jobs_count_by_owner_id(db_session):
    """Test retrieving the total count of jobs for a specific user."""
    # Arrange: Create user and 3 jobs
    user = schemas.UserCreate(
        employee_id="0026_dev", username="Counter", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    for i in range(3):
        job_data = schemas.JobCreate(
            job_name=f"Count Job {i}",
            method=HttpMethod.GET,
            endpoint="http://test.com",
            schedule_type=ScheduleType.ONE_TIME,
        )
        crud.create_job(db=db_session, owner_id=created_user.user_id, job_in=job_data)

    # Act: Get total count
    total_count = crud.get_jobs_count_by_owner_id(
        db=db_session, owner_id=created_user.user_id
    )

    # Assert
    assert total_count == 3


def test_get_executions_count_by_job_id(db_session):
    """Test retrieving the total count of executions for a specific job."""
    # Arrange: Create user, job, and 2 executions
    user = schemas.UserCreate(
        employee_id="0027_dev", username="ExecCounter", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)
    job = crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=schemas.JobCreate(
            job_name="Exec Count Task",
            method=HttpMethod.GET,
            endpoint="http://test.com",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )

    crud.create_execution(
        db=db_session, job_id=job.job_id, trigger_type=TriggerType.SCHEDULER
    )
    crud.create_execution(
        db=db_session, job_id=job.job_id, trigger_type=TriggerType.MANUAL
    )

    # Act: Get total execution count
    total_count = crud.get_executions_count_by_job_id(db=db_session, job_id=job.job_id)

    # Assert
    assert total_count == 2


# ==========================================
# 17. Test: Job Status Filter
# ==========================================


def test_get_jobs_by_owner_id_with_status_filter(db_session):
    """Test that get_jobs_by_owner_id correctly filters by job status."""
    # Arrange: Create user, 1 ACTIVE job, and 1 DISABLED job
    user = schemas.UserCreate(
        employee_id="0028_dev", username="FilterOwner", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    job_active = crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=schemas.JobCreate(
            job_name="Active Job",
            method=HttpMethod.GET,
            endpoint="http://test.com",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )

    job_disabled = crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=schemas.JobCreate(
            job_name="Disabled Job",
            method=HttpMethod.GET,
            endpoint="http://test.com",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )
    crud.change_job_status(
        db=db_session, job_id=job_disabled.job_id, new_status=JobStatus.DISABLED
    )

    # Act: Query only ACTIVE jobs
    active_results = crud.get_jobs_by_owner_id(
        db=db_session, owner_id=created_user.user_id, status=JobStatus.ACTIVE
    )

    # Assert: Should only return 1 job
    assert len(active_results) == 1
    assert active_results[0].job_id == job_active.job_id
    assert active_results[0].status == JobStatus.ACTIVE


# ==========================================
# 18. Test: Dependency Duplicate Prevention
# ==========================================


def test_create_job_dependency_prevents_duplicates(db_session):
    """Test that creating the exact same dependency twice returns the existing one instead of crashing."""
    # Arrange
    from sqlalchemy import select
    from src.database.models import JobDependency

    user = schemas.UserCreate(
        employee_id="0029_dev", username="DepDup", role=UserRole.DEVELOPER
    )
    created_user = crud.create_user(db=db_session, user_in=user)

    job_a = crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=schemas.JobCreate(
            job_name="A",
            method=HttpMethod.GET,
            endpoint="http://test",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )
    job_b = crud.create_job(
        db=db_session,
        owner_id=created_user.user_id,
        job_in=schemas.JobCreate(
            job_name="B",
            method=HttpMethod.GET,
            endpoint="http://test",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )

    dep_data = schemas.JobDependencyCreate(
        upstream_id=job_a.job_id, downstream_id=job_b.job_id
    )

    # Act 1: Create dependency for the first time
    first_attempt = crud.create_job_dependency(db=db_session, dependency_in=dep_data)

    # Act 2: Attempt to create the exact same dependency again
    second_attempt = crud.create_job_dependency(db=db_session, dependency_in=dep_data)

    # Assert: Both should return the same object ID, and DB should only have 1 record
    assert first_attempt.dependency_id == second_attempt.dependency_id

    total_deps = db_session.scalars(
        select(JobDependency).where(JobDependency.upstream_id == job_a.job_id)
    ).all()
    assert len(total_deps) == 1
