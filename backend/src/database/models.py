from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Boolean, JSON, Enum, func, ForeignKey
from typing import List, Optional, Dict, Any
from database import Base
import enum
from datetime import datetime

class UserRole(enum.Enum):
    DEVELOPER = "Developer"
    OPERATOR = "Operator"

class HttpMethod(enum.Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"

class JobStatus(enum.Enum):
    ACTIVE = "Active"
    DISABLED = "Disabled"
    DELETED = "Deleted"

class ScheduleType(enum.Enum):
    ONE_TIME = "One-time"
    RECURRING = "Recurring"

class TriggerType(enum.Enum):
    SCHEDULER = "Scheduler"
    MANUAL = "Manual"

class ExecutionStatus(enum.Enum):
    PENDING = "Pending"      # 排隊中
    RUNNING = "Running"      # 執行中
    SUCCESS = "Success"      # 成功
    FAILED = "Failed"        # 失敗
    TIMEOUT = "Timeout"      # 超時
    CANCELLED = "Cancelled"  # 已取消

class User(Base):
    __tablename__ = "users"
    
    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    employee_id: Mapped[str] = mapped_column(String(20), unique=True)
    username: Mapped[str] = mapped_column(String(30))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.DEVELOPER)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    
    jobs: Mapped[List["Job"]] = relationship(back_populates="owner")
    # jobs: Mapped[List["Job"]] = relationship(back_populates="owner", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, username='{self.username!r}', role='{self.role.name!r}')>"

class Job(Base):
    __tablename__ = "jobs"
    
    job_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    job_name: Mapped[str] = mapped_column(String(30))
    method: Mapped[HttpMethod] = mapped_column(Enum(HttpMethod))
    endpoint: Mapped[str] = mapped_column(String(2048))
    
    headers: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    body: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus))

    has_dependency: Mapped[bool] = mapped_column(Boolean, default=False)
    schedule_type: Mapped[ScheduleType] = mapped_column(Enum(ScheduleType))
    cron_expression: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    
    owner: Mapped["User"] = relationship(back_populates="jobs")
    
    # I am waiting who
    upstream_dependencies: Mapped[List["JobDependency"]] = relationship(
        foreign_keys="[JobDependency.downstream_id]",
        back_populates="downstream_job",
        cascade="all, delete-orphan"
    )

    # who is waiting for me
    downstream_dependencies: Mapped[List["JobDependency"]] = relationship(
        foreign_keys="[JobDependency.upstream_id]",
        back_populates="upstream_job",
        cascade="all, delete-orphan"
    )
    
    executions: Mapped[List["Execution"]] = relationship(back_populates="job", cascade="all, delete-orphan")
    
    
    def __repr__(self) -> str:
        return f"<Job(job_id={self.job_id}, owner_id={self.owner_id}, name='{self.job_name!r}', status='{self.status.name!r}')>"

class JobDependency(Base):
    __tablename__ = "job_dependencies"
    
    dependency_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    upstream_id: Mapped[int] = mapped_column(ForeignKey("jobs.job_id"))   # depend_on_job_id
    downstream_id: Mapped[int] = mapped_column(ForeignKey("jobs.job_id")) # job_id
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    upstream_job: Mapped["Job"] = relationship(
        foreign_keys=[upstream_id], 
        back_populates="downstream_dependencies"
    )
    downstream_job: Mapped["Job"] = relationship(
        foreign_keys=[downstream_id], 
        back_populates="upstream_dependencies"
    )
    
    def __repr__(self) -> str:
        return f"<Dependency(upstream={self.upstream_id} -> downstream={self.downstream_id})>"
    
class Execution(Base):
    __tablename__ = "executions"
    
    execution_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.job_id"))
    
    trigger_type: Mapped[TriggerType] = mapped_column(Enum(TriggerType), default=TriggerType.SCHEDULER)
    status: Mapped[ExecutionStatus] = mapped_column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING)
    
    # 執行時間細節 (剛建立時還沒跑完，所以 end_time 和 duration 允許為 NULL)
    start_time: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    duration: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 單位：秒
    
    # 分散式架構設計
    worker_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # 哪台機器跑的
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 失敗分析
    error_message: Mapped[Optional[str]] = mapped_column(String(4000), nullable=True) # 錯誤訊息可能很長
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # --- 關聯設定 ---
    job: Mapped["Job"] = relationship(back_populates="executions")
    log_reference: Mapped[Optional["LogReference"]] = relationship(
        back_populates="execution", 
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Execution(id={self.execution_id}, job_id={self.job_id}, status='{self.status.name}', retry={self.retry_count})>"


class LogReference(Base):
    __tablename__ = "log_references"
    
    log_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    execution_id: Mapped[int] = mapped_column(ForeignKey("executions.execution_id"))
    
    log_path:Mapped[str] = mapped_column(String(1024))
    log_size:Mapped[int] = mapped_column(Integer)
    
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    execution: Mapped["Execution"] = relationship(back_populates="log_reference")