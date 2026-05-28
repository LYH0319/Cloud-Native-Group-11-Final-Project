from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Enum, func
from typing import List, Optional
from database import Base
import enum
from datetime import datetime

class UserRole(enum.Enum):
    DEVELOPER = "Developer"
    OPERATOR = "Operator"

class User(Base):
    __tablename__ = "users"
    
    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(unique=True)
    username: Mapped[str] = mapped_column(String(30))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.DEVELOPER)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

