"""Service health and readiness routes."""

from __future__ import annotations

from fastapi import (
    APIRouter,
    Request,
    Response,
    status,
)

from wc26 import __version__
from wc26.analytics.transfer_intelligence.catalog import (
    TransferDataCatalog,
)
from wc26.api.schemas.health import (
    HealthResponse,
    ReadinessResponse,
)
from wc26.api.settings import ApiSettings

router = APIRouter(
    tags=["system"],
)


def _get_api_settings(
    request: Request,
) -> ApiSettings:
    """Return settings stored on the FastAPI application."""

    settings = getattr(
        request.app.state,
        "api_settings",
        None,
    )

    if isinstance(
        settings,
        ApiSettings,
    ):
        return settings

    return ApiSettings()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check API health",
)
def get_health(
    request: Request,
) -> HealthResponse:
    """Return the current API process status."""

    settings = _get_api_settings(request)

    return HealthResponse(
        status="ok",
        service=settings.service_name,
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

    settings = _get_api_settings(request)

    catalog = getattr(
        request.app.state,
        "transfer_data_catalog",
        None,
    )

    if not isinstance(
        catalog,
        TransferDataCatalog,
    ):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return ReadinessResponse(
            status="not_ready",
            service=settings.service_name,
            version=__version__,
        )

    return ReadinessResponse(
        status="ready",
        service=settings.service_name,
        version=__version__,
    )


__all__ = [
    "router",
]
