from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from src.database.models import UserRole, HttpMethod, ScheduleType, JobStatus
from src.database.models import TriggerType, ExecutionStatus

# ==========================================
# 1. User Schemas
# ==========================================


class UserBase(BaseModel):
    """Base schema containing common attributes for a User."""

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
    """

    pass


class UserResponse(UserBase):
    """
    Schema for serializing User data in API responses.
    Includes database-generated fields like IDs and timestamps.
    """

    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Enables Pydantic to read data directly from SQLAlchemy ORM models
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 2. Job Schemas
# ==========================================


class JobBase(BaseModel):
    """Base schema containing common attributes for a scheduled Job."""

    job_name: str = Field(..., min_length=1, max_length=30)
    method: HttpMethod
    endpoint: str = Field(..., max_length=2048)
    schedule_type: ScheduleType
    has_dependency: bool = False

    # Optional configurations
    headers: Optional[Dict[str, Any]] = None
    body: Optional[Dict[str, Any]] = None
    cron_expression: Optional[str] = Field(default=None, max_length=100)


class JobCreate(JobBase):
    """
    Schema for creating a new Job.
    Used by the API router to validate incoming POST request payloads.
    """

    pass


class JobResponse(JobBase):
    """
    Schema for serializing Job data in API responses.
    Includes current execution status and database-generated fields.
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
    """Schema for returning execution history to the frontend."""

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
    """

    status: ExecutionStatus
    worker_id: str = Field(..., max_length=50)
    error_message: Optional[str] = Field(default=None, max_length=4000)
    # The CRUD function will calculate end_time and duration automatically


# ==========================================
# 4. Job Dependency Schemas
# ==========================================


class JobDependencyCreate(BaseModel):
    """Schema for creating a dependency link between two jobs."""

    upstream_id: int = Field(
        ..., description="The ID of the job that must finish first"
    )
    downstream_id: int = Field(..., description="The ID of the job that waits")


class JobDependencyResponse(JobDependencyCreate):
    """Schema for returning dependency information."""

    dependency_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 5. Log Reference Schemas
# ==========================================


class LogReferenceResponse(BaseModel):
    """Schema for returning log metadata to the frontend."""

    log_id: int
    execution_id: int
    log_path: str
    log_size: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
