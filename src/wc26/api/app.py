"""FastAPI application factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import replace
from pathlib import Path
from time import perf_counter
from typing import Protocol

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from wc26 import __version__
from wc26.analytics.transfer_intelligence.catalog import (
    TransferDataCatalog,
)
from wc26.api.deployment import (
    DeploymentIdentity,
    resolve_deployment_identity,
)
from wc26.api.exception_handlers import (
    register_exception_handlers,
)
from wc26.api.request_context import (
    REQUEST_ID_HEADER,
    RequestObservabilityMiddleware,
)
from wc26.api.routes.deployment import router as deployment_router
from wc26.api.routes.health import router as health_router
from wc26.api.routes.players import (
    router as players_router,
)
from wc26.api.routes.transfer_intelligence import (
    router as transfer_intelligence_router,
)
from wc26.api.runtime import ApiRuntimeState
from wc26.api.settings import (
    ApiSettings,
    TransferDatasetPaths,
)

logger = logging.getLogger("wc26.api.lifecycle")


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


def _elapsed_ms(
    started_at: float,
) -> float:
    """Return elapsed monotonic time in milliseconds."""

    return round(
        (perf_counter() - started_at) * 1000,
        3,
    )


def _deployment_log_fields(
    settings: ApiSettings,
    identity: DeploymentIdentity,
) -> dict[str, object]:
    """Return shared application deployment log fields."""

    return {
        "service": settings.service_name,
        "version": __version__,
        "environment": settings.environment,
        "provider": identity.provider,
        "commit_sha": identity.commit_sha,
        "branch": identity.branch,
        "deployment_id": identity.deployment_id,
        "dataset_bundle_sha256": (identity.dataset_bundle_sha256),
    }


def _catalog_row_counts(
    catalog: TransferDataCatalog,
) -> dict[str, int]:
    """Return observable runtime catalog row counts."""

    return {
        "players_rows": len(catalog.players),
        "similarity_rows": len(catalog.similarity),
        "heatmap_similarity_rows": len(catalog.heatmap_similarity),
        "heatmap_profiles_rows": len(catalog.heatmap_profiles),
    }


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

    runtime = ApiRuntimeState(
        settings=runtime_settings,
    )

    @asynccontextmanager
    async def lifespan(
        application: FastAPI,
    ) -> AsyncIterator[None]:
        """Manage application runtime data and lifecycle logs."""

        del application

        startup_started_at = perf_counter()

        runtime.mark_started()

        identity = resolve_deployment_identity()
        deployment_fields = _deployment_log_fields(
            runtime.settings,
            identity,
        )

        logger.info(
            "WC26 API starting",
            extra={
                "event": "api.starting",
                **deployment_fields,
            },
        )

        try:
            if catalog_loader is not None:
                catalog_started_at = perf_counter()

                logger.info(
                    "Transfer catalog loading",
                    extra={
                        "event": ("catalog.loading"),
                        **deployment_fields,
                        "features_path": str(runtime.dataset_paths.features),
                        "similarity_path": str(runtime.dataset_paths.similarity),
                        "heatmap_similarity_path": str(runtime.dataset_paths.heatmap_similarity),
                        "heatmap_profiles_path": str(runtime.dataset_paths.heatmap_profiles),
                    },
                )

                try:
                    catalog = catalog_loader(
                        features=(runtime.dataset_paths.features),
                        similarity=(runtime.dataset_paths.similarity),
                        heatmap_similarity=(runtime.dataset_paths.heatmap_similarity),
                        heatmap_profiles=(runtime.dataset_paths.heatmap_profiles),
                    )
                except Exception:
                    logger.exception(
                        "Transfer catalog loading failed",
                        extra={
                            "event": ("catalog.load_failed"),
                            **deployment_fields,
                            "duration_ms": (_elapsed_ms(catalog_started_at)),
                        },
                    )
                    raise

                runtime.attach_catalog(catalog)

                logger.info(
                    "Transfer catalog loaded",
                    extra={
                        "event": ("catalog.loaded"),
                        **deployment_fields,
                        "duration_ms": (_elapsed_ms(catalog_started_at)),
                        **_catalog_row_counts(catalog),
                    },
                )

            ready = runtime.is_ready

            logger.info(
                ("WC26 API ready" if ready else ("WC26 API started without runtime catalog")),
                extra={
                    "event": ("api.ready" if ready else "api.started"),
                    **deployment_fields,
                    "ready": ready,
                    "startup_duration_ms": (_elapsed_ms(startup_started_at)),
                },
            )

            yield
        finally:
            shutdown_started_at = perf_counter()

            logger.info(
                "WC26 API shutdown started",
                extra={
                    "event": ("api.shutdown.started"),
                    **deployment_fields,
                    "ready": runtime.is_ready,
                    "uptime_seconds": (runtime.uptime_seconds()),
                },
            )

            runtime.clear_catalog()

            logger.info(
                "WC26 API shutdown completed",
                extra={
                    "event": ("api.shutdown.completed"),
                    **deployment_fields,
                    "ready": runtime.is_ready,
                    "duration_ms": (_elapsed_ms(shutdown_started_at)),
                    "uptime_seconds": (runtime.uptime_seconds()),
                },
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
            expose_headers=[REQUEST_ID_HEADER],
        )

    application.add_middleware(RequestObservabilityMiddleware)

    application.state.api_runtime = runtime

    application.include_router(health_router)
    application.include_router(deployment_router)
    application.include_router(players_router)
    application.include_router(transfer_intelligence_router)

    register_exception_handlers(application)

    return application


__all__ = [
    "TransferDataCatalogLoader",
    "create_app",
]
