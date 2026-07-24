"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from wc26 import __version__
from wc26.api.exception_handlers import (
    register_exception_handlers,
)
from wc26.api.routes.health import router as health_router
from wc26.api.routes.players import (
    router as players_router,
)
from wc26.api.routes.transfer_intelligence import (
    router as transfer_intelligence_router,
)


def create_app() -> FastAPI:
    """Create and configure the WC26 FastAPI application."""

    application = FastAPI(
        title="WC26 Transfer Intelligence API",
        summary=("Football recruitment intelligence powered by World Cup data."),
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    application.include_router(health_router)
    application.include_router(players_router)
    application.include_router(transfer_intelligence_router)

    register_exception_handlers(application)

    return application


__all__ = [
    "create_app",
]
