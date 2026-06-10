from datetime import datetime, timedelta
from unittest.mock import patch

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
    JobStatus,
    ScheduleType,
    TriggerType,
    User,
    UserRole,
)
from src.utils import logger as log_storage
from src.utils.security import create_access_token, hash_password

pytestmark = [pytest.mark.integration, pytest.mark.api, pytest.mark.auth]


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


def _auth_headers_for_user(user):
    token = create_access_token(subject=str(user.user_id))
    return {"Authorization": f"Bearer {token}"}


def _auth_headers_for_job(api_db_session, job):
    user = crud.get_user_by_user_id(db=api_db_session, user_id=job.owner_id)
    return _auth_headers_for_user(user)


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


def _create_test_admin(api_db_session):
    admin = User(
        employee_id="admin",
        username="Admin",
        role=UserRole.ADMIN,
        hashed_password=hash_password("admin"),
    )
    api_db_session.add(admin)
    api_db_session.commit()
    api_db_session.refresh(admin)
    return admin


def test_auth_register_succeeds(client):
    response = client.post(
        "/api/auth/register",
        json={
            "employee_id": "auth_user_1",
            "username": "AuthUserOne",
            "email": "auth1@example.com",
            "password": "secret123",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["employee_id"] == "auth_user_1"
    assert body["email"] == "auth1@example.com"
    assert "hashed_password" not in body


def test_auth_register_rejects_duplicate_email_or_username(client):
    payload = {
        "employee_id": "auth_user_2",
        "username": "AuthUserTwo",
        "email": "auth2@example.com",
        "password": "secret123",
    }
    assert client.post("/api/auth/register", json=payload).status_code == 201

    duplicate_email = {
        **payload,
        "employee_id": "auth_user_3",
        "username": "AuthUserThree",
    }
    duplicate_username = {
        **payload,
        "employee_id": "auth_user_4",
        "email": "auth4@example.com",
    }

    assert client.post("/api/auth/register", json=duplicate_email).status_code == 409
    assert client.post("/api/auth/register", json=duplicate_username).status_code == 409


def test_auth_register_rejects_duplicate_employee_id(client):
    payload = {
        "employee_id": "auth_user_2b",
        "username": "AuthUserTwoB",
        "email": "auth2b@example.com",
        "password": "secret123",
    }
    assert client.post("/api/auth/register", json=payload).status_code == 201

    duplicate_employee_id = {
        **payload,
        "username": "AuthUserTwoC",
        "email": "auth2c@example.com",
    }

    response = client.post("/api/auth/register", json=duplicate_employee_id)

    assert response.status_code == 409


def test_auth_login_returns_access_token(client):
    client.post(
        "/api/auth/register",
        json={
            "employee_id": "auth_user_5",
            "username": "AuthUserFive",
            "email": "auth5@example.com",
            "password": "secret123",
        },
    )

    response = client.post(
        "/api/auth/login",
        json={"identifier": "auth5@example.com", "password": "secret123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] == 3600
    assert body["user"]["username"] == "AuthUserFive"


def test_builtin_admin_login_returns_admin_token(client, api_db_session):
    _create_test_admin(api_db_session)

    response = client.post(
        "/api/auth/login-password",
        json={"employee_id": "admin", "password": "admin"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["user"]["employee_id"] == "admin"
    assert body["user"]["role"] == "Admin"


def test_admin_can_list_and_delete_other_users(client, api_db_session):
    _create_test_admin(api_db_session)

    admin_login = client.post(
        "/api/auth/login-password",
        json={"employee_id": "admin", "password": "admin"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    created = client.post(
        "/api/auth/register",
        json={
            "employee_id": "managed_user_1",
            "username": "ManagedUserOne",
            "password": "secret123",
            "role": "Developer",
        },
    )
    assert created.status_code == 201

    users_response = client.get("/api/auth/users", headers=admin_headers)

    assert users_response.status_code == 200
    managed_user = next(
        user
        for user in users_response.json()
        if user["employee_id"] == "managed_user_1"
    )

    delete_response = client.delete(
        f"/api/auth/users/{managed_user['user_id']}",
        headers=admin_headers,
    )

    assert delete_response.status_code == 204
    users_after_delete = client.get("/api/auth/users", headers=admin_headers)
    assert "managed_user_1" not in {
        user["employee_id"] for user in users_after_delete.json()
    }


def test_admin_cannot_delete_builtin_admin(client, api_db_session):
    _create_test_admin(api_db_session)

    admin_login = client.post(
        "/api/auth/login-password",
        json={"employee_id": "admin", "password": "admin"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    users_response = client.get("/api/auth/users", headers=admin_headers)
    admin_user = next(
        user for user in users_response.json() if user["employee_id"] == "admin"
    )

    response = client.delete(
        f"/api/auth/users/{admin_user['user_id']}",
        headers=admin_headers,
    )

    assert response.status_code == 400


def test_auth_register_normalizes_email_and_rejects_duplicate(client):
    response = client.post(
        "/api/auth/register",
        json={
            "employee_id": " auth_user_7 ",
            "username": " AuthUserSeven ",
            "email": " AUTH7@EXAMPLE.COM ",
            "password": "secret123",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["employee_id"] == "auth_user_7"
    assert body["username"] == "AuthUserSeven"
    assert body["email"] == "auth7@example.com"

    duplicate = {
        "employee_id": "auth_user_8",
        "username": "AuthUserEight",
        "email": "auth7@example.com",
        "password": "secret123",
    }
    assert client.post("/api/auth/register", json=duplicate).status_code == 409


def test_auth_login_accepts_form_payload(client):
    client.post(
        "/api/auth/register",
        json={
            "employee_id": "auth_user_9",
            "username": "AuthUserNine",
            "email": "auth9@example.com",
            "password": "secret123",
        },
    )

    response = client.post(
        "/api/auth/login",
        data={"username": "auth_user_9", "password": "secret123"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["username"] == "AuthUserNine"


def test_auth_me_returns_current_user(client, api_db_session):
    user = crud.create_user(
        db=api_db_session,
        user_in=schemas.UserCreate(
            employee_id="auth_me_user",
            username="AuthMeUser",
            email="auth-me@example.com",
            password="secret123",
        ),
    )

    response = client.get("/api/auth/me", headers=_auth_headers_for_user(user))

    assert response.status_code == 200
    assert response.json()["user_id"] == user.user_id
    assert response.json()["email"] == "auth-me@example.com"


def test_auth_logout_requires_valid_token(client):
    assert client.post("/api/auth/logout").status_code == 401


def test_auth_login_invalid_password_fails(client):
    client.post(
        "/api/auth/register",
        json={
            "employee_id": "auth_user_6",
            "username": "AuthUserSix",
            "email": "auth6@example.com",
            "password": "secret123",
        },
    )

    response = client.post(
        "/api/auth/login",
        json={"identifier": "auth6@example.com", "password": "wrong"},
    )

    assert response.status_code == 401


@patch("src.api.routers.auth.send_password_reset_email")
def test_forgot_password_sends_email_for_account_with_email(
    mock_send_email,
    client,
):
    client.post(
        "/api/auth/register",
        json={
            "employee_id": "forgot_user_1",
            "username": "ForgotUserOne",
            "email": "forgot1@example.com",
            "password": "secret123",
        },
    )

    response = client.post(
        "/api/auth/forgot-password",
        json={"employee_id": "forgot_user_1"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "sent"
    mock_send_email.assert_called_once()
    assert mock_send_email.call_args.args[0] == "forgot1@example.com"
    assert "reset_token=" in mock_send_email.call_args.args[1]


def test_forgot_password_reports_missing_email(client):
    client.post(
        "/api/auth/register",
        json={
            "employee_id": "forgot_user_2",
            "username": "ForgotUserTwo",
            "password": "secret123",
        },
    )

    response = client.post(
        "/api/auth/forgot-password",
        json={"employee_id": "forgot_user_2"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "missing_email"


def test_reset_password_requires_valid_reset_token(client, api_db_session):
    user = crud.create_user(
        db=api_db_session,
        user_in=schemas.UserCreate(
            employee_id="forgot_user_3",
            username="ForgotUserThree",
            email="forgot3@example.com",
            password="oldsecret",
        ),
    )
    token = create_access_token(
        subject=str(user.user_id),
        extra_claims={"purpose": "password_reset"},
    )

    response = client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": "newsecret"},
    )

    assert response.status_code == 200
    assert response.json()["employee_id"] == "forgot_user_3"
    login = client.post(
        "/api/auth/login-password",
        json={"employee_id": "forgot_user_3", "password": "newsecret"},
    )
    assert login.status_code == 200


def test_admin_can_reset_user_password(client, api_db_session):
    admin = _create_test_admin(api_db_session)
    user = crud.create_user(
        db=api_db_session,
        user_in=schemas.UserCreate(
            employee_id="managed_reset_1",
            username="ManagedResetOne",
            password="oldsecret",
        ),
    )

    response = client.patch(
        f"/api/auth/users/{user.user_id}/password",
        json={"new_password": "newsecret"},
        headers=_auth_headers_for_user(admin),
    )

    assert response.status_code == 200
    login = client.post(
        "/api/auth/login-password",
        json={"employee_id": "managed_reset_1", "password": "newsecret"},
    )
    assert login.status_code == 200


def test_invalid_token_is_rejected(client):
    response = client.get(
        "/api/jobs/",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )

    assert response.status_code == 401


def test_get_job_executions_success(client, api_db_session):
    job = _create_job(api_db_session)
    _create_execution(api_db_session, job.job_id)

    response = client.get(
        f"/api/jobs/{job.job_id}/executions",
        headers=_auth_headers_for_job(api_db_session, job),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["items"][0]["job_id"] == job.job_id


@patch("src.api.routers.jobs.dispatch_task")
def test_manual_trigger_creates_execution_and_dispatches(
    mock_dispatch,
    client,
    api_db_session,
):
    job = _create_job(api_db_session)
    mock_dispatch.return_value = {
        "queued": True,
        "queue_name": "job_priority_queue",
        "task_payload": {
            "execution_id": 1,
            "job_id": job.job_id,
            "task_type": "http",
            "payload": {
                "method": "GET",
                "endpoint": "http://test.com/api-history",
                "headers": {},
                "body": {},
            },
            "timeout_threshold": 300,
        },
    }

    response = client.post(
        f"/api/jobs/{job.job_id}/trigger",
        headers=_auth_headers_for_job(api_db_session, job),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["execution"]["job_id"] == job.job_id
    assert body["execution"]["trigger_type"] == "Manual"
    assert body["execution"]["status"] == "Pending"
    assert body["dispatch"]["queued"] is True
    assert body["dispatch"]["queue_name"] == "job_priority_queue"
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
    mock_dispatch.assert_called_once()


@patch("src.api.routers.jobs.dispatch_task")
def test_manual_trigger_does_not_require_next_run_time(
    mock_dispatch,
    client,
    api_db_session,
):
    job = _create_job(api_db_session, "api_manual_no_run")
    job.next_run_time = None
    api_db_session.commit()
    mock_dispatch.return_value = {
        "queued": True,
        "queue_name": "job_priority_queue",
        "task_payload": {
            "execution_id": 1,
            "job_id": job.job_id,
            "task_type": "http",
            "payload": {
                "method": "GET",
                "endpoint": "http://test.com/api-history",
                "headers": {},
                "body": {},
            },
            "timeout_threshold": 300,
        },
    }

    response = client.post(
        f"/api/jobs/{job.job_id}/trigger",
        headers=_auth_headers_for_job(api_db_session, job),
    )

    assert response.status_code == 201
    assert response.json()["execution"]["status"] == "Pending"
    mock_dispatch.assert_called_once()


@patch("src.api.routers.jobs.dispatch_task")
def test_manual_trigger_dispatches_shell_job_as_shell_task(
    mock_dispatch,
    client,
    api_db_session,
):
    owner = _create_default_job_owner(api_db_session)
    job = crud.create_job(
        db=api_db_session,
        owner_id=owner.user_id,
        job_in=schemas.JobCreate(
            job_name="Shell Success",
            method=HttpMethod.POST,
            endpoint="shell://local",
            schedule_type=ScheduleType.ONE_TIME,
            headers={"task_type": "shell"},
            body={"command": "echo hello"},
        ),
    )
    mock_dispatch.return_value = {
        "queued": True,
        "queue_name": "job_priority_queue",
        "task_payload": {
            "execution_id": 1,
            "job_id": job.job_id,
            "task_type": "shell",
            "payload": {},
            "timeout_threshold": 60,
        },
    }

    response = client.post(
        f"/api/jobs/{job.job_id}/trigger",
        headers=_auth_headers_for_user(owner),
    )

    assert response.status_code == 201
    called_job_dict = mock_dispatch.call_args.kwargs["job_dict"]
    assert called_job_dict["task_type"] == "shell"


def test_get_job_executions_job_not_found(client, api_db_session):
    user = _create_default_job_owner(api_db_session)
    response = client.get(
        "/api/jobs/9999/executions",
        headers=_auth_headers_for_user(user),
    )

    assert response.status_code == 404


def test_get_execution_success(client, api_db_session):
    job = _create_job(api_db_session)
    execution = _create_execution(api_db_session, job.job_id)

    response = client.get(
        f"/api/executions/{execution.execution_id}",
        headers=_auth_headers_for_job(api_db_session, job),
    )

    assert response.status_code == 200
    assert response.json()["execution_id"] == execution.execution_id


def test_get_execution_not_found(client, api_db_session):
    user = _create_default_job_owner(api_db_session)
    response = client.get(
        "/api/executions/9999",
        headers=_auth_headers_for_user(user),
    )

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
        headers=_auth_headers_for_job(api_db_session, job),
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
        headers=_auth_headers_for_job(api_db_session, job),
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
        headers=_auth_headers_for_job(api_db_session, job),
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
    user = _create_default_job_owner(api_db_session)

    response = client.post(
        "/api/jobs/",
        json={
            "job_name": "No Dependency",
            "method": "GET",
            "endpoint": "http://test.com/no-dependency",
            "schedule_type": "One-time",
        },
        headers=_auth_headers_for_user(user),
    )

    assert response.status_code == 201
    job = crud.get_job_by_id(
        db=api_db_session,
        job_id=response.json()["job_id"],
    )
    assert job is not None
    assert job.has_dependency is False
    assert job.next_run_time is not None
    assert job.owner_id == user.user_id


def test_register_recurring_job_computes_next_run_time(client, api_db_session):
    user = _create_default_job_owner(api_db_session)

    response = client.post(
        "/api/jobs/",
        json={
            "job_name": "Recurring",
            "method": "GET",
            "endpoint": "http://test.com/recurring",
            "schedule_type": "Recurring",
            "cron_expression": "*/5 * * * *",
        },
        headers=_auth_headers_for_user(user),
    )

    assert response.status_code == 201
    job = crud.get_job_by_id(
        db=api_db_session,
        job_id=response.json()["job_id"],
    )
    assert job is not None
    assert job.next_run_time is not None


def test_register_recurring_job_rejects_invalid_cron(client, api_db_session):
    user = _create_default_job_owner(api_db_session)

    response = client.post(
        "/api/jobs/",
        json={
            "job_name": "Bad Cron",
            "method": "GET",
            "endpoint": "http://test.com/bad-cron",
            "schedule_type": "Recurring",
            "cron_expression": "not a cron",
        },
        headers=_auth_headers_for_user(user),
    )

    assert response.status_code == 400


def test_register_recurring_job_without_cron_is_rejected(client, api_db_session):
    user = _create_default_job_owner(api_db_session)

    response = client.post(
        "/api/jobs/",
        json={
            "job_name": "Missing Cron",
            "method": "GET",
            "endpoint": "http://test.com/missing-cron",
            "schedule_type": "Recurring",
        },
        headers=_auth_headers_for_user(user),
    )

    assert response.status_code == 400


def test_register_job_rejects_unsupported_http_method(client, api_db_session):
    user = _create_default_job_owner(api_db_session)

    response = client.post(
        "/api/jobs/",
        json={
            "job_name": "Bad Method",
            "method": "TRACE",
            "endpoint": "http://test.com/bad-method",
            "schedule_type": "One-time",
        },
        headers=_auth_headers_for_user(user),
    )

    assert response.status_code == 422


def test_register_job_rejects_missing_endpoint(client, api_db_session):
    user = _create_default_job_owner(api_db_session)

    response = client.post(
        "/api/jobs/",
        json={
            "job_name": "Missing Endpoint",
            "method": "GET",
            "schedule_type": "One-time",
        },
        headers=_auth_headers_for_user(user),
    )

    assert response.status_code == 422


def test_unauthenticated_job_creation_is_rejected(client):
    response = client.post(
        "/api/jobs/",
        json={
            "job_name": "No Auth",
            "method": "GET",
            "endpoint": "http://test.com/no-auth",
            "schedule_type": "One-time",
        },
    )

    assert response.status_code == 401


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
        headers=_auth_headers_for_user(owner),
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


def test_job_listing_only_returns_authenticated_users_jobs(client, api_db_session):
    first_user = _create_default_job_owner(api_db_session)
    second_user = crud.create_user(
        db=api_db_session,
        user_in=schemas.UserCreate(
            employee_id="api_other_owner",
            username="ApiOtherOwner",
            role=UserRole.DEVELOPER,
        ),
    )
    first_job = crud.create_job(
        db=api_db_session,
        owner_id=first_user.user_id,
        job_in=schemas.JobCreate(
            job_name="Mine",
            method=HttpMethod.GET,
            endpoint="http://test.com/mine",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )
    crud.create_job(
        db=api_db_session,
        owner_id=second_user.user_id,
        job_in=schemas.JobCreate(
            job_name="Other",
            method=HttpMethod.GET,
            endpoint="http://test.com/other",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )

    response = client.get("/api/jobs/", headers=_auth_headers_for_user(first_user))

    assert response.status_code == 200
    assert [item["job_id"] for item in response.json()] == [first_job.job_id]


def test_operator_job_listing_returns_all_jobs(client, api_db_session):
    first_user = _create_default_job_owner(api_db_session)
    operator = crud.create_user(
        db=api_db_session,
        user_in=schemas.UserCreate(
            employee_id="api_operator",
            username="ApiOperator",
            role=UserRole.OPERATOR,
        ),
    )
    first_job = crud.create_job(
        db=api_db_session,
        owner_id=first_user.user_id,
        job_in=schemas.JobCreate(
            job_name="Developer Job",
            method=HttpMethod.GET,
            endpoint="http://test.com/developer-job",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )

    response = client.get("/api/jobs/", headers=_auth_headers_for_user(operator))

    assert response.status_code == 200
    assert first_job.job_id in {item["job_id"] for item in response.json()}


def test_developer_cannot_change_job_status(client, api_db_session):
    user = _create_default_job_owner(api_db_session)
    job = crud.create_job(
        db=api_db_session,
        owner_id=user.user_id,
        job_in=schemas.JobCreate(
            job_name="Developer Status",
            method=HttpMethod.GET,
            endpoint="http://test.com/developer-status",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )

    response = client.patch(
        f"/api/jobs/{job.job_id}/status",
        json={"status": "Disabled"},
        headers=_auth_headers_for_user(user),
    )

    assert response.status_code == 403


def test_operator_can_change_job_status(client, api_db_session):
    owner = _create_default_job_owner(api_db_session)
    operator = crud.create_user(
        db=api_db_session,
        user_in=schemas.UserCreate(
            employee_id="api_operator_status",
            username="ApiOperatorStatus",
            role=UserRole.OPERATOR,
        ),
    )
    job = crud.create_job(
        db=api_db_session,
        owner_id=owner.user_id,
        job_in=schemas.JobCreate(
            job_name="Operator Status",
            method=HttpMethod.GET,
            endpoint="http://test.com/operator-status",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )

    response = client.patch(
        f"/api/jobs/{job.job_id}/status",
        json={"status": "Disabled"},
        headers=_auth_headers_for_user(operator),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Disabled"


@patch("src.api.routers.history.dispatch_task")
def test_operator_rerun_increments_retry_count(
    mock_dispatch,
    client,
    api_db_session,
):
    owner = _create_default_job_owner(api_db_session)
    operator = crud.create_user(
        db=api_db_session,
        user_in=schemas.UserCreate(
            employee_id="api_operator_rerun",
            username="ApiOperatorRerun",
            role=UserRole.OPERATOR,
        ),
    )
    job = crud.create_job(
        db=api_db_session,
        owner_id=owner.user_id,
        job_in=schemas.JobCreate(
            job_name="Rerun Source",
            method=HttpMethod.GET,
            endpoint="http://test.com/rerun-source",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )
    execution = crud.create_execution(
        db=api_db_session,
        job_id=job.job_id,
        trigger_type=TriggerType.MANUAL,
        retry_count=2,
    )
    mock_dispatch.return_value = {
        "queued": True,
        "queue_name": "job_priority_queue",
        "task_payload": {
            "execution_id": execution.execution_id + 1,
            "job_id": job.job_id,
            "task_type": "http",
            "payload": {},
            "timeout_threshold": 60,
        },
    }

    response = client.post(
        f"/api/executions/{execution.execution_id}/rerun",
        headers=_auth_headers_for_user(operator),
    )

    assert response.status_code == 201
    assert response.json()["execution"]["retry_count"] == 3
    mock_dispatch.assert_called_once()


def test_get_job_detail_returns_authenticated_users_job(client, api_db_session):
    job = _create_job(api_db_session, "api_detail_owner")

    response = client.get(
        f"/api/jobs/{job.job_id}",
        headers=_auth_headers_for_job(api_db_session, job),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == job.job_id
    assert body["owner_id"] == job.owner_id


def test_get_job_detail_rejects_non_owner(client, api_db_session):
    job = _create_job(api_db_session, "api_detail_owner")
    other = crud.create_user(
        db=api_db_session,
        user_in=schemas.UserCreate(
            employee_id="api_detail_other",
            username="ApiDetailOther",
            role=UserRole.DEVELOPER,
        ),
    )

    response = client.get(
        f"/api/jobs/{job.job_id}",
        headers=_auth_headers_for_user(other),
    )

    assert response.status_code == 404


def test_get_job_detail_rejects_deleted_job(client, api_db_session):
    job = _create_job(api_db_session, "api_detail_deleted")
    job.status = JobStatus.DELETED
    api_db_session.commit()

    response = client.get(
        f"/api/jobs/{job.job_id}",
        headers=_auth_headers_for_job(api_db_session, job),
    )

    assert response.status_code == 404


def test_register_job_rejects_missing_dependency(client, api_db_session):
    owner = _create_default_job_owner(api_db_session)

    response = client.post(
        "/api/jobs/",
        json={
            "job_name": "Missing Dependency",
            "method": "GET",
            "endpoint": "http://test.com/missing-dependency",
            "schedule_type": "One-time",
            "depends_on": [9999],
        },
        headers=_auth_headers_for_user(owner),
    )

    assert response.status_code == 404


def test_register_job_rejects_dependency_owned_by_another_user(
    client,
    api_db_session,
):
    owner = _create_default_job_owner(api_db_session)
    other = crud.create_user(
        db=api_db_session,
        user_in=schemas.UserCreate(
            employee_id="api_dependency_other",
            username="ApiDependencyOther",
            role=UserRole.DEVELOPER,
        ),
    )
    other_job = crud.create_job(
        db=api_db_session,
        owner_id=other.user_id,
        job_in=schemas.JobCreate(
            job_name="Other Dependency",
            method=HttpMethod.GET,
            endpoint="http://test.com/other-dependency",
            schedule_type=ScheduleType.ONE_TIME,
        ),
    )

    response = client.post(
        "/api/jobs/",
        json={
            "job_name": "Cross Owner Dependency",
            "method": "GET",
            "endpoint": "http://test.com/cross-owner-dependency",
            "schedule_type": "One-time",
            "depends_on": [other_job.job_id],
        },
        headers=_auth_headers_for_user(owner),
    )

    assert response.status_code == 404


def test_manual_trigger_rejects_non_owner(client, api_db_session):
    job = _create_job(api_db_session, "api_owner_job")
    other = crud.create_user(
        db=api_db_session,
        user_in=schemas.UserCreate(
            employee_id="api_other_user",
            username="ApiOtherUser",
            role=UserRole.DEVELOPER,
        ),
    )

    response = client.post(
        f"/api/jobs/{job.job_id}/trigger",
        headers=_auth_headers_for_user(other),
    )

    assert response.status_code == 404


def test_manual_trigger_rejects_non_existent_job(client, api_db_session):
    user = _create_default_job_owner(api_db_session)

    response = client.post(
        "/api/jobs/9999/trigger",
        headers=_auth_headers_for_user(user),
    )

    assert response.status_code == 404


def test_manual_trigger_rejects_inactive_job(client, api_db_session):
    job = _create_job(api_db_session, "api_inactive_job")
    job.status = JobStatus.DISABLED
    api_db_session.commit()

    response = client.post(
        f"/api/jobs/{job.job_id}/trigger",
        headers=_auth_headers_for_job(api_db_session, job),
    )

    assert response.status_code == 409


def test_execution_history_rejects_non_owner(client, api_db_session):
    job = _create_job(api_db_session, "api_history_owner")
    _create_execution(api_db_session, job.job_id)
    other = crud.create_user(
        db=api_db_session,
        user_in=schemas.UserCreate(
            employee_id="api_history_other",
            username="ApiHistoryOther",
            role=UserRole.DEVELOPER,
        ),
    )

    response = client.get(
        f"/api/jobs/{job.job_id}/executions",
        headers=_auth_headers_for_user(other),
    )

    assert response.status_code == 404


def test_get_execution_rejects_non_owner(client, api_db_session):
    job = _create_job(api_db_session, "api_execution_owner")
    execution = _create_execution(api_db_session, job.job_id)
    other = crud.create_user(
        db=api_db_session,
        user_in=schemas.UserCreate(
            employee_id="api_execution_other",
            username="ApiExecutionOther",
            role=UserRole.DEVELOPER,
        ),
    )

    response = client.get(
        f"/api/executions/{execution.execution_id}",
        headers=_auth_headers_for_user(other),
    )

    assert response.status_code == 404


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


def test_get_execution_logs_execution_not_found(client, api_db_session):
    user = _create_default_job_owner(api_db_session)
    response = client.get(
        "/api/executions/9999/logs",
        headers=_auth_headers_for_user(user),
    )

    assert response.status_code == 404


def test_get_execution_logs_without_log_reference_returns_empty_logs(
    client,
    api_db_session,
):
    job = _create_job(api_db_session, "api_log_empty_list")
    execution = _create_execution(api_db_session, job.job_id)

    response = client.get(
        f"/api/executions/{execution.execution_id}/logs",
        headers=_auth_headers_for_job(api_db_session, job),
    )

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

    response = client.get(
        f"/api/executions/{execution.execution_id}/logs",
        headers=_auth_headers_for_job(api_db_session, job),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["execution_id"] == execution.execution_id
    assert body["logs"][0]["log_id"] == log_ref.log_id
    assert body["logs"][0]["execution_id"] == execution.execution_id
    assert body["logs"][0]["log_path"] == "/app/logs/executions/metadata.log"
    assert body["logs"][0]["log_size"] == 256
    assert body["logs"][0]["created_at"] is not None


def test_get_execution_logs_rejects_non_owner(client, api_db_session):
    job = _create_job(api_db_session, "api_log_meta_owner")
    execution = _create_execution(api_db_session, job.job_id)
    crud.create_log_reference(
        db=api_db_session,
        execution_id=execution.execution_id,
        log_path="/app/logs/executions/private.log",
        log_size=256,
    )
    other = crud.create_user(
        db=api_db_session,
        user_in=schemas.UserCreate(
            employee_id="api_log_meta_other",
            username="ApiLogMetadataOther",
            role=UserRole.DEVELOPER,
        ),
    )

    response = client.get(
        f"/api/executions/{execution.execution_id}/logs",
        headers=_auth_headers_for_user(other),
    )

    assert response.status_code == 404


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

    response = client.get(
        f"/api/executions/{execution.execution_id}/logs/content",
        headers=_auth_headers_for_job(api_db_session, job),
    )

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

    response = client.get(
        f"/api/executions/{execution.execution_id}/logs/content",
        headers=_auth_headers_for_job(api_db_session, job),
    )

    assert response.status_code == 404


def test_get_execution_log_content_rejects_non_owner(
    client,
    api_db_session,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(log_storage, "LOG_ROOT", str(tmp_path))
    job = _create_job(api_db_session, "api_log_text_owner")
    execution = _create_execution(api_db_session, job.job_id)
    log_path, log_size = log_storage.write_execution_log(
        execution.execution_id,
        "private worker output",
    )
    crud.create_log_reference(
        db=api_db_session,
        execution_id=execution.execution_id,
        log_path=log_path,
        log_size=log_size,
    )
    other = crud.create_user(
        db=api_db_session,
        user_in=schemas.UserCreate(
            employee_id="api_log_text_other",
            username="ApiLogContentOther",
            role=UserRole.DEVELOPER,
        ),
    )

    response = client.get(
        f"/api/executions/{execution.execution_id}/logs/content",
        headers=_auth_headers_for_user(other),
    )

    assert response.status_code == 404
