from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from src.database.models import UserRole, HttpMethod, ScheduleType, JobStatus
from src.database.models import TriggerType, ExecutionStatus

# ==========================================
# 1. User Schemas
# ==========================================


class UserBase(BaseModel):
    """
    Base schema containing common attributes for a User.

    Attributes:
        employee_id (str): Unique employee identifier (Required).
        username (str): Display name of the user (Required).
        role (UserRole): Authorization role (Required).
    """

    employee_id: str = Field(
        ...,
        min_length=4,
        max_length=20,
        description="Unique employee identifier",
    )
    username: str = Field(
        ...,
        min_length=1,
        max_length=30,
        description="Display name of the user",
    )
    role: UserRole = Field(default=UserRole.DEVELOPER, description="Authorization role")
    email: Optional[str] = Field(default=None, max_length=255)


class UserCreate(UserBase):
    """
    Schema for creating a new User.
    Used by the API router to validate incoming POST request payloads.
    Inherits all required attributes from UserBase (employee_id, username, role).
    """

    password: Optional[str] = Field(default=None, min_length=6, max_length=128)


class UserResponse(UserBase):
    """
    Schema for serializing User data in API responses.
    Includes database-generated fields like IDs and timestamps.

    Attributes:
        user_id (int): Internal primary key.
        is_active (bool): Flag indicating if the account is currently active.
        created_at (datetime): Timestamp when the account was created.
        updated_at (datetime): Timestamp when the account was last modified.
    """

    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserRead(UserResponse):
    """Public user response. Never includes hashed_password."""

    pass


class UserLogin(BaseModel):
    """Minimal login payload; identifier may be email, username, or employee_id."""

    identifier: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserRead


# ==========================================
# 2. Job Schemas
# ==========================================


class JobBase(BaseModel):
    """
    Base schema containing common attributes for a scheduled Job.

    Attributes:
        job_name (str): Human-readable name for the job (Required).
        method (HttpMethod): The HTTP method to use (Required).
        endpoint (str): The target URL for the request (Required).
        schedule_type (ScheduleType): ONE_TIME or RECURRING (Required).
        has_dependency (bool, optional): Defaults to False.
        headers (Dict[str, Any] | None, optional): HTTP headers. Defaults to None.
        body (Dict[str, Any] | None, optional): JSON request body. Defaults to None.
        cron_expression (str | None, optional): Required if RECURRING. Defaults to None.
    """

    job_name: str = Field(..., min_length=1, max_length=30)
    method: HttpMethod
    endpoint: str = Field(..., max_length=2048)
    schedule_type: ScheduleType
    has_dependency: bool = False

    headers: Optional[Dict[str, Any]] = None
    body: Optional[Dict[str, Any]] = None
    cron_expression: Optional[str] = Field(default=None, max_length=100)


class JobCreate(JobBase):
    """
    Schema for creating a new Job.
    Used by the API router to validate incoming POST request payloads.
    Inherits all attributes from JobBase.
    """

    job_name: str
    method: HttpMethod
    endpoint: str
    schedule_type: ScheduleType
    headers: Optional[dict] = None
    body: Optional[dict] = None
    cron_expression: Optional[str] = None
    depends_on: Optional[list[int]] = None # 💡 請他加上這一行！


class JobResponse(JobBase):
    """
    Schema for serializing Job data in API responses.
    Includes current execution status and database-generated fields.

    Attributes:
        job_id (int): Internal primary key.
        owner_id (int): ID of the user who created the job.
        status (JobStatus): Current status of the job.
        next_run_time (datetime | None): Next execution timestamp.
        created_at (datetime): Creation timestamp.
        updated_at (datetime): Last modified timestamp.
    """

    job_id: int
    owner_id: int
    status: JobStatus
    next_run_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobUpdate(BaseModel):
    """
    Schema for updating an existing Job.
    All fields are optional to support partial updates (PATCH).

    Attributes:
        job_name (str | None, optional): Human-readable name for the job.
        method (HttpMethod | None, optional): The HTTP method to use.
        endpoint (str | None, optional): The target URL for the request.
        schedule_type (ScheduleType | None, optional): ONE_TIME or RECURRING.
        has_dependency (bool | None, optional): Indicates if this job waits for upstream jobs.
        headers (Dict[str, Any] | None, optional): JSON-serialized HTTP headers.
        body (Dict[str, Any] | None, optional): JSON-serialized HTTP request body payload.
        cron_expression (str | None, optional): The cron schedule string.
    """

    job_name: Optional[str] = Field(default=None, min_length=1, max_length=30)
    method: Optional[HttpMethod] = None
    endpoint: Optional[str] = Field(default=None, max_length=2048)
    schedule_type: Optional[ScheduleType] = None
    has_dependency: Optional[bool] = None

    headers: Optional[Dict[str, Any]] = None
    body: Optional[Dict[str, Any]] = None
    cron_expression: Optional[str] = Field(default=None, max_length=100)


