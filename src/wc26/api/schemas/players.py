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


__all__ = [
    "PlayerSearchItemResponse",
    "PlayerSearchResponse",
]
