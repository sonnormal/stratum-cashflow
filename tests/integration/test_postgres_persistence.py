from decimal import Decimal
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from cashflow.api.main import create_app
from cashflow.db.models import Base
from cashflow.db.repository import PostgresMovementRepository
from cashflow.domain.models import AccountMovement, TransactionType


def test_postgres_table_creation_and_insert(
    db_engine, db_session: Session, valid_movement_payload: dict
) -> None:
    Base.metadata.create_all(db_engine)
    repo = PostgresMovementRepository(session=db_session)

    movement = AccountMovement.from_contract(valid_movement_payload)
    is_new, movement_id = repo.save_movement(movement)

    assert is_new is True
    assert movement_id is not None

    retrieved = repo.get_by_id(movement_id)
    assert retrieved is not None
    assert retrieved.bank_code == "VIB"
    assert retrieved.amount == Decimal("75000.00")
    assert retrieved.counterparty == "Highlands Coffee"
    assert retrieved.category == "Food & Beverage"


def test_postgres_atomic_unique_constraint_idempotency(
    db_engine, db_session: Session, valid_movement_payload: dict
) -> None:
    Base.metadata.create_all(db_engine)
    repo = PostgresMovementRepository(session=db_session)

    movement = AccountMovement.from_contract(valid_movement_payload)

    # First insert
    is_new_1, id_1 = repo.save_movement(movement)
    assert is_new_1 is True
    assert id_1 is not None

    # Second insert with identical bank_code and raw_source_ref
    is_new_2, id_2 = repo.save_movement(movement)
    assert is_new_2 is False
    assert id_2 is None


def test_api_post_movement_end_to_end_in_container(
    db_engine, valid_movement_payload: dict
) -> None:
    Base.metadata.create_all(db_engine)
    app = create_app(engine=db_engine)
    client = TestClient(app)

    # First call: Should create movement
    response_1 = client.post("/api/v1/movements", json=valid_movement_payload)
    assert response_1.status_code == 201
    data_1 = response_1.json()
    assert data_1["status"] == "RECORDED"
    assert "movement_id" in data_1

    # Second call: Duplicate should be ignored cleanly
    response_2 = client.post("/api/v1/movements", json=valid_movement_payload)
    assert response_2.status_code == 200
    data_2 = response_2.json()
    assert data_2["status"] == "DUPLICATE_IGNORED"
