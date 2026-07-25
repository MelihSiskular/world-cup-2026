"""Service health and readiness routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import (
    APIRouter,
    Request,
    Response,
    status,
)

from wc26 import __version__
from wc26.api.runtime import (
    ApiRuntimeState,
    get_api_runtime_state,
)
from wc26.api.schemas.health import (
    HealthResponse,
    ReadinessResponse,
)

router = APIRouter(
    tags=["system"],
)


def _get_runtime_metadata(
    runtime: ApiRuntimeState,
) -> tuple[datetime, float]:
    """Return metadata available after application startup."""

    started_at = runtime.started_at

    if started_at is None:
        raise RuntimeError("WC26 API runtime has not started.")

    return (
        started_at,
        runtime.uptime_seconds(),
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check API health",
)
def get_health(
    request: Request,
) -> HealthResponse:
    """Return the current API process status."""

    runtime = get_api_runtime_state(request)

    (
        started_at,
        uptime_seconds,
    ) = _get_runtime_metadata(runtime)

    return HealthResponse(
        status="ok",
        service=runtime.settings.service_name,
        version=__version__,
        environment=runtime.settings.environment,
        started_at=started_at,
        uptime_seconds=uptime_seconds,
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Check API readiness",
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ReadinessResponse,
            "description": ("The runtime transfer data catalog is not available."),
        },
    },
)
def get_readiness(
    request: Request,
    response: Response,
) -> ReadinessResponse:
    """Return whether the API is ready to serve analytics requests."""

    runtime = get_api_runtime_state(request)

    (
        started_at,
        uptime_seconds,
    ) = _get_runtime_metadata(runtime)

    catalog_loaded_at = runtime.catalog_loaded_at

    if not runtime.is_ready or catalog_loaded_at is None:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return ReadinessResponse(
            status="not_ready",
            service=runtime.settings.service_name,
            version=__version__,
            environment=runtime.settings.environment,
            started_at=started_at,
            uptime_seconds=uptime_seconds,
            catalog_loaded_at=None,
        )

    return ReadinessResponse(
        status="ready",
        service=runtime.settings.service_name,
        version=__version__,
        environment=runtime.settings.environment,
        started_at=started_at,
        uptime_seconds=uptime_seconds,
        catalog_loaded_at=catalog_loaded_at,
    )


__all__ = [
    "router",
]
