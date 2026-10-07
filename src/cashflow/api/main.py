import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker

from cashflow.api.routes import router
from cashflow.db.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if hasattr(app.state, "engine") and app.state.engine:
        Base.metadata.create_all(app.state.engine)
    yield


def create_app(engine: Engine | None = None) -> FastAPI:
    app = FastAPI(title="Stratum Cashflow Service", version="0.1.0", lifespan=lifespan)

    if engine is None:
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://postgres:postgres@localhost:5432/cashflow",
        )
        engine = create_engine(database_url)

    app.state.engine = engine
    app.state.session_factory = sessionmaker(bind=engine)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(router)
    return app
