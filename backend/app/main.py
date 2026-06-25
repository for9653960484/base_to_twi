from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
import app.models  # noqa: F401 — register SQLAlchemy mappers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init connections, etc.
    yield
    # Shutdown: close connections


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="API управления базой знаний по техобслуживанию парка оборудования",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.API_PREFIX)

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "backend"}

    return app


app = create_app()
