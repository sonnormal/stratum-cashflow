from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class TransactionType(StrEnum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class MovementStatus(StrEnum):
    RECORDED = "RECORDED"
    DUPLICATE_IGNORED = "DUPLICATE_IGNORED"


class AccountMovement(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: str
    occurred_at: datetime
    bank_code: str
    account_number_mask: str | None = None
    transaction_type: TransactionType
    amount: Decimal
    currency: str = "VND"
    description: str | None = None
    counterparty: str | None = None
    category: str | None = None
    raw_source_ref: str
    remaining_balance: Decimal | None = None

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be strictly positive")
        return v

    @classmethod
    def from_contract(cls, data: dict[str, Any]) -> "AccountMovement":
        # Defensive amount coercion to Decimal
        raw_amount = data["amount"]
        if isinstance(raw_amount, (int, float, str)):
            decimal_amount = Decimal(str(raw_amount))
        else:
            decimal_amount = raw_amount

        occurred_raw = data["occurred_at"]
        if isinstance(occurred_raw, str):
            occurred_at = datetime.fromisoformat(occurred_raw.replace("Z", "+00:00"))
        else:
            occurred_at = occurred_raw

        return cls(
            event_id=str(data["event_id"]),
            occurred_at=occurred_at,
            bank_code=str(data["bank_code"]),
            account_number_mask=data.get("account_number_mask"),
            transaction_type=TransactionType(data["transaction_type"]),
            amount=decimal_amount,
            currency=str(data.get("currency", "VND")),
            description=data.get("description"),
            counterparty=data.get("counterparty"),
            category=data.get("category"),
            raw_source_ref=str(data["raw_source_ref"]),
            remaining_balance=(
                Decimal(str(data["remaining_balance"]))
                if data.get("remaining_balance") is not None
                else None
            ),
        )


class MovementResult(BaseModel):
    status: MovementStatus
    movement_id: str | None = None
