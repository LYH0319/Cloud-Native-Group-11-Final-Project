import os
from sqlalchemy import create_engine
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
                employee_id="admin_000", 
                username="System Admin",
                role=UserRole.ADMIN
            )
            
            db.add(default_admin)
            db.commit()
            print("✅ Default Admin user created successfully!")
            
    except Exception as e:
        print(f"❌ Error creating default admin: {e}")
        db.rollback()
    finally:
        db.close()