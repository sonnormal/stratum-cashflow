from collections.abc import Generator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from cashflow.db.repository import PostgresMovementRepository
from cashflow.domain.models import AccountMovement, MovementStatus
from cashflow.domain.service import CashflowService

router = APIRouter(prefix="/api/v1")


def get_db(request: Request) -> Generator[Session, None, None]:
    session_factory = request.app.state.session_factory
    session: Session = session_factory()
    try:
        yield session
    finally:
        session.close()


@router.post("/movements")
async def record_movement(
    payload: dict[str, Any],
    db: Annotated[Session, Depends(get_db)],
) -> JSONResponse:
    try:
        movement = AccountMovement.from_contract(payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e

    repo = PostgresMovementRepository(session=db)
    service = CashflowService(repository=repo)
    result = service.record_movement(movement)

    if result.status == MovementStatus.RECORDED:
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"status": "RECORDED", "movement_id": result.movement_id},
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "DUPLICATE_IGNORED"},
    )