# ==========================================
# 3. Execution Schemas
# ==========================================


class LogReferenceResponse(BaseModel):
    """Schema for returning log metadata to the frontend."""

    log_id: int
    execution_id: int
    log_path: str
    log_size: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExecutionLogsResponse(BaseModel):
    """Schema for returning execution log metadata."""

    execution_id: int
    logs: list[LogReferenceResponse]


class ExecutionResponse(BaseModel):
    """
    Schema for returning execution history to the frontend.

    Attributes:
        execution_id (int): Internal primary key.
        job_id (int): ID of the parent job.
        trigger_type (TriggerType): Indicates how the execution was triggered.
        status (ExecutionStatus): Current status of the execution.
        start_time (datetime | None): Timestamp when processing started.
        end_time (datetime | None): Timestamp when processing finished.
        duration (int | None): Execution duration in seconds.
        worker_id (str | None): Identifier of the processing worker node.
        retry_count (int): Number of retries attempted.
        error_message (str | None): Error details if failed.
        created_at (datetime): Creation timestamp.
    """

    execution_id: int
    job_id: int
    trigger_type: TriggerType
    status: ExecutionStatus
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    duration: Optional[int]
    worker_id: Optional[str]
    retry_count: int
    error_message: Optional[str]
    created_at: datetime
    log_reference: Optional[LogReferenceResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ExecutionHistoryResponse(BaseModel):
    """Paginated execution history response."""

    items: list[ExecutionResponse]
    skip: int
    limit: int
    count: int


class TaskDispatchPayload(BaseModel):
    """Queue payload shape expected by the worker execution layer."""

    execution_id: int
    job_id: int
    task_type: str
    payload: Dict[str, Any]
    timeout_threshold: int = 60


class ManualTriggerDispatchInfo(BaseModel):
    """Dispatch metadata returned by manual trigger API."""

    queued: bool
    queue_name: Optional[str] = None
    reason: str
    task_payload: TaskDispatchPayload


class ManualTriggerResponse(BaseModel):
    """Response returned after a manual trigger request is recorded."""

    execution: ExecutionResponse
    dispatch: ManualTriggerDispatchInfo


class ExecutionWorkerUpdate(BaseModel):
    """
    Schema used by remote workers to report execution results back to the
    main server. Records structured result metadata while keeping large logs
    in external storage.

    Attributes:
        status (ExecutionStatus): The new execution status (Required).
        worker_id (str): Identifier of the worker node (Required).
        error_message (str | None, optional): Detailed error message. Defaults to None.
    """

    job_id: Optional[int] = None
    status: ExecutionStatus
    worker_id: str = Field(..., max_length=50)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = Field(default=None, ge=0)
    retry_count: Optional[int] = Field(default=None, ge=0)
    error_message: Optional[str] = Field(default=None, max_length=4000)

    log_path: Optional[str] = Field(default=None, max_length=1024)
    log_size: Optional[int] = Field(default=None)


# ==========================================
# 4. Job Dependency Schemas
# ==========================================


class JobDependencyCreate(BaseModel):
    """
    Schema for creating a dependency link between two jobs.

    Attributes:
        upstream_id (int): The ID of the job that must finish first (Required).
        downstream_id (int): The ID of the job that waits (Required).
    """

    upstream_id: int = Field(
        ..., description="The ID of the job that must finish first"
    )
    downstream_id: int = Field(..., description="The ID of the job that waits")


class JobDependencyResponse(JobDependencyCreate):
    """
    Schema for returning dependency information.

    Attributes:
        dependency_id (int): Internal primary key.
        created_at (datetime): Creation timestamp.
    """

    dependency_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 5. Log Reference Schemas
# ==========================================


class ExecutionResultReportResponse(BaseModel):
    """Schema returned after a worker reports an execution result."""

    execution: ExecutionResponse
    log_reference: Optional[LogReferenceResponse] = None
