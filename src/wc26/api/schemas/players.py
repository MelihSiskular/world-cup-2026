"""Player catalogue API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PlayerSearchItemResponse(BaseModel):
    """Lightweight player information returned by discovery."""

    model_config = ConfigDict(extra="forbid")

    player_id: int
    player_name: str
    national_team_name: str | None
    country_name: str | None
    country_alpha3: str | None
    position: str | None
    final_role: str | None
    archetype: str | None
    spatial_role: str | None
    age: float | None
    market_value: float | None
    market_value_currency: str | None
    minutes: float | None
    role_confidence_pct: float | None
    data_reliability_score: float | None
    player_quality_score: float | None


class PlayerSearchResponse(BaseModel):
    """Structured and paginated player-discovery response."""

    model_config = ConfigDict(extra="forbid")

    query: str | None
    count: int = Field(ge=0)
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=25)
    has_more: bool
    sort_by: str
    sort_direction: str
    players: list[PlayerSearchItemResponse]


class PlayerSearchFilterOptionResponse(BaseModel):
    """One categorical player-discovery filter option."""

    model_config = ConfigDict(extra="forbid")

    value: str
    label: str
    count: int = Field(ge=0)
    country_alpha3: str | None


class PlayerSearchFilterRangeResponse(BaseModel):
    """Observed numeric range for one discovery filter."""

    model_config = ConfigDict(extra="forbid")

    minimum: float | None
    maximum: float | None


class PlayerSearchFiltersResponse(BaseModel):
    """Dataset-backed advanced-filter metadata."""

    model_config = ConfigDict(extra="forbid")

    player_count: int = Field(ge=0)
    positions: list[PlayerSearchFilterOptionResponse]
    final_roles: list[PlayerSearchFilterOptionResponse]
    archetypes: list[PlayerSearchFilterOptionResponse]
    countries: list[PlayerSearchFilterOptionResponse]
    age: PlayerSearchFilterRangeResponse
    market_value: PlayerSearchFilterRangeResponse
    minutes: PlayerSearchFilterRangeResponse
    role_confidence: PlayerSearchFilterRangeResponse
    data_reliability: PlayerSearchFilterRangeResponse
    market_value_currency: str | None


class PlayerTournamentSummaryResponse(BaseModel):
    """Tournament participation context for one player."""

    model_config = ConfigDict(extra="forbid")

    matches: int | None
    starts: int | None
    substitute_appearances: int | None
    captain_appearances: int | None
    minutes: float | None
    formations_used: int | None
    primary_formation: str | None
    primary_lineup_position: str | None


class PlayerSampleContextResponse(BaseModel):
    """Sample-size context for percentile interpretation."""

    model_config = ConfigDict(extra="forbid")

    target_minutes: float | None
    minimum_peer_minutes: float = Field(ge=0)
    target_meets_peer_minimum: bool | None


class PlayerPerformanceMetricResponse(BaseModel):
    """One position-aware tournament metric."""

    model_config = ConfigDict(extra="forbid")

    key: str
    label: str
    short_label: str
    unit: str
    value: float
    performance_percentile: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )
    peer_count: int = Field(ge=0)


class PlayerPerformanceMetricGroupResponse(BaseModel):
    """Grouped player metrics."""

    model_config = ConfigDict(extra="forbid")

    key: str
    metrics: list[PlayerPerformanceMetricResponse]


class PlayerInsightResponse(BaseModel):
    """Explainable strength or watch-out."""

    model_config = ConfigDict(extra="forbid")

    kind: str
    group: str
    group_label: str
    metric_key: str
    metric_label: str
    metric_short_label: str
    value: float
    percentile: float = Field(
        ge=0,
        le=100,
    )
    peer_count: int = Field(ge=0)
    evidence: str


class PlayerIntelligenceResponse(BaseModel):
    """Position-aware tournament intelligence."""

    model_config = ConfigDict(extra="forbid")

    position_group: str
    sample: PlayerSampleContextResponse
    groups: list[PlayerPerformanceMetricGroupResponse]
    strengths: list[PlayerInsightResponse]
    watch_outs: list[PlayerInsightResponse]


class PlayerProfileResponse(BaseModel):
    """Detailed profile returned for one player."""

    model_config = ConfigDict(extra="forbid")

    player_id: int
    player_name: str
    national_team_name: str | None
    country_name: str | None
    country_alpha3: str | None
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
    tournament: PlayerTournamentSummaryResponse | None = None
    intelligence: PlayerIntelligenceResponse | None = None


__all__ = [
    "PlayerInsightResponse",
    "PlayerIntelligenceResponse",
    "PlayerPerformanceMetricGroupResponse",
    "PlayerPerformanceMetricResponse",
    "PlayerSampleContextResponse",
    "PlayerTournamentSummaryResponse",
    "PlayerProfileResponse",
    "PlayerSearchFilterOptionResponse",
    "PlayerSearchFilterRangeResponse",
    "PlayerSearchFiltersResponse",
    "PlayerSearchItemResponse",
    "PlayerSearchResponse",
]
