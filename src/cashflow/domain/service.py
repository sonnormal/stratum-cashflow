from typing import Any, Protocol

from cashflow.domain.models import AccountMovement, MovementResult, MovementStatus


class MovementRepository(Protocol):
    def save_movement(self, movement: AccountMovement) -> tuple[bool, str | None]: ...


class CashflowService:
    def __init__(self, repository: Any) -> None:
        self.repository = repository

    def record_movement(self, movement: AccountMovement) -> MovementResult:
        is_new, movement_id = self.repository.save_movement(movement)
        if is_new:
            return MovementResult(status=MovementStatus.RECORDED, movement_id=movement_id)
        return MovementResult(status=MovementStatus.DUPLICATE_IGNORED, movement_id=None)
