import json
from pathlib import Path
from typing import Any, Generator

import pytest
from testcontainers.community.postgres import PostgresContainer
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

FIXTURES_DIR = (
    Path(__file__).parent.parent
    / "changes"
    / "CR-26j001-bank-cashflow-ingestion"
    / "fixtures"
)


@pytest.fixture
def valid_movement_payload() -> dict[str, Any]:
    with open(FIXTURES_DIR / "valid_movement_event.json") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def db_engine(postgres_container: PostgresContainer):
    connection_url = postgres_container.get_connection_url()
    engine = create_engine(connection_url)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    connection = db_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = session_factory()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
