import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from typing import Generator

# 1. Set the environment variable FIRST, before any other app modules are imported.
# This ensures that when config/settings are loaded, they read the test DB URL.
os.environ.setdefault("DATABASE_URL", "sqlite://")

# 2. Import Base AFTER setting the environment variable.
from src.database.connection import Base 

@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """
    Creates an isolated, in-memory SQLite database session for testing.

    This fixture sets up all database tables before a test runs,
    yields the session for testing, and automatically cleans up
    (drops all tables and closes the connection) after the test completes.
    """
    # create engine
    engine_url = "sqlite://"
    engine = create_engine(engine_url)

    # create table
    Base.metadata.create_all(engine)

    # yield session
    with sessionmaker(bind=engine)() as session:
        yield session

    # clean up
    Base.metadata.drop_all(engine)