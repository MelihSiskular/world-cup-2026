"""Service health-check routes."""

from __future__ import annotations

from fastapi import APIRouter

from wc26 import __version__
from wc26.api.schemas.health import HealthResponse

router = APIRouter(
    tags=["system"],
)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check API health",
)
def get_health() -> HealthResponse:
    """Return the current API service status."""

    return HealthResponse(
        status="ok",
        service="wc26-transfer-intelligence",
        version=__version__,
    )


__all__ = [
    "router",
]
