"""Deployment identity API schemas."""

from __future__ import annotations

from pydantic import BaseModel


class DeploymentIdentityResponse(BaseModel):
    """Application and dataset release identity."""

    service: str
    version: str
    environment: str
    provider: str
    commit_sha: str | None
    branch: str | None
    deployment_id: str | None
    dataset_bundle_sha256: str | None


__all__ = [
    "DeploymentIdentityResponse",
]
