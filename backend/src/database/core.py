import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, MappedAsDataclass
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(".env.local"))

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if SQLALCHEMY_DATABASE_URL is None:
    raise ValueError("Database URL is not set. Please check your .env file.")

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, echo=True)

# create sessionmaker
SessionLocal = sessionmaker(engine)


class Base(MappedAsDataclass, DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        print(f"Database excetion: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(engine)
    ensure_schema_compatibility(engine)
    ensure_default_admin()
    print("Initialized database tables!")


def ensure_default_admin() -> None:
    """Ensure the built-in admin/admin account exists after DB startup."""
    from src.database.models import User, UserRole
    from src.utils.security import hash_password

    db = SessionLocal()
    try:
        admin = db.scalar(
            text("SELECT user_id FROM users WHERE employee_id = :employee_id"),
            {"employee_id": "admin"},
        )
        hashed_password = hash_password("admin")
        if admin is None:
            default_admin = User(
                employee_id="admin",
                username="Admin",
                role=UserRole.ADMIN,
                hashed_password=hashed_password,
            )
            db.add(default_admin)
        else:
            user = db.get(User, admin)
            if user is not None:
                user.username = "Admin"
                user.role = UserRole.ADMIN
                user.hashed_password = hashed_password
                user.is_active = True
        db.commit()
    except Exception as error:
        print(f"Error creating default admin: {error}")
        db.rollback()
    finally:
        db.close()


def ensure_schema_compatibility(bind_engine=None) -> None:
    """
    Apply tiny compatibility fixes for local databases created before auth fields.

    This project does not currently use Alembic. create_all() creates missing tables,
    but it does not add columns to tables that already exist in a Docker volume.
    """
    target_engine = bind_engine or engine
    inspector = inspect(target_engine)

    if not inspector.has_table("users"):
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    statements = []
    if "email" not in existing_columns:
        statements.append("ALTER TABLE users ADD COLUMN email VARCHAR(255) NULL")
    if "hashed_password" not in existing_columns:
        statements.append(
            "ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255) NULL"
        )

    if inspector.has_table("executions"):
        execution_columns = {
            column["name"] for column in inspector.get_columns("executions")
        }
        if "last_heartbeat" not in execution_columns:
            statements.append("ALTER TABLE executions ADD COLUMN last_heartbeat DATETIME NULL")

    if not statements:
        return

    with target_engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
