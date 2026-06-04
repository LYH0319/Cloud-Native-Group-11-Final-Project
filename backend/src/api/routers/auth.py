import os
from datetime import timedelta
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import Annotated

from src.api.dependencies import get_current_user
import src.database.crud as crud
import src.database.schemas as schemas
from src.database.core import get_db
from src.database.models import User, UserRole
from src.utils.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    decode_access_token,
    hash_password,
)
from src.utils.email import send_password_reset_email

ERROR_USER_NOT_FOUND = "Can not find ID"
ERROR_ACCOUNT_NOT_FOUND = "User not found"


router = APIRouter(prefix="/auth", tags=["Auth"])


def _conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def _build_token_response(user: User) -> dict:
    return {
        "access_token": create_access_token(subject=str(user.user_id)),
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": user,
    }


def _build_reset_link(token: str) -> str:
    base_url = os.getenv("RESET_PASSWORD_BASE_URL", "http://localhost:3000")
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}reset_token={token}"


def _require_admin(current_user: User) -> None:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required",
        )


def _ensure_unique_user_fields(
    db: Session,
    user_in: schemas.UserCreate,
) -> None:
    if user_in.email and crud.get_user_by_email(db=db, email=user_in.email):
        raise _conflict("email already registered")
    if crud.get_user_by_username(db=db, username=user_in.username):
        raise _conflict("username already registered")
    existing_employee = crud.get_user_by_employee_id(
        db=db,
        employee_id=user_in.employee_id,
    )
    if existing_employee:
        raise _conflict("employee_id already registered")


@router.post(
    "/register",
    response_model=schemas.UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_in: schemas.UserCreate,
    db: Annotated[Session, Depends(get_db)] = None,                  
):
    """Register a user with a hashed password."""
    if not user_in.password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="password is required",
        )
    _ensure_unique_user_fields(db=db, user_in=user_in)
    try:
        return crud.create_user(db=db, user_in=user_in)
    except IntegrityError as error:
        db.rollback()
        raise _conflict("user already registered") from error


@router.post("/login", response_model=schemas.TokenResponse)
async def login_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)] = None,                  
):
    """Authenticate a user and return a JWT access token.

    Accepts JSON payloads using `identifier` plus `password`, or
    `application/x-www-form-urlencoded` payloads using OAuth2-style
    `username` plus `password`.
    """
    login_in = await _login_from_request(request)
    user = crud.authenticate_user(
        db=db,
        identifier=login_in.identifier,
        password=login_in.password,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _build_token_response(user)


@router.post("/check-id")
def check_id(request: schemas.CheckIdRequest, db: Annotated[Session, Depends(get_db)]):
    """Check whether an employee ID exists and already has a password."""
    user = crud.get_user_by_employee_id(db=db, employee_id=request.employee_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_USER_NOT_FOUND,
        )
    return {"isRegistered": bool(user.hashed_password)}


@router.post("/register-password")
def register_password(
    request: schemas.PasswordRequest,
    db: Annotated[Session, Depends(get_db)] = None,                  
):
    """Set the initial password for a pre-created employee account."""
    user = crud.get_user_by_employee_id(db=db, employee_id=request.employee_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_USER_NOT_FOUND,
        )
    if user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password already registered",
        )

    user.hashed_password = hash_password(request.password)
    db.commit()
    return {"message": "Password registered successfully"}


@router.post("/login-password", response_model=schemas.TokenResponse)
def login_password(
    request: schemas.PasswordRequest,
    db: Annotated[Session, Depends(get_db)] = None,                  
):
    """Authenticate the frontend employee-ID password flow and return a JWT."""
    user = crud.authenticate_user(
        db=db,
        identifier=request.employee_id,
        password=request.password,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _build_token_response(user)


@router.post("/forgot-password", response_model=schemas.ForgotPasswordResponse)
def forgot_password(
    request: schemas.ForgotPasswordRequest,
    db: Annotated[Session, Depends(get_db)] = None,
):
    """Start password reset by emailing a short-lived reset token."""
    user = crud.get_user_by_employee_id(db=db, employee_id=request.employee_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_USER_NOT_FOUND,
        )

    if not user.email:
        return {
            "status": "missing_email",
            "message": "此帳號未綁定 email，請聯絡管理員重設密碼",
        }

    token = create_access_token(
        subject=str(user.user_id),
        expires_delta=timedelta(minutes=30),
        extra_claims={"purpose": "password_reset"},
    )
    try:
        send_password_reset_email(user.email, _build_reset_link(token))
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="SMTP email delivery failed. Please check SMTP_USERNAME and SMTP_PASSWORD.",
        ) from error
    return {
        "status": "sent",
        "message": "密碼重設連結已寄到帳號綁定的 email",
    }


@router.post("/reset-password")
def reset_password_with_token(
    request: schemas.TokenResetPasswordRequest,
    db: Annotated[Session, Depends(get_db)] = None,
):
    """Reset a password with a valid email reset token."""
    try:
        payload = decode_access_token(request.token)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        ) from error

    if payload.get("purpose") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    user = crud.get_user_by_user_id(db=db, user_id=int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_ACCOUNT_NOT_FOUND,
        )

    user.hashed_password = hash_password(request.new_password)
    db.commit()
    return {
        "message": "Password reset successfully",
        "employee_id": user.employee_id,
    }


@router.patch("/users/{user_id}/password")
def admin_reset_user_password(
    user_id: int,
    request: schemas.AdminResetPasswordRequest,
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """Allow admins to reset a user's password from the admin page."""
    _require_admin(current_user)
    user = crud.get_user_by_user_id(db=db, user_id=user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_ACCOUNT_NOT_FOUND,
        )

    user.hashed_password = hash_password(request.new_password)
    db.commit()
    return {"message": "Password reset successfully"}


@router.get("/me", response_model=schemas.UserRead)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's public profile."""
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_user(_: User = Depends(get_current_user)):
    """Validate the current token and let clients discard it."""
    return None


@router.get("/users", response_model=list[schemas.UserRead])
def list_users(
    db: Annotated[Session, Depends(get_db)] = None,                  
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """List active users for the admin account management page."""
    _require_admin(current_user)
    return crud.get_users(db=db)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Annotated[Session, Depends(get_db)] = None,                  
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """Soft delete a user account from the admin account management page."""
    _require_admin(current_user)
    user = crud.get_user_by_user_id(db=db, user_id=user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_ACCOUNT_NOT_FOUND,
        )
    if user.user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete current user",
        )
    if user.employee_id == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete builtin admin",
        )

    crud.delete_user(db=db, user_id=user_id)
    return None


async def _login_from_request(request: Request) -> schemas.UserLogin:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            payload = await request.json()
            return schemas.UserLogin.model_validate(payload)
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="invalid login payload",
            ) from error

    if "application/x-www-form-urlencoded" not in content_type:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="login payload is required",
        )

    body = (await request.body()).decode("utf-8")
    form = parse_qs(body, keep_blank_values=True)
    identifier = _first_form_value(form, "username") or _first_form_value(
        form, "identifier"
    )
    password = _first_form_value(form, "password")
    if identifier is None or password is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="username and password are required",
        )
    return schemas.UserLogin(identifier=identifier, password=password)


def _first_form_value(form: dict[str, list[str]], key: str) -> str | None:
    values = form.get(key)
    if not values:
        return None
    return values[0]
