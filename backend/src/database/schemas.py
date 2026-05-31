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
        ..., min_length=4, max_length=20, description="Unique employee identifier"
    )
    username: str = Field(
        ..., min_length=1, max_length=30, description="Display name of the user"
    )
    role: UserRole = Field(description="Authorization role")


class UserCreate(UserBase):
    """
    Schema for creating a new User.
    Used by the API router to validate incoming POST request payloads.
    Inherits all required attributes from UserBase (employee_id, username, role).
    """

    pass


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

# 1. 檢查 ID
class CheckIdRequest(BaseModel):
    employee_id: str

class CheckIdResponse(BaseModel):
    isRegistered: bool

# 2. 註冊密碼
class RegisterPasswordRequest(BaseModel):
    employee_id: str
    password: str

# 3. 登入驗證
class LoginRequest(BaseModel):
    employee_id: str
    password: str

class LoginResponse(BaseModel):
    id: str  # 對應前端的 user.id (通常放 employee_id)
    role: str # 'developer' | 'operator' | 'admin'

# 4. 重設密碼
class ResetPasswordRequest(BaseModel):
    employee_id: str
    new_password: str


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

    pass


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

    model_config = ConfigDict(from_attributes=True)


class ExecutionWorkerUpdate(BaseModel):
    """
    Schema used by remote workers to report execution results back to the main server.
    Only allows updating status, timing, and error details.

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


class LogReferenceResponse(BaseModel):
    """
    Schema for returning log metadata to the frontend.

    Attributes:
        log_id (int): Internal primary key.
        execution_id (int): ID of the associated execution.
        log_path (str): File path or URI of the log.
        log_size (int): Size of the log in bytes.
        created_at (datetime): Creation timestamp.
    """

    log_id: int
    execution_id: int
    log_path: str
    log_size: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExecutionResultReportResponse(BaseModel):
    """Schema returned after a worker reports an execution result."""

    execution: ExecutionResponse
    log_reference: Optional[LogReferenceResponse] = None
