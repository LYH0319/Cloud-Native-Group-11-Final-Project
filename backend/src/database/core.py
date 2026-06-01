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
    print("Initialized database tables!")

    from sqlalchemy import select
    from models import User, UserRole

    # 拿取連線
    db = SessionLocal()
    try:
        # 檢查資料庫裡是不是已經有 ADMIN 存在了
        admin_exists = db.scalar(select(User).where(User.role == UserRole.ADMIN))

        if not admin_exists:
            print("No Admin found. Creating default Admin user...")

            # 建立預設的超級管理員 (你可以跟組員討論預設的員編要叫什麼)
            default_admin = User(
                employee_id="admin_000", username="System Admin", role=UserRole.ADMIN
            )

            db.add(default_admin)
            db.commit()
            print("✅ Default Admin user created successfully!")

    except Exception as e:
        print(f"❌ Error creating default admin: {e}")
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

    existing_columns = {
        column["name"] for column in inspector.get_columns("users")
    }
    statements = []
    if "email" not in existing_columns:
        statements.append("ALTER TABLE users ADD COLUMN email VARCHAR(255) NULL")
    if "hashed_password" not in existing_columns:
        statements.append(
            "ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255) NULL"
        )

    if not statements:
        return

    with target_engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
