import os

from fastapi import FastAPI
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker

from cashflow.api.routes import router


def create_app(engine: Engine | None = None) -> FastAPI:
    app = FastAPI(title="Stratum Cashflow Service", version="0.1.0")

    if engine is None:
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/cashflow",
        )
        engine = create_engine(database_url)

    app.state.engine = engine
    app.state.session_factory = sessionmaker(bind=engine)

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(router)
    return app
