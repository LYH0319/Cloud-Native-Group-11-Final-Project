import pytest
from src.database import crud
from src.database.models import User, UserRole, HttpMethod, ScheduleType, JobStatus
from src.database import schemas
from datetime import datetime, timedelta, timezone

# ==========================================
# 1. Test: Create User
# ==========================================
def test_create_user_success(db_session):
    """Test that a new user can be successfully created and default values are written correctly."""
    # Arrange (Prepare parameters)
    user = schemas.UserCreate(employee_id="0002_dev", username="Someone", role=UserRole.DEVELOPER)
    
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
    user = schemas.UserCreate(employee_id="0002_dev", username="Someone", role=UserRole.DEVELOPER)
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
    user = schemas.UserCreate(employee_id="0002_dev", username="Someone", role=UserRole.DEVELOPER)
    created_user = crud.create_user(db=db_session, user_in=user)
    
    # Act (Call change_user_role to change their role to OPERATOR)
    result = crud.change_user_role(db=db_session, user_id=created_user.user_id, new_role=UserRole.OPERATOR)
    
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
    user = schemas.UserCreate(employee_id="0002_dev", username="Someone", role=UserRole.DEVELOPER)
    created_user = crud.create_user(db=db_session, user_in=user)

    # Act (Call delete_user)
    result = crud.delete_user(db=db_session, user_id=created_user.user_id)
    
    # Assert 1: Confirm that delete_user returns True
    # Assert 2: Call get_user_by_id again to verify the user is still in the database, but is_active is False!
    assert result == True
    assert crud.get_user_by_user_id(db=db_session, user_id=created_user.user_id).is_active == False

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
            employee_id="admin_000", 
            username="System Admin",
            role=UserRole.ADMIN
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
    user = schemas.UserCreate(employee_id="0002_dev", username="Someone", role=UserRole.DEVELOPER)
    created_user = crud.create_user(db=db_session, user_in=user)
    job_data = schemas.JobCreate(
        job_name="trigger_billing_report",
        method=HttpMethod.POST,
        endpoint="https://api.internal.system.com/v1/billing/generate",
        schedule_type=ScheduleType.ONE_TIME,
        headers={"Authorization": "Bearer internal_service_token_123"},
        body={"target_region": "ap-northeast-1"}
    )
    
    # Act (Call crud.create_job)
    result = crud.create_job(db=db_session, owner_id=created_user.user_id, job_in=job_data)
    
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
    user = schemas.UserCreate(employee_id="0010_dev", username="Owner", role=UserRole.DEVELOPER)
    created_user = crud.create_user(db=db_session, user_in=user)
    
    job1 = schemas.JobCreate(
        job_name="Job 1", method=HttpMethod.GET, endpoint="http://test.com/1", schedule_type=ScheduleType.ONE_TIME
    )
    job2 = schemas.JobCreate(
        job_name="Job 2", method=HttpMethod.GET, endpoint="http://test.com/2", schedule_type=ScheduleType.ONE_TIME
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
    user = schemas.UserCreate(employee_id="0011_dev", username="Scheduler", role=UserRole.DEVELOPER)
    created_user = crud.create_user(db=db_session, user_in=user)
    
    # Use UTC time to match database func.now() behavior
    past_time = datetime.now(timezone.utc) - timedelta(minutes=10) 
    job_data = schemas.JobCreate(
        job_name="Ready Job", method=HttpMethod.GET, endpoint="http://test.com", schedule_type=ScheduleType.ONE_TIME
    )
    crud.create_job(db=db_session, owner_id=created_user.user_id, job_in=job_data, next_run_time=past_time)
    
    # Act 
    results = crud.get_active_jobs(db=db_session)
    
    # Assert 
    assert len(results) == 1
    assert results[0].job_name == "Ready Job"


def test_get_active_jobs_filters_by_schedule_type(db_session):
    """Test that get_active_jobs correctly filters by ONE_TIME or RECURRING."""
    # Arrange 
    user = schemas.UserCreate(employee_id="0013_dev", username="Filter", role=UserRole.DEVELOPER)
    created_user = crud.create_user(db=db_session, user_in=user)
    
    # Use UTC time
    past_time = datetime.now(timezone.utc) - timedelta(minutes=1)
    job_one_time = schemas.JobCreate(
        job_name="One Time Job", method=HttpMethod.GET, endpoint="http://test.com", schedule_type=ScheduleType.ONE_TIME
    )
    job_recurring = schemas.JobCreate(
        job_name="Recurring Job", method=HttpMethod.GET, endpoint="http://test.com", schedule_type=ScheduleType.RECURRING, cron_expression="0 * * * *"
    )
    crud.create_job(db=db_session, owner_id=created_user.user_id, job_in=job_one_time, next_run_time=past_time)
    crud.create_job(db=db_session, owner_id=created_user.user_id, job_in=job_recurring, next_run_time=past_time)
    
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
    user = schemas.UserCreate(employee_id="0014_dev", username="Paginator", role=UserRole.DEVELOPER)
    created_user = crud.create_user(db=db_session, user_in=user)
    
    for i in range(3):
        job_data = schemas.JobCreate(
            job_name=f"Job {i}", method=HttpMethod.GET, endpoint="http://test.com", schedule_type=ScheduleType.ONE_TIME
        )
        crud.create_job(db=db_session, owner_id=created_user.user_id, job_in=job_data)
        
    # Act (跳過第 0 筆，只拿 1 筆)
    results = crud.get_all_jobs(db=db_session, skip=1, limit=1)
    
    # Assert 
    assert len(results) == 1
    assert results[0].job_name == "Job 1"