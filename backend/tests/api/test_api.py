from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.database import crud, schemas
from src.database.connection import Base, get_db
from src.database.models import (
    ExecutionStatus,
    HttpMethod,
    ScheduleType,
    TriggerType,
    UserRole,
)
from src.utils import logger as log_storage


@pytest.fixture()
def api_db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with sessionmaker(bind=engine)() as session:
        yield session

    Base.metadata.drop_all(engine)


@pytest.fixture()
def client(api_db_session):
    def override_get_db():
        yield api_db_session

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def _create_job(api_db_session, employee_id="api_history_dev"):
    user = crud.create_user(
        db=api_db_session,
        user_in=schemas.UserCreate(
            employee_id=employee_id,
            username="ApiHistoryUser",
            role=UserRole.DEVELOPER,
        ),
    )
    return crud.create_job(
        db=api_db_session,
        owner_id=user.user_id,
        job_in=schemas.JobCreate(
            job_name="API History",
            method=HttpMethod.GET,
            endpoint="http://test.com/api-history",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )


def _create_execution(
    api_db_session,
    job_id,
    trigger_type=TriggerType.MANUAL,
    status=ExecutionStatus.PENDING,
    created_at=None,
):
    execution = crud.create_execution(
        db=api_db_session,
        job_id=job_id,
        trigger_type=trigger_type,
    )
    execution.status = status
    if created_at is not None:
        execution.created_at = created_at
    api_db_session.commit()
    api_db_session.refresh(execution)
    return execution


def _create_default_job_owner(api_db_session):
    return crud.create_user(
        db=api_db_session,
        user_in=schemas.UserCreate(
            employee_id="api_default_owner",
            username="ApiDefaultOwner",
            role=UserRole.DEVELOPER,
        ),
    )


def test_get_job_executions_success(client, api_db_session):
    job = _create_job(api_db_session)
    _create_execution(api_db_session, job.job_id)

    response = client.get(f"/api/jobs/{job.job_id}/executions")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["items"][0]["job_id"] == job.job_id


def test_manual_trigger_returns_execution_and_dispatch_preview(
    client,
    api_db_session,
):
    job = _create_job(api_db_session)

    response = client.post(f"/api/jobs/{job.job_id}/trigger")

    assert response.status_code == 201
    body = response.json()
    assert body["execution"]["job_id"] == job.job_id
    assert body["execution"]["trigger_type"] == "Manual"
    assert body["execution"]["status"] == "Pending"
    assert body["dispatch"]["queued"] is False
    assert body["dispatch"]["task_payload"]["job_id"] == job.job_id
    assert (
        body["dispatch"]["task_payload"]["execution_id"]
        == body["execution"]["execution_id"]
    )
    assert body["dispatch"]["task_payload"]["task_type"] == "http"
    assert body["dispatch"]["task_payload"]["payload"]["method"] == "GET"
    assert (
        body["dispatch"]["task_payload"]["payload"]["endpoint"]
        == "http://test.com/api-history"
    )


def test_get_job_executions_job_not_found(client):
    response = client.get("/api/jobs/9999/executions")

    assert response.status_code == 404


def test_get_execution_success(client, api_db_session):
    job = _create_job(api_db_session)
    execution = _create_execution(api_db_session, job.job_id)

    response = client.get(f"/api/executions/{execution.execution_id}")

    assert response.status_code == 200
    assert response.json()["execution_id"] == execution.execution_id


def test_get_execution_not_found(client):
    response = client.get("/api/executions/9999")

    assert response.status_code == 404


def test_get_job_executions_status_filter(client, api_db_session):
    job = _create_job(api_db_session)
    _create_execution(
        api_db_session,
        job.job_id,
        status=ExecutionStatus.SUCCESS,
    )
    _create_execution(
        api_db_session,
        job.job_id,
        status=ExecutionStatus.FAILED,
    )

    response = client.get(
        f"/api/jobs/{job.job_id}/executions",
        params={"status": "Success"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["items"][0]["status"] == "Success"


def test_get_job_executions_trigger_type_filter(client, api_db_session):
    job = _create_job(api_db_session)
    _create_execution(
        api_db_session,
        job.job_id,
        trigger_type=TriggerType.MANUAL,
    )
    _create_execution(
        api_db_session,
        job.job_id,
        trigger_type=TriggerType.SCHEDULER,
    )

    response = client.get(
        f"/api/jobs/{job.job_id}/executions",
        params={"trigger_type": "Manual"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["items"][0]["trigger_type"] == "Manual"


def test_get_job_executions_pagination(client, api_db_session):
    job = _create_job(api_db_session)
    base_time = datetime(2026, 1, 1)
    first = _create_execution(
        api_db_session,
        job.job_id,
        created_at=base_time,
    )
    second = _create_execution(
        api_db_session,
        job.job_id,
        created_at=base_time + timedelta(minutes=1),
    )

    response = client.get(
        f"/api/jobs/{job.job_id}/executions",
        params={"skip": 1, "limit": 1},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["skip"] == 1
    assert body["limit"] == 1
    assert body["count"] == 1
    assert body["items"][0]["execution_id"] == first.execution_id
    assert body["items"][0]["execution_id"] != second.execution_id


def test_register_job_without_depends_on_sets_has_dependency_false(
    client,
    api_db_session,
):
    _create_default_job_owner(api_db_session)

    response = client.post(
        "/api/jobs/",
        json={
            "job_name": "No Dependency",
            "method": "GET",
            "endpoint": "http://test.com/no-dependency",
            "schedule_type": "One-time",
        },
    )

    assert response.status_code == 201
    job = crud.get_job_by_id(
        db=api_db_session,
        job_id=response.json()["job_id"],
    )
    assert job is not None
    assert job.has_dependency is False


def test_register_job_with_depends_on_sets_has_dependency_true(
    client,
    api_db_session,
):
    owner = _create_default_job_owner(api_db_session)
    upstream = crud.create_job(
        db=api_db_session,
        owner_id=owner.user_id,
        job_in=schemas.JobCreate(
            job_name="Upstream",
            method=HttpMethod.GET,
            endpoint="http://test.com/upstream",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )

    response = client.post(
        "/api/jobs/",
        json={
            "job_name": "Downstream",
            "method": "GET",
            "endpoint": "http://test.com/downstream",
            "schedule_type": "One-time",
            "depends_on": [upstream.job_id],
        },
    )

    assert response.status_code == 201
    job = crud.get_job_by_id(
        db=api_db_session,
        job_id=response.json()["job_id"],
    )
    assert job is not None
    assert job.has_dependency is True

    upstream_dependencies = crud.get_upstream_dependencies(
        db=api_db_session,
        job_id=job.job_id,
    )
    assert len(upstream_dependencies) == 1
    assert upstream_dependencies[0].upstream_id == upstream.job_id


def _worker_result_payload(**overrides):
    payload = {
        "status": "Success",
        "worker_id": "api-test-worker",
    }
    payload.update(overrides)
    return payload


def test_report_execution_result_empty_log_path_returns_400(client, api_db_session):
    job = _create_job(api_db_session, "api_log_empty")
    execution = _create_execution(api_db_session, job.job_id)

    response = client.patch(
        f"/api/executions/{execution.execution_id}/result",
        json=_worker_result_payload(log_path="", log_size=0),
    )

    assert response.status_code == 400


def test_report_execution_result_negative_log_size_returns_400(client, api_db_session):
    job = _create_job(api_db_session, "api_log_negative")
    execution = _create_execution(api_db_session, job.job_id)

    response = client.patch(
        f"/api/executions/{execution.execution_id}/result",
        json=_worker_result_payload(
            log_path="/app/logs/executions/negative.log",
            log_size=-1,
        ),
    )

    assert response.status_code == 400


def test_report_execution_result_with_log_metadata_creates_reference(
    client,
    api_db_session,
):
    job = _create_job(api_db_session, "api_log_create")
    execution = _create_execution(api_db_session, job.job_id)

    response = client.patch(
        f"/api/executions/{execution.execution_id}/result",
        json=_worker_result_payload(
            log_path="/app/logs/executions/create.log",
            log_size=128,
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["log_reference"]["execution_id"] == execution.execution_id
    assert body["log_reference"]["log_path"] == "/app/logs/executions/create.log"
    assert body["log_reference"]["log_size"] == 128


def test_get_execution_logs_execution_not_found(client):
    response = client.get("/api/executions/9999/logs")

    assert response.status_code == 404


def test_get_execution_logs_without_log_reference_returns_empty_logs(
    client,
    api_db_session,
):
    job = _create_job(api_db_session, "api_log_empty_list")
    execution = _create_execution(api_db_session, job.job_id)

    response = client.get(f"/api/executions/{execution.execution_id}/logs")

    assert response.status_code == 200
    assert response.json() == {
        "execution_id": execution.execution_id,
        "logs": [],
    }


def test_get_execution_logs_with_log_reference_returns_metadata(
    client,
    api_db_session,
):
    job = _create_job(api_db_session, "api_log_metadata")
    execution = _create_execution(api_db_session, job.job_id)
    log_ref = crud.create_log_reference(
        db=api_db_session,
        execution_id=execution.execution_id,
        log_path="/app/logs/executions/metadata.log",
        log_size=256,
    )

    response = client.get(f"/api/executions/{execution.execution_id}/logs")

    assert response.status_code == 200
    body = response.json()
    assert body["execution_id"] == execution.execution_id
    assert body["logs"][0]["log_id"] == log_ref.log_id
    assert body["logs"][0]["execution_id"] == execution.execution_id
    assert body["logs"][0]["log_path"] == "/app/logs/executions/metadata.log"
    assert body["logs"][0]["log_size"] == 256
    assert body["logs"][0]["created_at"] is not None


def test_get_execution_log_content_returns_plain_text(
    client,
    api_db_session,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(log_storage, "LOG_ROOT", str(tmp_path))
    job = _create_job(api_db_session, "api_log_content")
    execution = _create_execution(api_db_session, job.job_id)
    log_path, log_size = log_storage.write_execution_log(
        execution.execution_id,
        "worker output",
    )
    crud.create_log_reference(
        db=api_db_session,
        execution_id=execution.execution_id,
        log_path=log_path,
        log_size=log_size,
    )

    response = client.get(f"/api/executions/{execution.execution_id}/logs/content")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text == "worker output"


def test_get_execution_log_content_missing_file_returns_404(
    client,
    api_db_session,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(log_storage, "LOG_ROOT", str(tmp_path))
    job = _create_job(api_db_session, "api_log_missing")
    execution = _create_execution(api_db_session, job.job_id)
    crud.create_log_reference(
        db=api_db_session,
        execution_id=execution.execution_id,
        log_path=str(tmp_path / "executions" / "missing.log"),
        log_size=10,
    )

    response = client.get(f"/api/executions/{execution.execution_id}/logs/content")

    assert response.status_code == 404
