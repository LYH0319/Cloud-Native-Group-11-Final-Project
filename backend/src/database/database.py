import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(".env.local"))

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if SQLALCHEMY_DATABASE_URL is None:
    raise ValueError("Database URL is not set. Please check your .env file.")

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, echo=True)

# create sessionmaker
SessionLocal = sessionmaker(engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(engine)
    print("Initialized database tables!")