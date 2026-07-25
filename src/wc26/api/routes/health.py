"""Service health and readiness routes."""

from __future__ import annotations

from fastapi import (
    APIRouter,
    Request,
    Response,
    status,
)

from wc26 import __version__
from wc26.api.runtime import get_api_runtime_state
from wc26.api.schemas.health import (
    HealthResponse,
    ReadinessResponse,
)

router = APIRouter(
    tags=["system"],
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

    return HealthResponse(
        status="ok",
        service=runtime.settings.service_name,
        version=__version__,
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

    if not runtime.is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return ReadinessResponse(
            status="not_ready",
            service=runtime.settings.service_name,
            version=__version__,
        )

    return ReadinessResponse(
        status="ready",
        service=runtime.settings.service_name,
        version=__version__,
    )


__all__ = [
    "router",
]
