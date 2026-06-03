from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, JSON, Enum, func, ForeignKey
from typing import List, Optional, Dict, Any
from src.database.connection import Base
import enum
from datetime import datetime

# ==========================================
# ENUMS
# ==========================================


class UserRole(enum.Enum):
    """Defines the authorization levels for system users."""

    ADMIN = "Admin"
    DEVELOPER = "Developer"
    OPERATOR = "Operator"


class HttpMethod(enum.Enum):
    """Supported HTTP methods for job requests."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class JobStatus(enum.Enum):
    """Represents the current lifecycle state of a job."""

    ACTIVE = "Active"
    DISABLED = "Disabled"
    DELETED = "Deleted"


class ScheduleType(enum.Enum):
    """Determines whether a job runs exactly once or repeatedly based on a cron expression."""

    ONE_TIME = "One-time"
    RECURRING = "Recurring"


class TriggerType(enum.Enum):
    """Indicates how a specific job execution was initiated."""

    SCHEDULER = "Scheduler"
    MANUAL = "Manual"


class ExecutionStatus(enum.Enum):
    """Tracks the real-time status of a single job execution instance."""

    PENDING = "Pending"  # Waiting in queue
    RUNNING = "Running"  # Currently being processed by a worker
    SUCCESS = "Success"  # Completed without errors
    FAILED = "Failed"  # Encountered an error during execution
    TIMEOUT = "Timeout"  # Exceeded maximum allowed execution time
    CANCELLED = "Cancelled"  # Manually aborted before or during execution


# ==========================================
# MODELS
# ==========================================


class User(Base):
    """
    Represents a user in the system.

    Attributes:
        user_id (int): Internal primary key.
        employee_id (str): Unique identifier for the employee (used for login/reference).
        username (str): Display name of the user.
        role (UserRole): Authorization level of the user.
        created_at (datetime): Timestamp when the account was created.
        updated_at (datetime): Timestamp when the account was last modified.
        is_active (bool): Flag indicating if the account is currently active (used for soft deletes).
    """

    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, init=False
    )
    employee_id: Mapped[str] = mapped_column(String(20), unique=True)
    username: Mapped[str] = mapped_column(String(30))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.DEVELOPER)
    email: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True, default=None
    )
    hashed_password: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), init=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), init=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    jobs: Mapped[List["Job"]] = relationship(back_populates="owner", init=False)

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, username='{self.username!r}', role='{self.role.name!r}')>"


class Job(Base):
    """
    Represents an HTTP request task configured by a user.

    Attributes:
        job_id (int): Internal primary key.
        owner_id (int): Foreign key referencing the user who created the job.
        job_name (str): Human-readable name for the job.
        method (HttpMethod): The HTTP method to use for the request.
        endpoint (str): The target URL for the request.
        headers (dict, optional): JSON-serialized HTTP headers.
        body (dict, optional): JSON-serialized HTTP request body payload.
        status (JobStatus): Current status of the job (e.g., ACTIVE, DISABLED).
        has_dependency (bool): Flag indicating if this job waits for upstream jobs to finish.
        schedule_type (ScheduleType): Whether the job runs once or on a recurring schedule.
        cron_expression (str, optional): The cron schedule string (required if RECURRING).
        next_run_time (datetime, optional): The calculated next execution timestamp.
    """

    __tablename__ = "jobs"

    # === 1. init=False 區 (不影響排序) ===
    job_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, init=False
    )

    # === 2. 必填區 (不能有 default) ===
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    job_name: Mapped[str] = mapped_column(String(30))
    method: Mapped[HttpMethod] = mapped_column(Enum(HttpMethod))
    endpoint: Mapped[str] = mapped_column(String(2048))
    schedule_type: Mapped[ScheduleType] = mapped_column(
        Enum(ScheduleType)
    )  # ✨ 把它搬到這裡！

    # === 3. 選填區 (有 default 的必須放在必填區下面) ===
    headers: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=None
    )
    body: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=None
    )
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.ACTIVE)
    has_dependency: Mapped[bool] = mapped_column(Boolean, default=False)
    cron_expression: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, default=None
    )
    next_run_time: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, default=None
    )

    # === 4. init=False 區 (不影響排序) ===
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), init=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), init=False
    )

    owner: Mapped["User"] = relationship(back_populates="jobs", init=False)

    upstream_dependencies: Mapped[List["JobDependency"]] = relationship(
        foreign_keys="[JobDependency.downstream_id]",
        back_populates="downstream_job",
        cascade="all, delete-orphan",
        init=False,
    )

    downstream_dependencies: Mapped[List["JobDependency"]] = relationship(
        foreign_keys="[JobDependency.upstream_id]",
        back_populates="upstream_job",
        cascade="all, delete-orphan",
        init=False,
    )

    executions: Mapped[List["Execution"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", init=False
    )

    def __repr__(self) -> str:
        return (
            f"<Job(job_id={self.job_id}, owner_id={self.owner_id}, "
            f"name='{self.job_name!r}', status='{self.status.name!r}')>"
        )


class JobDependency(Base):
    """
    Represents a directed edge in the job dependency graph (DAG).
    Defines execution order where the upstream job must succeed before the downstream job starts.

    Attributes:
        dependency_id (int): Internal primary key.
        upstream_id (int): Foreign key of the job that must finish first.
        downstream_id (int): Foreign key of the job waiting for the upstream job.
    """

    __tablename__ = "job_dependencies"

    dependency_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, init=False
    )
    upstream_id: Mapped[int] = mapped_column(ForeignKey("jobs.job_id"))
    downstream_id: Mapped[int] = mapped_column(ForeignKey("jobs.job_id"))

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), init=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), init=False
    )

    upstream_job: Mapped["Job"] = relationship(
        foreign_keys=[upstream_id], back_populates="downstream_dependencies", init=False
    )
    downstream_job: Mapped["Job"] = relationship(
        foreign_keys=[downstream_id], back_populates="upstream_dependencies", init=False
    )

    def __repr__(self) -> str:
        return f"<Dependency(upstream={self.upstream_id} -> downstream={self.downstream_id})>"


class Execution(Base):
    """
    Represents a single execution instance (attempt) of a specific job.

    Attributes:
        execution_id (int): Internal primary key.
        job_id (int): Foreign key referencing the parent job.
        trigger_type (TriggerType): How this execution was triggered (e.g., automatically or manually).
        status (ExecutionStatus): Current status of this specific execution.
        start_time (datetime, optional): Timestamp when the worker started processing.
        end_time (datetime, optional): Timestamp when the execution finished (success or failure).
        duration (int, optional): Execution duration in seconds.
        worker_id (str, optional): Identifier of the distributed worker node that processed this execution.
        retry_count (int): Number of times this execution has been retried.
        error_message (str, optional): Detailed error message if the execution failed.
    """

    __tablename__ = "executions"

    execution_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, init=False
    )
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.job_id"))

    trigger_type: Mapped[TriggerType] = mapped_column(
        Enum(TriggerType), default=TriggerType.SCHEDULER
    )
    status: Mapped[ExecutionStatus] = mapped_column(
        Enum(ExecutionStatus), default=ExecutionStatus.PENDING
    )

    start_time: Mapped[Optional[datetime]] = mapped_column(nullable=True, default=None)
    end_time: Mapped[Optional[datetime]] = mapped_column(nullable=True, default=None)
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(
        nullable=True, default=None
    )
    duration: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=None
    )

    worker_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, default=None
    )
    retry_count: Mapped[int] = mapped_column(Integer, default=0)

    error_message: Mapped[Optional[str]] = mapped_column(
        String(4000), nullable=True, default=None
    )

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), init=False)

    job: Mapped["Job"] = relationship(back_populates="executions", init=False)
    log_reference: Mapped[Optional["LogReference"]] = relationship(
        back_populates="execution", cascade="all, delete-orphan", init=False
    )

    def __repr__(self) -> str:
        return (
            f"<Execution(id={self.execution_id}, job_id={self.job_id}, "
            f"status='{self.status.name}', retry={self.retry_count})>"
        )


class LogReference(Base):
    """
    Stores metadata pointing to external log files associated with a specific execution.

    Attributes:
        log_id (int): Internal primary key.
        execution_id (int): Foreign key referencing the associated execution.
        log_path (str): File path or URI where the actual log content is stored.
        log_size (int): Size of the log file in bytes.
    """

    __tablename__ = "log_references"

    log_id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, init=False
    )
    execution_id: Mapped[int] = mapped_column(ForeignKey("executions.execution_id"))

    log_path: Mapped[str] = mapped_column(String(1024))
    log_size: Mapped[int] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), init=False)

    execution: Mapped["Execution"] = relationship(
        back_populates="log_reference", init=False
    )
