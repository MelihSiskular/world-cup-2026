"""Health-check API schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response returned by the service health endpoint."""

    status: Literal["ok"]
    service: str
    version: str


__all__ = [
    "HealthResponse",
]
