"""Deployment identity route."""

from __future__ import annotations

from fastapi import APIRouter, Request

from wc26 import __version__
from wc26.api.deployment import (
    resolve_deployment_identity,
)
from wc26.api.schemas.deployment import (
    DeploymentIdentityResponse,
)
from wc26.api.settings import ApiSettings

router = APIRouter(
    tags=["system"],
)


def _get_api_settings(
    request: Request,
) -> ApiSettings:
    """Return settings stored on the application runtime."""

    runtime = getattr(
        request.app.state,
        "api_runtime",
        None,
    )
    runtime_settings = getattr(
        runtime,
        "settings",
        None,
    )

    if isinstance(
        runtime_settings,
        ApiSettings,
    ):
        return runtime_settings

    direct_settings = getattr(
        request.app.state,
        "api_settings",
        None,
    )

    if isinstance(
        direct_settings,
        ApiSettings,
    ):
        return direct_settings

    return ApiSettings.from_environment()


@router.get(
    "/deployment",
    response_model=DeploymentIdentityResponse,
    summary="Inspect deployment identity",
)
def get_deployment_identity(
    request: Request,
) -> DeploymentIdentityResponse:
    """Return application and dataset release identity."""

    settings = _get_api_settings(request)
    identity = resolve_deployment_identity()

    return DeploymentIdentityResponse(
        service=settings.service_name,
        version=__version__,
        environment=settings.environment,
        provider=identity.provider,
        commit_sha=identity.commit_sha,
        branch=identity.branch,
        deployment_id=identity.deployment_id,
        dataset_bundle_sha256=(identity.dataset_bundle_sha256),
    )


__all__ = [
    "router",
]
