import pytest
import math
from pydantic import ValidationError

from src.worker.schemas import HeartbeatState, TaskPayload

pytestmark = pytest.mark.unit


def test_task_payload_accepts_valid_payload_and_defaults_timeout():
    task = TaskPayload(
        execution_id=1,
        job_id=10,
        task_type="http",
        payload={"method": "GET"},
    )

    assert task.execution_id == 1
    assert task.job_id == 10
    assert task.task_type == "http"
    assert task.payload == {"method": "GET"}
    assert task.timeout_threshold == 60


def test_task_payload_rejects_missing_required_fields():
    with pytest.raises(ValidationError):
        TaskPayload(job_id=10, task_type="http")


def test_task_payload_rejects_invalid_integer_fields():
    with pytest.raises(ValidationError):
        TaskPayload(
            execution_id="not-int",
            job_id=10,
            task_type="http",
            payload={},
        )


def test_heartbeat_state_defaults_progress_fields():
    heartbeat = HeartbeatState(
        job_id=10,
        execution_id=1,
        last_active_time=123.45,
    )

    assert heartbeat.status == "RUNNING"
    assert heartbeat.checkpoint_line == 0
    assert heartbeat.percentage == pytest.approx(0.0)
