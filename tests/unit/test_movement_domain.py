from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock

import pytest

from cashflow.domain.models import (
    AccountMovement,
    MovementResult,
    MovementStatus,
    TransactionType,
)
from cashflow.domain.service import CashflowService


def test_valid_movement_domain_validation(valid_movement_payload: dict[str, Any]) -> None:
    movement = AccountMovement.from_contract(valid_movement_payload)

    assert movement.event_id == valid_movement_payload["event_id"]
    assert movement.bank_code == "VIB"
    assert movement.transaction_type == TransactionType.DEBIT
    assert movement.amount == Decimal("75000.00")
    assert movement.currency == "VND"
    assert movement.counterparty == "Highlands Coffee"
    assert movement.category == "Food & Beverage"
    assert movement.raw_source_ref == valid_movement_payload["raw_source_ref"]


@pytest.mark.parametrize("invalid_amount", [0, -1000, -0.01])
def test_negative_or_zero_amount_rejection(
    valid_movement_payload: dict[str, Any], invalid_amount: float
) -> None:
    payload = valid_movement_payload.copy()
    payload["amount"] = invalid_amount

    with pytest.raises(ValueError, match="Amount must be strictly positive"):
        AccountMovement.from_contract(payload)


def test_service_idempotent_duplicate_handling(valid_movement_payload: dict[str, Any]) -> None:
    movement = AccountMovement.from_contract(valid_movement_payload)

    mock_repo = MagicMock()
    mock_repo.save_movement.return_value = (False, None)  # Duplicate, not saved

    service = CashflowService(repository=mock_repo)
    result: MovementResult = service.record_movement(movement)

    assert result.status == MovementStatus.DUPLICATE_IGNORED
    assert result.movement_id is None
    mock_repo.save_movement.assert_called_once_with(movement)


def test_service_new_movement_success(valid_movement_payload: dict[str, Any]) -> None:
    movement = AccountMovement.from_contract(valid_movement_payload)

    mock_repo = MagicMock()
    mock_repo.save_movement.return_value = (True, movement.event_id)

    service = CashflowService(repository=mock_repo)
    result: MovementResult = service.record_movement(movement)

    assert result.status == MovementStatus.RECORDED
    assert result.movement_id == movement.event_id
    mock_repo.save_movement.assert_called_once_with(movement)
