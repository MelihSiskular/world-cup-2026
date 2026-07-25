"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import replace
from pathlib import Path
from typing import Protocol

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from wc26 import __version__
from wc26.analytics.transfer_intelligence.catalog import (
    TransferDataCatalog,
)
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
from wc26.api.settings import (
    ApiSettings,
    TransferDatasetPaths,
)


class TransferDataCatalogLoader(Protocol):
    """Callable contract for loading runtime datasets."""

    def __call__(
        self,
        *,
        features: Path,
        similarity: Path,
        heatmap_similarity: Path,
        heatmap_profiles: Path,
    ) -> TransferDataCatalog:
        """Load and return the runtime catalog."""


def create_app(
    *,
    settings: ApiSettings | None = None,
    dataset_paths: TransferDatasetPaths | None = None,
    catalog_loader: TransferDataCatalogLoader | None = None,
) -> FastAPI:
    """Create and configure the WC26 FastAPI application."""

    runtime_settings = settings if settings is not None else ApiSettings()

    if dataset_paths is not None:
        runtime_settings = replace(
            runtime_settings,
            dataset_paths=dataset_paths,
        )

    runtime_paths = runtime_settings.dataset_paths

    @asynccontextmanager
    async def lifespan(
        application: FastAPI,
    ) -> AsyncIterator[None]:
        """Load and release application runtime data."""

        catalog_loaded = False

        if catalog_loader is not None:
            application.state.transfer_data_catalog = catalog_loader(
                features=runtime_paths.features,
                similarity=runtime_paths.similarity,
                heatmap_similarity=(runtime_paths.heatmap_similarity),
                heatmap_profiles=(runtime_paths.heatmap_profiles),
            )
            catalog_loaded = True

        try:
            yield
        finally:
            if catalog_loaded:
                delattr(
                    application.state,
                    "transfer_data_catalog",
                )

    application = FastAPI(
        title=runtime_settings.title,
        summary=runtime_settings.summary,
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    if runtime_settings.cors_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=list(runtime_settings.cors_origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    application.state.api_settings = runtime_settings
    application.state.transfer_dataset_paths = runtime_paths

    application.include_router(health_router)
    application.include_router(players_router)
    application.include_router(transfer_intelligence_router)

    register_exception_handlers(application)

    return application


__all__ = [
    "TransferDataCatalogLoader",
    "create_app",
]
