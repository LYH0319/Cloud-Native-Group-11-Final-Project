from src.database import crud
from src.database.models import User, UserRole, HttpMethod, ScheduleType, JobStatus
from src.database import schemas
from datetime import datetime, timedelta, timezone
from src.database.models import TriggerType, ExecutionStatus


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


def test_update_execution_lifecycle(db_session):
    """Test the smart update logic for state transitions and duration calculation."""
    # Arrange
    user = schemas.UserCreate(
        employee_id="0020_dev", username="LifecycleUser", role=UserRole.DEVELOPER
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
        db=db_session, job_id=created_job.job_id, trigger_type=TriggerType.MANUAL
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
    assert success_exec.duration >= 1  # Should be at least 1 second due to sleep


def test_report_execution_result_with_log_reference(db_session):
    """Test worker result reporting updates execution metadata and stores log reference."""
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
        db=db_session, job_id=created_job.job_id, trigger_type=TriggerType.MANUAL
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
    """Test result reporting rejects payloads whose job_id does not match execution.job_id."""
    # Arrange
    user = schemas.UserCreate(
        employee_id="0022_dev", username="MismatchUser", role=UserRole.DEVELOPER
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
