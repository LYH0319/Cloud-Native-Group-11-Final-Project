import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from src.database.connection import Base
from typing import Generator


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
