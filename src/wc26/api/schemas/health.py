"""Health and readiness API schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response returned by the service health endpoint."""

    status: Literal["ok"]
    service: str
    version: str
    environment: str
    started_at: datetime
    uptime_seconds: float = Field(ge=0.0)


class ReadinessResponse(BaseModel):
    """Response returned by the service readiness endpoint."""

    status: Literal["ready", "not_ready"]
    service: str
    version: str
    environment: str
    started_at: datetime
    uptime_seconds: float = Field(ge=0.0)
    catalog_loaded_at: datetime | None


__all__ = [
    "HealthResponse",
    "ReadinessResponse",
]
