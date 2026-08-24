"""Application contract models for transfer intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class TransferAnalysisRequest:
    """Input required to run one transfer analysis."""

    player: str | None
    features: Path
    similarity: Path
    heatmap_similarity: Path
    heatmap_profiles: Path
    minimum_minutes: float
    minimum_role_confidence: float
    maximum_market_value: float | None
    neutral_heatmap_score: float
    player_id: int | None = None


@dataclass(frozen=True, slots=True)
class TransferRecommendation:
    """One JSON-compatible transfer recommendation."""

    data: JsonObject

    def to_dict(self) -> JsonObject:
        """Return a detached dictionary representation."""

        return dict(self.data)


@dataclass(frozen=True, slots=True)
class TransferModeResult:
    """Recommendations produced for one recruitment mode."""

    mode: str
    recommendations: tuple[TransferRecommendation, ...]

    def to_dict(self) -> JsonObject:
        """Return a JSON-compatible dictionary representation."""

        recommendation_values: list[JsonValue] = [
            recommendation.to_dict() for recommendation in self.recommendations
        ]

        return {
            "mode": self.mode,
            "recommendations": recommendation_values,
        }


@dataclass(frozen=True, slots=True)
class TransferAnalysisResult:
    """Complete structured result of a transfer analysis."""

    target: JsonObject
    modes: tuple[TransferModeResult, ...]

    def to_dict(self) -> JsonObject:
        """Return a JSON-compatible dictionary representation."""

        mode_values: dict[str, JsonValue] = {mode.mode: mode.to_dict() for mode in self.modes}

        return {
            "target": dict(self.target),
            "modes": mode_values,
        }


@dataclass(frozen=True, slots=True)
class PlayerSearchRequest:
    """Input parameters required to discover and filter players."""

    query: str | None
    features: Path
    limit: int
    offset: int = 0
    positions: tuple[str, ...] = ()
    final_roles: tuple[str, ...] = ()
    archetypes: tuple[str, ...] = ()
    countries: tuple[str, ...] = ()
    minimum_age: float | None = None
    maximum_age: float | None = None
    minimum_market_value: float | None = None
    maximum_market_value: float | None = None
    minimum_minutes: float | None = None
    minimum_role_confidence: float | None = None
    minimum_data_reliability: float | None = None
    sort_by: str | None = None
    sort_direction: str | None = None


@dataclass(frozen=True, slots=True)
class PlayerSearchItem:
    """One lightweight player-discovery result."""

    player_id: int
    player_name: str
    national_team_name: str | None
    position: str | None
    final_role: str | None
    archetype: str | None
    age: float | None
    market_value: float | None
    market_value_currency: str | None
    country_name: str | None = None
    country_alpha3: str | None = None
    spatial_role: str | None = None
    minutes: float | None = None
    role_confidence_pct: float | None = None
    data_reliability_score: float | None = None
    player_quality_score: float | None = None

    def to_dict(self) -> JsonObject:
        """Return a JSON-compatible player representation."""

        return {
            "player_id": self.player_id,
            "player_name": self.player_name,
            "national_team_name": self.national_team_name,
            "country_name": self.country_name,
            "country_alpha3": self.country_alpha3,
            "position": self.position,
            "final_role": self.final_role,
            "archetype": self.archetype,
            "spatial_role": self.spatial_role,
            "age": self.age,
            "market_value": self.market_value,
            "market_value_currency": self.market_value_currency,
            "minutes": self.minutes,
            "role_confidence_pct": self.role_confidence_pct,
            "data_reliability_score": self.data_reliability_score,
            "player_quality_score": self.player_quality_score,
        }


@dataclass(frozen=True, slots=True)
class PlayerSearchResult:
    """Structured and paginated player-discovery result."""

    query: str | None
    players: tuple[PlayerSearchItem, ...]
    total: int | None = None
    offset: int = 0
    limit: int = 10
    sort_by: str = "relevance"
    sort_direction: str = "asc"

    @property
    def count(self) -> int:
        """Return the number of players in the current page."""

        return len(self.players)

    @property
    def resolved_total(self) -> int:
        """Return the complete filtered result count."""

        return self.count if self.total is None else self.total

    @property
    def has_more(self) -> bool:
        """Return whether another result page is available."""

        return self.offset + self.count < self.resolved_total

    def to_dict(self) -> JsonObject:
        """Return a JSON-compatible discovery result."""

        player_values: list[JsonValue] = [player.to_dict() for player in self.players]

        return {
            "query": self.query,
            "count": self.count,
            "total": self.resolved_total,
            "offset": self.offset,
            "limit": self.limit,
            "has_more": self.has_more,
            "sort_by": self.sort_by,
            "sort_direction": self.sort_direction,
            "players": player_values,
        }


@dataclass(frozen=True, slots=True)
class PlayerSearchFiltersRequest:
    """Dataset paths required to build discovery filter metadata."""

    features: Path
    player_tournament_summary: Path | None = None


@dataclass(frozen=True, slots=True)
class PlayerSearchFilterOption:
    """One dataset-backed categorical filter option."""

    value: str
    label: str
    count: int
    country_alpha3: str | None = None

    def to_dict(self) -> JsonObject:
        """Return a JSON-compatible filter option."""

        return {
            "value": self.value,
            "label": self.label,
            "count": self.count,
            "country_alpha3": self.country_alpha3,
        }


@dataclass(frozen=True, slots=True)
class PlayerSearchFilterRange:
    """Observed numeric range for one discovery filter."""

    minimum: float | None
    maximum: float | None

    def to_dict(self) -> JsonObject:
        """Return a JSON-compatible numeric range."""

        return {
            "minimum": self.minimum,
            "maximum": self.maximum,
        }


@dataclass(frozen=True, slots=True)
class PlayerSearchFiltersResult:
    """Dataset-backed metadata for the advanced-filter UI."""

    player_count: int
    positions: tuple[PlayerSearchFilterOption, ...]
    final_roles: tuple[PlayerSearchFilterOption, ...]
    archetypes: tuple[PlayerSearchFilterOption, ...]
    countries: tuple[PlayerSearchFilterOption, ...]
    age: PlayerSearchFilterRange
    market_value: PlayerSearchFilterRange
    minutes: PlayerSearchFilterRange
    role_confidence: PlayerSearchFilterRange
    data_reliability: PlayerSearchFilterRange
    market_value_currency: str | None

    def to_dict(self) -> JsonObject:
        """Return JSON-compatible discovery filter metadata."""

        position_values: list[JsonValue] = [option.to_dict() for option in self.positions]
        final_role_values: list[JsonValue] = [option.to_dict() for option in self.final_roles]
        archetype_values: list[JsonValue] = [option.to_dict() for option in self.archetypes]
        country_values: list[JsonValue] = [option.to_dict() for option in self.countries]

        return {
            "player_count": self.player_count,
            "positions": position_values,
            "final_roles": final_role_values,
            "archetypes": archetype_values,
            "countries": country_values,
            "age": self.age.to_dict(),
            "market_value": self.market_value.to_dict(),
            "minutes": self.minutes.to_dict(),
            "role_confidence": self.role_confidence.to_dict(),
            "data_reliability": self.data_reliability.to_dict(),
            "market_value_currency": self.market_value_currency,
        }


@dataclass(frozen=True, slots=True)
class PlayerTournamentSummaryResult:
    """Tournament participation context exposed by the player profile."""

    matches: int | None
    starts: int | None
    substitute_appearances: int | None
    captain_appearances: int | None
    minutes: float | None
    formations_used: int | None
    primary_formation: str | None
    primary_lineup_position: str | None

    def to_dict(self) -> JsonObject:
        """Return JSON-compatible tournament context."""

        return {
            "matches": self.matches,
            "starts": self.starts,
            "substitute_appearances": self.substitute_appearances,
            "captain_appearances": self.captain_appearances,
            "minutes": self.minutes,
            "formations_used": self.formations_used,
            "primary_formation": self.primary_formation,
            "primary_lineup_position": self.primary_lineup_position,
        }


@dataclass(frozen=True, slots=True)
class PlayerSampleContextResult:
    """Evidence boundary for percentile interpretation."""

    target_minutes: float | None
    minimum_peer_minutes: float
    target_meets_peer_minimum: bool | None

    def to_dict(self) -> JsonObject:
        """Return JSON-compatible sample context."""

        return {
            "target_minutes": self.target_minutes,
            "minimum_peer_minutes": self.minimum_peer_minutes,
            "target_meets_peer_minimum": (self.target_meets_peer_minimum),
        }


@dataclass(frozen=True, slots=True)
class PlayerPerformanceMetricResult:
    """One presentation-ready player performance metric."""

    key: str
    label: str
    short_label: str
    unit: str
    value: float
    performance_percentile: float | None
    peer_count: int

    def to_dict(self) -> JsonObject:
        """Return JSON-compatible performance metric."""

        return {
            "key": self.key,
            "label": self.label,
            "short_label": self.short_label,
            "unit": self.unit,
            "value": self.value,
            "performance_percentile": (self.performance_percentile),
            "peer_count": self.peer_count,
        }


@dataclass(frozen=True, slots=True)
class PlayerPerformanceMetricGroupResult:
    """One grouped family of player performance metrics."""

    key: str
    metrics: tuple[
        PlayerPerformanceMetricResult,
        ...,
    ]

    def to_dict(self) -> JsonObject:
        """Return JSON-compatible metric group."""

        metric_values: list[JsonValue] = [metric.to_dict() for metric in self.metrics]

        return {
            "key": self.key,
            "metrics": metric_values,
        }


@dataclass(frozen=True, slots=True)
class PlayerInsightResult:
    """One explainable player strength or watch-out."""

    kind: str
    group: str
    group_label: str
    metric_key: str
    metric_label: str
    metric_short_label: str
    value: float
    percentile: float
    peer_count: int
    evidence: str

    def to_dict(self) -> JsonObject:
        """Return JSON-compatible player insight."""

        return {
            "kind": self.kind,
            "group": self.group,
            "group_label": self.group_label,
            "metric_key": self.metric_key,
            "metric_label": self.metric_label,
            "metric_short_label": self.metric_short_label,
            "value": self.value,
            "percentile": self.percentile,
            "peer_count": self.peer_count,
            "evidence": self.evidence,
        }


@dataclass(frozen=True, slots=True)
class PlayerIntelligenceResult:
    """Position-aware tournament intelligence for one player."""

    position_group: str
    sample: PlayerSampleContextResult
    groups: tuple[
        PlayerPerformanceMetricGroupResult,
        ...,
    ]
    strengths: tuple[
        PlayerInsightResult,
        ...,
    ]
    watch_outs: tuple[
        PlayerInsightResult,
        ...,
    ]

    def to_dict(self) -> JsonObject:
        """Return JSON-compatible player intelligence."""

        group_values: list[JsonValue] = [group.to_dict() for group in self.groups]
        strength_values: list[JsonValue] = [insight.to_dict() for insight in self.strengths]
        watch_out_values: list[JsonValue] = [insight.to_dict() for insight in self.watch_outs]

        return {
            "position_group": self.position_group,
            "sample": self.sample.to_dict(),
            "groups": group_values,
            "strengths": strength_values,
            "watch_outs": watch_out_values,
        }


@dataclass(frozen=True, slots=True)
class PlayerProfileRequest:
    """Input required to retrieve one player profile."""

    player_id: int
    features: Path
    player_tournament_summary: Path | None = None


@dataclass(frozen=True, slots=True)
class PlayerProfileResult:
    """Structured profile returned for one player."""

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
    tournament: PlayerTournamentSummaryResult | None = None
    intelligence: PlayerIntelligenceResult | None = None

    def to_dict(self) -> JsonObject:
        """Return a JSON-compatible player profile."""

        return {
            "player_id": self.player_id,
            "player_name": self.player_name,
            "national_team_name": self.national_team_name,
            "country_name": self.country_name,
            "country_alpha3": self.country_alpha3,
            "position": self.position,
            "age": self.age,
            "height_cm": self.height_cm,
            "appearances": self.appearances,
            "starts": self.starts,
            "minutes": self.minutes,
            "weighted_rating": self.weighted_rating,
            "market_value": self.market_value,
            "market_value_currency": self.market_value_currency,
            "archetype": self.archetype,
            "spatial_role": self.spatial_role,
            "final_role": self.final_role,
            "lateral_profile": self.lateral_profile,
            "vertical_profile": self.vertical_profile,
            "mobility_profile": self.mobility_profile,
            "role_confidence_pct": self.role_confidence_pct,
            "spatial_reliability": self.spatial_reliability,
            "data_reliability_score": self.data_reliability_score,
            "player_quality_score": self.player_quality_score,
            "role_reason": self.role_reason,
            "tournament": (None if self.tournament is None else self.tournament.to_dict()),
            "intelligence": (None if self.intelligence is None else self.intelligence.to_dict()),
        }


@dataclass(frozen=True, slots=True)
class HeatmapPlayerRequest:
    """Stable player identifier for one measured heatmap."""

    player_id: int


@dataclass(frozen=True, slots=True)
class HeatmapComparisonRequest:
    """Stable player identifiers for one heatmap comparison."""

    target_player_id: int
    candidate_player_id: int


@dataclass(frozen=True, slots=True)
class HeatmapPlayerResult:
    """Heatmap evidence available for one comparison player."""

    player_id: int
    player_name: str
    available: bool
    grid_width: int | None
    grid_height: int | None
    grid: tuple[tuple[float, ...], ...] | None
    matches_with_heatmap: int | None
    heatmap_point_count: int | None
    weighted_mean_x: float | None
    weighted_mean_y: float | None
    peak_cell_x: float | None
    peak_cell_y: float | None
    heatmap_entropy: float | None

    def to_dict(self) -> JsonObject:
        """Return JSON-compatible player heatmap evidence."""

        grid_value: JsonValue = None

        if self.grid is not None:
            grid_rows: list[JsonValue] = []

            for row in self.grid:
                row_values: list[JsonValue] = [float(value) for value in row]
                grid_rows.append(row_values)

            grid_value = grid_rows

        return {
            "player_id": self.player_id,
            "player_name": self.player_name,
            "available": self.available,
            "grid_width": self.grid_width,
            "grid_height": self.grid_height,
            "grid": grid_value,
            "matches_with_heatmap": self.matches_with_heatmap,
            "heatmap_point_count": self.heatmap_point_count,
            "weighted_mean_x": self.weighted_mean_x,
            "weighted_mean_y": self.weighted_mean_y,
            "peak_cell_x": self.peak_cell_x,
            "peak_cell_y": self.peak_cell_y,
            "heatmap_entropy": self.heatmap_entropy,
        }


@dataclass(frozen=True, slots=True)
class HeatmapSimilarityResult:
    """Measured pairwise heatmap similarity evidence."""

    available: bool
    heatmap_similarity_score_pct: float | None
    heatmap_cosine_similarity_pct: float | None
    occupation_overlap_pct: float | None
    peak_zone_similarity_pct: float | None
    peak_zone_distance: float | None
    entropy_similarity_pct: float | None
    target_matches_with_heatmap: int | None
    candidate_matches_with_heatmap: int | None
    target_heatmap_points: int | None
    candidate_heatmap_points: int | None

    def to_dict(self) -> JsonObject:
        """Return JSON-compatible measured similarity evidence."""

        return {
            "available": self.available,
            "heatmap_similarity_score_pct": (self.heatmap_similarity_score_pct),
            "heatmap_cosine_similarity_pct": (self.heatmap_cosine_similarity_pct),
            "occupation_overlap_pct": (self.occupation_overlap_pct),
            "peak_zone_similarity_pct": (self.peak_zone_similarity_pct),
            "peak_zone_distance": self.peak_zone_distance,
            "entropy_similarity_pct": (self.entropy_similarity_pct),
            "target_matches_with_heatmap": (self.target_matches_with_heatmap),
            "candidate_matches_with_heatmap": (self.candidate_matches_with_heatmap),
            "target_heatmap_points": (self.target_heatmap_points),
            "candidate_heatmap_points": (self.candidate_heatmap_points),
        }


@dataclass(frozen=True, slots=True)
class HeatmapComparisonResult:
    """Complete target-to-candidate heatmap comparison."""

    target: HeatmapPlayerResult
    candidate: HeatmapPlayerResult
    similarity: HeatmapSimilarityResult

    def to_dict(self) -> JsonObject:
        """Return JSON-compatible heatmap comparison."""

        return {
            "target": self.target.to_dict(),
            "candidate": self.candidate.to_dict(),
            "similarity": self.similarity.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class RadarComparisonRequest:
    """Stable player identifiers for one radar comparison."""

    target_player_id: int
    candidate_player_id: int


@dataclass(frozen=True, slots=True)
class RadarDimensionResult:
    """One position-relative playing-style radar dimension."""

    key: str
    label: str
    raw_score: float | None
    percentile: float | None
    peer_count: int

    def to_dict(self) -> JsonObject:
        """Return JSON-compatible radar dimension evidence."""

        return {
            "key": self.key,
            "label": self.label,
            "raw_score": self.raw_score,
            "percentile": self.percentile,
            "peer_count": self.peer_count,
        }


@dataclass(frozen=True, slots=True)
class RadarPlayerResult:
    """Position-relative radar profile for one player."""

    player_id: int
    player_name: str
    position: str | None
    available: bool
    peer_count: int
    dimensions: tuple[RadarDimensionResult, ...]

    def to_dict(self) -> JsonObject:
        """Return JSON-compatible radar player profile."""

        dimension_values: list[JsonValue] = [dimension.to_dict() for dimension in self.dimensions]

        return {
            "player_id": self.player_id,
            "player_name": self.player_name,
            "position": self.position,
            "available": self.available,
            "peer_count": self.peer_count,
            "dimensions": dimension_values,
        }


@dataclass(frozen=True, slots=True)
class RadarComparisonMetadataResult:
    """Compatibility metadata for rendering two radar profiles."""

    same_position: bool
    overlay_available: bool
    reason: str | None

    def to_dict(self) -> JsonObject:
        """Return JSON-compatible radar comparison metadata."""

        return {
            "same_position": self.same_position,
            "overlay_available": self.overlay_available,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class RadarComparisonResult:
    """Complete target-to-candidate playing-style radar comparison."""

    target: RadarPlayerResult
    candidate: RadarPlayerResult
    comparison: RadarComparisonMetadataResult

    def to_dict(self) -> JsonObject:
        """Return JSON-compatible radar comparison."""

        return {
            "target": self.target.to_dict(),
            "candidate": self.candidate.to_dict(),
            "comparison": self.comparison.to_dict(),
        }


__all__ = [
    "HeatmapComparisonRequest",
    "HeatmapComparisonResult",
    "HeatmapPlayerRequest",
    "HeatmapPlayerResult",
    "HeatmapSimilarityResult",
    "JsonObject",
    "JsonScalar",
    "JsonValue",
    "PlayerInsightResult",
    "PlayerIntelligenceResult",
    "PlayerPerformanceMetricGroupResult",
    "PlayerPerformanceMetricResult",
    "PlayerSampleContextResult",
    "PlayerTournamentSummaryResult",
    "PlayerProfileRequest",
    "PlayerProfileResult",
    "PlayerSearchFilterOption",
    "PlayerSearchFilterRange",
    "PlayerSearchFiltersRequest",
    "PlayerSearchFiltersResult",
    "PlayerSearchItem",
    "PlayerSearchRequest",
    "PlayerSearchResult",
    "RadarComparisonMetadataResult",
    "RadarComparisonRequest",
    "RadarComparisonResult",
    "RadarDimensionResult",
    "RadarPlayerResult",
    "TransferAnalysisRequest",
    "TransferAnalysisResult",
    "TransferModeResult",
    "TransferRecommendation",
]
