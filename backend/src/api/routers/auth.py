from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user
import src.database.crud as crud
import src.database.schemas as schemas
from src.database.core import get_db
from src.database.models import User
from src.utils.security import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token

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


def _ensure_unique_user_fields(db: Session, user_in: schemas.UserCreate) -> None:
    if user_in.email and crud.get_user_by_email(db=db, email=user_in.email):
        raise _conflict("email already registered")
    if crud.get_user_by_username(db=db, username=user_in.username):
        raise _conflict("username already registered")
    if crud.get_user_by_employee_id(db=db, employee_id=user_in.employee_id):
        raise _conflict("employee_id already registered")


@router.post(
    "/register",
    response_model=schemas.UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_db),
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
    db: Session = Depends(get_db),
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


@router.get("/me", response_model=schemas.UserRead)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's public profile."""
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_user(_: User = Depends(get_current_user)):
    """Validate the current token and let clients discard it."""
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
