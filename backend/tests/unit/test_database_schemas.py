import pytest
from pydantic import ValidationError

from src.database import schemas
from src.database.models import ExecutionStatus, HttpMethod, ScheduleType

pytestmark = pytest.mark.unit


def test_user_create_rejects_short_password():
    with pytest.raises(ValidationError):
        schemas.UserCreate(
            employee_id="schema_user",
            username="SchemaUser",
            password="short",
        )


def test_job_create_rejects_invalid_method():
    with pytest.raises(ValidationError):
        schemas.JobCreate(
            job_name="Invalid Method",
            method="TRACE",
            endpoint="http://example.test",
            schedule_type=ScheduleType.ONE_TIME,
        )


def test_job_create_rejects_missing_endpoint():
    with pytest.raises(ValidationError):
        schemas.JobCreate(
            job_name="Missing Endpoint",
            method=HttpMethod.GET,
            schedule_type=ScheduleType.ONE_TIME,
        )


def test_execution_worker_update_rejects_negative_duration():
    with pytest.raises(ValidationError):
        schemas.ExecutionWorkerUpdate(
            status=ExecutionStatus.SUCCESS,
            worker_id="worker-1",
            duration=-1,
        )


def test_execution_worker_update_rejects_negative_retry_count():
    with pytest.raises(ValidationError):
        schemas.ExecutionWorkerUpdate(
            status=ExecutionStatus.SUCCESS,
            worker_id="worker-1",
            retry_count=-1,
        )
