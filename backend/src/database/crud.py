from sqlalchemy.orm import Session
from sqlalchemy import asc, desc, select, func
from src.database.models import (
    User,
    UserRole,
    JobStatus,
    ScheduleType,
    Job,
    Execution,
    ExecutionStatus,
    TriggerType,
    JobDependency,
    LogReference,
    JobStatus
)
from datetime import datetime, timezone, timedelta
from src.database import schemas
from src.utils.logger import validate_log_path, validate_log_size
from src.utils.security import hash_password, verify_password

# ==========================================
#                  USER CRUD
# ==========================================


def create_user(db: Session, user_in: schemas.UserCreate) -> User:
    """
    Creates a new user in the database.

    Args:
        db (Session): The database session.
        user_in (schemas.UserCreate): The validated user data containing employee_id, username, and role.

    Returns:
        User: The newly created user object.
    """
    new_user = User(
        employee_id=user_in.employee_id,
        username=user_in.username,
        role=user_in.role,
        email=user_in.email,
        hashed_password=hash_password(user_in.password) if user_in.password else None,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_user_by_user_id(db: Session, user_id: int) -> User | None:
    """
    Retrieves a user by their unique internal user ID.

    Args:
        db (Session): The database session.
        user_id (int): The specific user_id to search for.

    Returns:
        User | None: The user object if found, otherwise None.
    """
    return db.scalar(select(User).where(User.user_id == user_id))


def get_user_by_employee_id(db: Session, employee_id: str) -> User | None:
    """
    Retrieves a user by their unique employee ID.

    Args:
        db (Session): The database session.
        employee_id (str): The specific employee ID to search for.

    Returns:
        User | None: The user object if found, otherwise None.
    """
    return db.scalar(select(User).where(User.employee_id == employee_id))


def get_user_by_email(db: Session, email: str) -> User | None:
    """Retrieves a user by email."""
    return db.scalar(select(User).where(User.email == email))


def get_user_by_username(db: Session, username: str) -> User | None:
    """Retrieves a user by username."""
    return db.scalar(select(User).where(User.username == username))


def authenticate_user(
    db: Session,
    identifier: str,
    password: str,
) -> User | None:
    """Authenticate by email, username, or employee_id."""
    user = (
        get_user_by_email(db=db, email=identifier)
        or get_user_by_username(db=db, username=identifier)
        or get_user_by_employee_id(db=db, employee_id=identifier)
    )
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    """
    Retrieves a list of all active users with pagination.

    Note:
        This query filters out inactive users (soft-deleted accounts).

    Args:
        db (Session): The database session.
        skip (int, optional): The number of records to skip. Defaults to 0.
        limit (int, optional): The maximum number of records to return. Defaults to 100.

    Returns:
        list[User]: A list of active user objects.
    """
    return list(
        db.scalars(select(User).where(User.is_active).offset(skip).limit(limit)).all()
    )


def change_user_role(db: Session, user_id: int, new_role: UserRole) -> User | None:
    """
    Updates the authorization role of a specific user.

    Args:
        db (Session): The database session.
        user_id (int): The internal primary key of the user to update.
        new_role (UserRole): The new role to assign to the user.

    Returns:
        User | None: The updated user object, or None if the user does not exist.
    """
    user = db.scalar(select(User).where(User.user_id == user_id))

    if not user:
        return None

    user.role = new_role
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    """
    Performs a soft delete on a user account.

    Note:
        This function does not permanently remove the record from the database.
        Instead, it sets the 'is_active' flag to False.

    Args:
        db (Session): The database session.
        user_id (int): The internal primary key of the user to delete.

    Returns:
        bool: True if the user was successfully soft-deleted, False if the user was not found.
    """
    user = db.scalar(select(User).where(User.user_id == user_id))

    if not user or not user.is_active:
        return False

    user.is_active = False
    db.commit()
    return True


# ==========================================
#                  JOB CRUD
# ==========================================


def create_job(
    db: Session,
    owner_id: int,
    job_in: schemas.JobCreate,
    next_run_time: datetime | None = None,
) -> Job:
    """
    Creates a new HTTP request job in the database.

    Args:
        db (Session): The database session.
        owner_id (int): The internal user ID of the job's owner.
        job_in (schemas.JobCreate): The validated job data containing
            job_name, method, endpoint, schedule_type,
            and optional fields like headers, body, and cron_expression.
        next_run_time (datetime | None, optional): The calculated next execution timestamp. Defaults to None.

    Note:
        The job 'status' is automatically set to ACTIVE by the database model.

    Returns:
        Job: The newly created job object.
    """
    depends_on = getattr(job_in, "depends_on", None) or []

    new_job = Job(
        owner_id=owner_id,
        job_name=job_in.job_name,
        method=job_in.method,
        endpoint=job_in.endpoint,
        headers=job_in.headers,
        body=job_in.body,
        has_dependency=bool(depends_on),
        schedule_type=job_in.schedule_type,
        cron_expression=job_in.cron_expression,
        next_run_time=next_run_time,
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job


def get_job_by_id(db: Session, job_id: int) -> Job | None:
    """
    Retrieves a specific job by its internal ID.

    Args:
        db (Session): The database session.
        job_id (int): The primary key of the job.

    Returns:
        Job | None: The job object if found, otherwise None.
    """
    return db.scalar(select(Job).where(Job.job_id == job_id))


def get_jobs_by_owner_id(
    db: Session,
    owner_id: int,
    status: JobStatus | None = None,  # Added optional filter
    skip: int = 0,
    limit: int = 100,
) -> list[Job]:
    """
    Retrieves a list of jobs owned by a specific user with pagination and optional status filtering.

    Note:
        This function returns all jobs belonging to the user, regardless of their status
        (including ACTIVE, DISABLED, and DELETED). The frontend can filter them if needed.

    Args:
        db (Session): The database session.
        owner_id (int): The internal user ID of the job's owner.
        skip (int, optional): The number of records to skip. Defaults to 0.
        limit (int, optional): The maximum number of records to return. Defaults to 100.

    Returns:
        list[Job]: A list of job objects owned by the specified user.
    """
    conditions = [Job.owner_id == owner_id]
    if status:
        conditions.append(Job.status == status)

    return list(
        db.scalars(select(Job).where(*conditions).offset(skip).limit(limit)).all()
    )


def get_active_jobs(
    db: Session,
    schedule_type: ScheduleType | None = None,
    target_time: datetime | None = None,
    skip: int = 0,
    limit: int = 100,
    for_update: bool = False,
) -> list[Job]:
    """
    Retrieves a batch of ACTIVE jobs that are ready to be executed.

    Args:
        db (Session): The database session.
        schedule_type (ScheduleType | None, optional): Filter by ONE_TIME or RECURRING. Defaults to None.
        target_time (datetime | None, optional): The evaluation time. If None, uses the current database time.
            Defaults to None.
        skip (int, optional): The number of records to skip. Defaults to 0.
        limit (int, optional): The maximum number of records to return. Defaults to 100.
        for_update (bool, optional): If True, locks the selected rows for execution (skip_locked=True).
            Should ONLY be True when called by the background scheduler. Defaults to False.

    Returns:
        list[Job]: A list of job objects ready for execution.
    """

    check_time = target_time if target_time else func.now()

    conditions = [
        Job.status == JobStatus.ACTIVE,
        Job.next_run_time <= check_time,
    ]
    if schedule_type:
        conditions.append(Job.schedule_type == schedule_type)

    stm = select(Job).where(*conditions).offset(skip).limit(limit)

    if for_update:
        stm = stm.with_for_update(skip_locked=True)

    return list(db.scalars(stm).all())


def get_all_jobs(db: Session, skip: int = 0, limit: int = 100) -> list[Job]:
    """
    Retrieves a list of all jobs in the system with pagination.

    Note:
        This is typically used by System Administrators for dashboard monitoring.

    Args:
        db (Session): The database session.
        skip (int, optional): The number of records to skip. Defaults to 0.
        limit (int, optional): The maximum number of records to return. Defaults to 100.

    Returns:
        list[Job]: A list of all job objects.
    """
    return list(db.scalars(select(Job).offset(skip).limit(limit)).all())


def get_jobs_count_by_owner_id(db: Session, owner_id: int) -> int:
    """
    Counts the total number of jobs owned by a specific user.
    Useful for frontend pagination components.

    Args:
        db (Session): The database session.
        owner_id (int): The internal user ID.

    Returns:
        int: The total count of jobs.
    """
    return (
        db.scalar(select(func.count(Job.job_id)).where(Job.owner_id == owner_id)) or 0
    )


def update_job(db: Session, job_id: int, job_in: schemas.JobUpdate) -> Job | None:
    """
    Updates an existing job's configuration.

    Args:
        db (Session): The database session.
        job_id (int): The internal primary key of the job to update.
        job_in (schemas.JobUpdate): The validated data containing the optional fields to update.

    Returns:
        Job | None: The updated job object, or None if the job does not exist.
    """
    job = db.scalar(select(Job).where(Job.job_id == job_id))

    if not job:
        return None

    update_data = job_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)

    return job


def change_job_status(db: Session, job_id: int, new_status: JobStatus) -> Job | None:
    """
    Changes the active state of a job (e.g., pausing or resuming).

    Note:
        This is a lightweight update specifically for toggling a job between
        ACTIVE and DISABLED states without requiring a full JobUpdate schema.

    Args:
        db (Session): The database session.
        job_id (int): The internal primary key of the job.
        new_status (JobStatus): The new status to apply.

    Returns:
        Job | None: The updated job object, or None if the job does not exist.
    """
    job = db.scalar(select(Job).where(Job.job_id == job_id))

    if not job:
        return None

    job.status = new_status
    db.commit()
    db.refresh(job)
    return job


def delete_job(db: Session, job_id: int) -> bool:
    """
    Performs a soft delete on a specific job.

    Note:
        This updates the job's status to JobStatus.DELETED.
        It does not permanently remove the record from the database
        in order to preserve execution history and log references.

    Args:
        db (Session): The database session.
        job_id (int): The internal primary key of the job to delete.

    Returns:
        bool: True if the job was successfully soft-deleted, False if the job was not found.
    """
    job = db.scalar(select(Job).where(Job.job_id == job_id))

    if not job or job.status == JobStatus.DELETED:
        return False

    job.status = JobStatus.DELETED
    db.commit()
    return True


def hard_delete_job(db: Session, job_id: int) -> bool:
    """
    Permanently removes a job and its cascaded data from the database.

    Args:
        db (Session): The database session.
        job_id (int): The internal primary key of the job.

    Returns:
        bool: True if the job was successfully deleted, False if not found.
    """
    job = db.scalar(select(Job).where(Job.job_id == job_id))

    if not job:
        return False

    db.delete(job)
    db.commit()
    return True


def purge_old_deleted_jobs(db: Session, retention_days: int = 30) -> int:
    """
    Permanently removes jobs that have been marked as DELETED for longer than the retention period.

    Args:
        db (Session): The database session.
        retention_days (int, optional): The number of days to retain soft-deleted jobs. Defaults to 30.

    Returns:
        int: The number of jobs permanently deleted.
    """
    threshold_time = datetime.now(timezone.utc) - timedelta(days=retention_days)

    # Find all jobs that are DELETED and were updated before the threshold time
    jobs_to_delete = db.scalars(
        select(Job).where(
            Job.status == JobStatus.DELETED, Job.updated_at <= threshold_time
        )
    ).all()

    deleted_count = len(jobs_to_delete)

    for job in jobs_to_delete:
        db.delete(job)

    db.commit()
    return deleted_count


# ==========================================
#               EXECUTION CRUD
# ==========================================


def create_execution(db: Session, job_id: int, trigger_type: TriggerType) -> Execution:
    """
    Creates a new execution record for a specific job.

    Note:
        The execution status defaults to PENDING. This is typically called
        when the scheduler or a user manually triggers a job.

    Args:
        db (Session): The database session.
        job_id (int): The internal primary key of the job being executed.
        trigger_type (TriggerType): It was triggered by SCHEDULER or MANUAL.

    Returns:
        Execution: The newly created execution object.
    """
    new_exec = Execution(job_id=job_id, trigger_type=trigger_type)
    db.add(new_exec)
    db.commit()
    db.refresh(new_exec)
    return new_exec


def get_execution_by_id(db: Session, execution_id: int) -> Execution | None:
    """
    Retrieves a specific execution record by its internal ID.

    Args:
        db (Session): The database session.
        execution_id (int): The primary key of the execution.

    Returns:
        Execution | None: The execution object if found, otherwise None.
    """
    return db.scalar(select(Execution).where(Execution.execution_id == execution_id))


def get_executions_by_job_id(
    db: Session, job_id: int, skip: int = 0, limit: int = 100
) -> list[Execution]:
    """
    Retrieves the execution history for a specific job with pagination.

    Args:
        db (Session): The database session.
        job_id (int): The primary key of the job.
        skip (int, optional): The number of records to skip. Defaults to 0.
        limit (int, optional): The maximum number of records to return. Defaults to 100.

    Returns:
        list[Execution]: A list of execution objects associated with the job (ordered chronologically).
    """
    stm = (
        select(Execution)
        .where(Execution.job_id == job_id)
        .order_by(Execution.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stm).all())


def get_execution_history(
    db: Session,
    job_id: int,
    status: ExecutionStatus | None = None,
    trigger_type: TriggerType | None = None,
    worker_id: str | None = None,
    start_time_from: datetime | None = None,
    start_time_to: datetime | None = None,
    skip: int = 0,
    limit: int = 100,
    order_by: str = "created_at",
    order_direction: str = "desc",
) -> list[Execution]:
    """
    Retrieves execution history for a job with filters, pagination, and sorting.

    The query is scoped to one job and defaults to newest executions first.
    """
    order_columns = {
        "created_at": Execution.created_at,
        "start_time": Execution.start_time,
        "end_time": Execution.end_time,
        "duration": Execution.duration,
        "execution_id": Execution.execution_id,
    }
    order_column = order_columns.get(order_by, Execution.created_at)
    direction = desc if order_direction == "desc" else asc
    limited = min(limit, 100)

    conditions = [Execution.job_id == job_id]
    if status is not None:
        conditions.append(Execution.status == status)
    if trigger_type is not None:
        conditions.append(Execution.trigger_type == trigger_type)
    if worker_id is not None:
        conditions.append(Execution.worker_id == worker_id)
    if start_time_from is not None:
        conditions.append(Execution.start_time >= start_time_from)
    if start_time_to is not None:
        conditions.append(Execution.start_time <= start_time_to)

    stm = (
        select(Execution)
        .where(*conditions)
        .order_by(direction(order_column))
        .offset(skip)
        .limit(limited)
    )
    return list(db.scalars(stm).all())


def get_executions_count_by_job_id(db: Session, job_id: int) -> int:
    """
    Counts the total number of execution records for a specific job.

    Args:
        db (Session): The database session.
        job_id (int): The internal job ID.

    Returns:
        int: The total count of executions.
    """
    return (
        db.scalar(
            select(func.count(Execution.execution_id)).where(Execution.job_id == job_id)
        )
        or 0
    )


def update_execution_status(
    db: Session,
    execution_id: int,
    status: ExecutionStatus,
    worker_id: str | None = None,
    error_message: str | None = None,
) -> Execution | None:
    """
    Updates the lifecycle status of a specific execution.

    Note:
        This is a "smart" update function that handles business logic:
        - If status is RUNNING: Records the start_time and assigns the worker_id.
        - If status is SUCCESS / FAILED / TIMEOUT / CANCELLED: Records the end_time,
          calculates the duration, and saves any error messages.

    Args:
        db (Session): The database session.
        execution_id (int): The internal primary key of the execution.
        status (ExecutionStatus): The new status of the execution.
        worker_id (str | None, optional): The ID of the worker node processing the job. Defaults to None.
        error_message (str | None, optional): Detailed error message if the execution failed. Defaults to None.

    Returns:
        Execution | None: The updated execution object, or None if not found.
    """
    exec_record = db.scalar(
        select(Execution).where(Execution.execution_id == execution_id)
    )

    if not exec_record:
        return None

    now_utc = datetime.now(timezone.utc)
    exec_record.status = status

    if status == ExecutionStatus.RUNNING:
        exec_record.start_time = now_utc
        if worker_id:
            exec_record.worker_id = worker_id

    elif status in [
        ExecutionStatus.SUCCESS,
        ExecutionStatus.FAILED,
        ExecutionStatus.TIMEOUT,
        ExecutionStatus.CANCELLED,
    ]:
        exec_record.end_time = now_utc
        if error_message:
            exec_record.error_message = error_message

        if exec_record.start_time:
            start_time_utc = (
                exec_record.start_time.replace(tzinfo=timezone.utc)
                if exec_record.start_time.tzinfo is None
                else exec_record.start_time
            )
            duration_td = now_utc - start_time_utc
            exec_record.duration = int(duration_td.total_seconds())

    db.commit()
    db.refresh(exec_record)
    return exec_record


def report_execution_result(  # noqa: C901
    db: Session,
    execution_id: int,
    report: schemas.ExecutionWorkerUpdate,
) -> tuple[Execution, LogReference | None] | None:
    """
    Stores the structured result reported by a worker.

    Large logs should remain in external storage; this function only stores
    their path and size as a LogReference record.
    """
    exec_record = db.scalar(
        select(Execution).where(Execution.execution_id == execution_id)
    )

    if not exec_record:
        return None

    if report.job_id is not None and report.job_id != exec_record.job_id:
        return None

    now_utc = datetime.now(timezone.utc)
    exec_record.status = report.status
    exec_record.worker_id = report.worker_id
    exec_record.error_message = report.error_message

    if report.retry_count is not None:
        exec_record.retry_count = report.retry_count

    if report.start_time is not None:
        exec_record.start_time = report.start_time
    elif report.status == ExecutionStatus.RUNNING and exec_record.start_time is None:
        exec_record.start_time = now_utc

    if report.end_time is not None:
        exec_record.end_time = report.end_time
    elif report.status in [
        ExecutionStatus.SUCCESS,
        ExecutionStatus.FAILED,
        ExecutionStatus.TIMEOUT,
        ExecutionStatus.CANCELLED,
    ]:
        exec_record.end_time = now_utc

    if report.duration is not None:
        exec_record.duration = report.duration
    elif exec_record.start_time and exec_record.end_time:
        start_time_utc = (
            exec_record.start_time.replace(tzinfo=timezone.utc)
            if exec_record.start_time.tzinfo is None
            else exec_record.start_time
        )
        end_time_utc = (
            exec_record.end_time.replace(tzinfo=timezone.utc)
            if exec_record.end_time.tzinfo is None
            else exec_record.end_time
        )
        exec_record.duration = int((end_time_utc - start_time_utc).total_seconds())

    log_reference = None
    if report.log_path is not None:
        validate_log_path(report.log_path)
        validate_log_size(report.log_size)
        log_reference = db.scalar(
            select(LogReference).where(LogReference.execution_id == execution_id)
        )
        if log_reference is None:
            log_reference = LogReference(
                execution_id=execution_id,
                log_path=report.log_path,
                log_size=report.log_size or 0,
            )
            db.add(log_reference)
        else:
            log_reference.log_path = report.log_path
            if report.log_size is not None:
                log_reference.log_size = report.log_size

    db.commit()
    db.refresh(exec_record)
    if log_reference is not None:
        db.refresh(log_reference)

    return exec_record, log_reference


# ==========================================
#        JOB DEPENDENCY CRUD
# ==========================================


def create_job_dependency(
    db: Session, dependency_in: schemas.JobDependencyCreate
) -> JobDependency:
    """
    Creates a new execution dependency between two jobs.
    Prevents duplicate dependency links.

    Args:
        db (Session): The database session.
        dependency_in (schemas.JobDependencyCreate): The validated data containing upstream_id and downstream_id.

    Returns:
        JobDependency: The newly created dependency object.
    """
    existing = db.scalar(
        select(JobDependency).where(
            JobDependency.upstream_id == dependency_in.upstream_id,
            JobDependency.downstream_id == dependency_in.downstream_id,
        )
    )

    if existing:
        return existing

    new_dependency = JobDependency(
        upstream_id=dependency_in.upstream_id, downstream_id=dependency_in.downstream_id
    )
    db.add(new_dependency)
    db.commit()
    db.refresh(new_dependency)
    return new_dependency


def get_upstream_dependencies(db: Session, job_id: int) -> list[JobDependency]:
    """
    Retrieves all jobs that the specified job is waiting for.
    (Finds records where downstream_id == job_id)

    Args:
        db (Session): The database session.
        job_id (int): The primary key of the downstream job.

    Returns:
        list[JobDependency]: A list of dependencies where the specified job is the downstream target.
    """
    return list(
        db.scalars(
            select(JobDependency).where(JobDependency.downstream_id == job_id)
        ).all()
    )


def get_downstream_dependencies(db: Session, job_id: int) -> list[JobDependency]:
    """
    Retrieves all jobs that are waiting for the specified job to finish.
    (Finds records where upstream_id == job_id)

    Args:
        db (Session): The database session.
        job_id (int): The primary key of the upstream job.

    Returns:
        list[JobDependency]: A list of dependencies where the specified job is the upstream source.
    """
    return list(
        db.scalars(
            select(JobDependency).where(JobDependency.upstream_id == job_id)
        ).all()
    )


def delete_job_dependency(db: Session, dependency_id: int) -> bool:
    """
    Permanently removes a dependency link between two jobs.

    Args:
        db (Session): The database session.
        dependency_id (int): The primary key of the dependency record.

    Returns:
        bool: True if deleted successfully, False if not found.
    """
    depend = db.scalar(
        select(JobDependency).where(JobDependency.dependency_id == dependency_id)
    )

    if not depend:
        return False

    db.delete(depend)
    db.commit()
    return True


# ==========================================
#           LOG REFERENCE CRUD
# ==========================================


def create_log_reference(
    db: Session, execution_id: int, log_path: str, log_size: int
) -> LogReference:
    """
    Creates a new log reference pointing to external storage (e.g., S3 or local disk).

    Args:
        db (Session): The database session.
        execution_id (int): The primary key of the associated execution.
        log_path (str): The storage URI or file path of the log.
        log_size (int): The size of the log file in bytes.

    Returns:
        LogReference: The newly created log reference object.
    """
    log_ref = LogReference(
        execution_id=execution_id, log_path=log_path, log_size=log_size
    )
    db.add(log_ref)
    db.commit()
    db.refresh(log_ref)
    return log_ref


def get_log_reference_by_execution_id(
    db: Session, execution_id: int
) -> LogReference | None:
    """
    Retrieves the log reference associated with a specific execution.

    Args:
        db (Session): The database session.
        execution_id (int): The primary key of the execution.

    Returns:
        LogReference | None: The log reference object if found, otherwise None.
    """
    return db.scalar(
        select(LogReference).where(LogReference.execution_id == execution_id)
    )


# 從jobs.py搬過來的
def get_active_dependency_graph(db: Session) -> dict[int, list[int]]:
    """從資料庫讀取目前的相依性關係，並打包成鄰接串列"""
    graph = {}
    # 透過 join 篩選，只有兩端任務都還活著 (ACTIVE) 的關聯才需要進圖進行死鎖判定
    stm = (
        select(JobDependency)
        .join(Job, JobDependency.downstream_id == Job.job_id)
        .where(Job.status == JobStatus.ACTIVE)
    )
    dependencies = db.scalars(stm).all()
    for dep in dependencies:
        if dep.downstream_id not in graph:
            graph[dep.downstream_id] = []
        graph[dep.downstream_id].append(dep.upstream_id)
    return graph

def create_job_dependencies(db: Session, downstream_id: int, upstream_ids: list[int]) -> None:
    """將多筆前置關聯批次安全寫入 job_dependencies 表"""
    for upstream_id in upstream_ids:
        dep_record = JobDependency(upstream_id=upstream_id, downstream_id=downstream_id)
        db.add(dep_record)
    db.commit()