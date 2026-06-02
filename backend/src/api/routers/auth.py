from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import src.database.crud as crud
import src.database.schemas as schemas
from src.database.core import get_db
from src.utils.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


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
    if user_in.email and crud.get_user_by_email(db=db, email=user_in.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email already registered",
        )
    if crud.get_user_by_username(db=db, username=user_in.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="username already registered",
        )
    if crud.get_user_by_employee_id(db=db, employee_id=user_in.employee_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="employee_id already registered",
        )
    return crud.create_user(db=db, user_in=user_in)


@router.post("/login", response_model=schemas.TokenResponse)
def login_user(
    login_in: schemas.UserLogin,
    db: Session = Depends(get_db),
):
    """Authenticate a user and return a JWT access token."""
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
    return {
        "access_token": create_access_token(subject=str(user.user_id)),
        "token_type": "bearer",
        "user": user,
    }
