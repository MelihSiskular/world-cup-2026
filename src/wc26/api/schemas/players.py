"""Player catalogue API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PlayerSearchItemResponse(BaseModel):
    """Lightweight player information returned by search."""

    model_config = ConfigDict(extra="forbid")

    player_id: int
    player_name: str
    national_team_name: str | None
    position: str | None
    final_role: str | None
    archetype: str | None
    age: float | None
    market_value: float | None
    market_value_currency: str | None


class PlayerSearchResponse(BaseModel):
    """Structured response returned by player search."""

    model_config = ConfigDict(extra="forbid")

    query: str
    count: int = Field(ge=0)
    players: list[PlayerSearchItemResponse]


class PlayerProfileResponse(BaseModel):
    """Detailed profile returned for one player."""

    model_config = ConfigDict(extra="forbid")

    player_id: int
    player_name: str
    national_team_name: str | None
    country_name: str | None
    position: str | None
    age: float | None
    height_cm: float | None
    appearances: int | None
    starts: int | None
    minutes: float | None
    weighted_rating: float | None
    market_value: float | None
    market_value_currency: str | None
    archetype: str | None
    spatial_role: str | None
    final_role: str | None
    lateral_profile: str | None
    vertical_profile: str | None
    mobility_profile: str | None
    role_confidence_pct: float | None
    spatial_reliability: float | None
    data_reliability_score: float | None
    player_quality_score: float | None
    role_reason: str | None


__all__ = [
    "PlayerProfileResponse",
    "PlayerSearchItemResponse",
    "PlayerSearchResponse",
]
