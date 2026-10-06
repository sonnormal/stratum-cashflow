import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from cashflow.db.models import AccountMovementORM
from cashflow.domain.models import AccountMovement, TransactionType


class PostgresMovementRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def save_movement(self, movement: AccountMovement) -> tuple[bool, str | None]:
        stmt: Any = (
            insert(AccountMovementORM)
            .values(
                event_id=uuid.UUID(movement.event_id),
                occurred_at=movement.occurred_at,
                bank_code=movement.bank_code,
                account_number_mask=movement.account_number_mask,
                transaction_type=movement.transaction_type.value,
                amount=movement.amount,
                currency=movement.currency,
                description=movement.description,
                counterparty=movement.counterparty,
                category=movement.category,
                raw_source_ref=movement.raw_source_ref,
            )
            .on_conflict_do_nothing(index_elements=["bank_code", "raw_source_ref"])
            .returning(AccountMovementORM.id)
        )
        result = self.session.execute(stmt)
        row = result.fetchone()
        self.session.commit()

        if row is not None:
            return True, str(row[0])
        return False, None

    def get_by_id(self, movement_id: str) -> AccountMovement | None:
        record = (
            self.session.query(AccountMovementORM)
            .filter(AccountMovementORM.id == uuid.UUID(movement_id))
            .first()
        )
        if not record:
            return None

        return AccountMovement(
            event_id=str(record.event_id),
            occurred_at=record.occurred_at,
            bank_code=str(record.bank_code),
            account_number_mask=record.account_number_mask,
            transaction_type=TransactionType(str(record.transaction_type)),
            amount=Decimal(str(record.amount)),
            currency=str(record.currency),
            description=record.description,
            counterparty=record.counterparty,
            category=record.category,
            raw_source_ref=str(record.raw_source_ref),
            remaining_balance=None,
        )
