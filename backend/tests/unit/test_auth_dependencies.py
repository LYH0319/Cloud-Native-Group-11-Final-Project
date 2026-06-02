import pytest
from fastapi import HTTPException

from src.api.dependencies import get_current_user
from src.database import crud, schemas
from src.database.models import UserRole
from src.utils.security import create_access_token

pytestmark = [pytest.mark.unit, pytest.mark.auth]


def _create_dependency_user(db_session):
    return crud.create_user(
        db=db_session,
        user_in=schemas.UserCreate(
            employee_id="dependency_user",
            username="DependencyUser",
            role=UserRole.DEVELOPER,
            email="dependency-user@example.com",
            password="secret123",
        ),
    )


def test_get_current_user_returns_active_user(db_session):
    user = _create_dependency_user(db_session)
    token = create_access_token(subject=str(user.user_id))

    current_user = get_current_user(token=token, db=db_session)

    assert current_user.user_id == user.user_id


def test_get_current_user_rejects_invalid_token(db_session):
    with pytest.raises(HTTPException) as error:
        get_current_user(token="not-a-valid-token", db=db_session)

    assert error.value.status_code == 401


def test_get_current_user_rejects_non_integer_subject(db_session):
    token = create_access_token(subject="not-an-int")

    with pytest.raises(HTTPException) as error:
        get_current_user(token=token, db=db_session)

    assert error.value.status_code == 401


def test_get_current_user_rejects_missing_user(db_session):
    token = create_access_token(subject="9999")

    with pytest.raises(HTTPException) as error:
        get_current_user(token=token, db=db_session)

    assert error.value.status_code == 401


def test_get_current_user_rejects_inactive_user(db_session):
    user = _create_dependency_user(db_session)
    crud.delete_user(db=db_session, user_id=user.user_id)
    token = create_access_token(subject=str(user.user_id))

    with pytest.raises(HTTPException) as error:
        get_current_user(token=token, db=db_session)

    assert error.value.status_code == 401
