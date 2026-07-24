"""Common API error response schemas."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

type ApiErrorCode = Literal[
    "player_not_found",
    "ambiguous_player",
    "dataset_unavailable",
    "invalid_dataset",
    "analysis_failed",
]


class ApiErrorDetail(BaseModel):
    """Machine-readable and human-readable API error details."""

    model_config = ConfigDict(extra="forbid")

    code: ApiErrorCode
    message: str


class ApiErrorResponse(BaseModel):
    """Standard error envelope returned by the API."""

    model_config = ConfigDict(extra="forbid")

    error: ApiErrorDetail


__all__ = [
    "ApiErrorCode",
    "ApiErrorDetail",
    "ApiErrorResponse",
]
