"""Transfer Intelligence API request and response schemas."""

from __future__ import annotations

from typing import Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    model_validator,
)


class HeatmapPlayerResponse(BaseModel):
    """Measured tournament heatmap evidence for one player."""

    model_config = ConfigDict(extra="forbid")

    player_id: int = Field(gt=0)
    player_name: str = Field(min_length=1)

    available: bool

    grid_width: int | None = Field(
        default=None,
        ge=2,
    )
    grid_height: int | None = Field(
        default=None,
        ge=2,
    )
    grid: list[list[float]] | None = None

    matches_with_heatmap: int | None = Field(
        default=None,
        ge=0,
    )
    heatmap_point_count: int | None = Field(
        default=None,
        ge=0,
    )

    weighted_mean_x: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )
    weighted_mean_y: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )
    peak_cell_x: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )
    peak_cell_y: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )
    heatmap_entropy: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    @model_validator(mode="after")
    def validate_grid_contract(self) -> Self:
        """Keep availability and grid dimensions internally consistent."""

        if not self.available:
            if self.grid is not None or self.grid_width is not None or self.grid_height is not None:
                raise ValueError("Unavailable heatmaps must not expose grid data.")

            return self

        if self.grid is None or self.grid_width is None or self.grid_height is None:
            raise ValueError("Available heatmaps require grid data and dimensions.")

        if len(self.grid) != self.grid_height:
            raise ValueError("Heatmap grid height does not match grid_height.")

        if any(len(row) != self.grid_width for row in self.grid):
            raise ValueError("Heatmap grid width does not match grid_width.")

        if any(value < 0.0 for row in self.grid for value in row):
            raise ValueError("Heatmap grid values must be non-negative.")

        return self


class HeatmapSimilarityResponse(BaseModel):
    """Measured pairwise heatmap similarity evidence."""

    model_config = ConfigDict(extra="forbid")

    available: bool

    heatmap_similarity_score_pct: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )
    heatmap_cosine_similarity_pct: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )
    occupation_overlap_pct: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )
    peak_zone_similarity_pct: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )
    peak_zone_distance: float | None = Field(
        default=None,
        ge=0.0,
    )
    entropy_similarity_pct: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )

    target_matches_with_heatmap: int | None = Field(
        default=None,
        ge=0,
    )
    candidate_matches_with_heatmap: int | None = Field(
        default=None,
        ge=0,
    )
    target_heatmap_points: int | None = Field(
        default=None,
        ge=0,
    )
    candidate_heatmap_points: int | None = Field(
        default=None,
        ge=0,
    )

    @model_validator(mode="after")
    def validate_measured_evidence(self) -> Self:
        """Require a measured headline score only when evidence is available."""

        if self.available and self.heatmap_similarity_score_pct is None:
            raise ValueError("Available heatmap similarity requires a measured score.")

        if not self.available and self.heatmap_similarity_score_pct is not None:
            raise ValueError("Unavailable heatmap similarity must not expose a measured score.")

        return self


class HeatmapComparisonResponse(BaseModel):
    """Target-to-candidate tournament heatmap comparison."""

    model_config = ConfigDict(extra="forbid")

    target: HeatmapPlayerResponse
    candidate: HeatmapPlayerResponse
    similarity: HeatmapSimilarityResponse


class RadarDimensionResponse(BaseModel):
    """One position-relative playing-style radar dimension."""

    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
    )

    key: str = Field(min_length=1)
    label: str = Field(min_length=1)

    raw_score: float | None
    percentile: float | None = Field(
        ge=0.0,
        le=100.0,
    )

    peer_count: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_dimension_evidence(
        self,
    ) -> Self:
        """Keep raw-score and percentile evidence consistent."""

        if self.percentile is not None and self.raw_score is None:
            raise ValueError("Radar percentile requires a raw score.")

        return self


class RadarPlayerResponse(BaseModel):
    """Position-relative playing-style profile for one player."""

    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
    )

    player_id: int = Field(gt=0)
    player_name: str = Field(min_length=1)

    position: str | None

    available: bool

    peer_count: int = Field(ge=0)

    dimensions: list[RadarDimensionResponse]

    @model_validator(mode="after")
    def validate_profile_contract(
        self,
    ) -> Self:
        """Validate one radar profile's evidence boundary."""

        keys = [dimension.key for dimension in self.dimensions]

        if len(keys) != len(set(keys)):
            raise ValueError("Radar dimension keys must be unique.")

        if any(dimension.peer_count > self.peer_count for dimension in self.dimensions):
            raise ValueError(
                "Radar dimension peer_count cannot exceed the player profile peer_count."
            )

        usable_dimensions = sum(dimension.percentile is not None for dimension in self.dimensions)

        if self.available:
            if self.position is None:
                raise ValueError("Available radar profiles require a position.")

            if usable_dimensions < 3:
                raise ValueError(
                    "Available radar profiles require at least three percentile dimensions."
                )

        return self


class RadarComparisonMetadataResponse(BaseModel):
    """Rendering compatibility for two playing-style profiles."""

    model_config = ConfigDict(extra="forbid")

    same_position: bool
    overlay_available: bool

    reason: (
        Literal[
            "profiles_unavailable",
            "target_profile_unavailable",
            "candidate_profile_unavailable",
            "different_position_profiles",
            "dimension_contract_mismatch",
        ]
        | None
    )

    @model_validator(mode="after")
    def validate_comparison_metadata(
        self,
    ) -> Self:
        """Keep overlay state and explanation internally consistent."""

        if self.overlay_available:
            if not self.same_position:
                raise ValueError("Radar overlay requires the same position.")

            if self.reason is not None:
                raise ValueError("Available radar overlay must not expose an unavailable reason.")

            return self

        if self.reason is None:
            raise ValueError("Unavailable radar overlay requires a reason.")

        return self


class RadarComparisonResponse(BaseModel):
    """Target-to-candidate playing-style radar comparison."""

    model_config = ConfigDict(extra="forbid")

    target: RadarPlayerResponse
    candidate: RadarPlayerResponse
    comparison: RadarComparisonMetadataResponse

    @model_validator(mode="after")
    def validate_overlay_contract(
        self,
    ) -> Self:
        """Validate shared-axis requirements for an overlay radar."""

        if not self.comparison.overlay_available:
            return self

        if not self.target.available or not self.candidate.available:
            raise ValueError("Radar overlay requires two available profiles.")

        if self.target.position != self.candidate.position:
            raise ValueError("Radar overlay requires matching positions.")

        target_keys = [dimension.key for dimension in self.target.dimensions]

        candidate_keys = [dimension.key for dimension in self.candidate.dimensions]

        if target_keys != candidate_keys:
            raise ValueError("Radar overlay requires matching ordered dimensions.")

        return self


class TransferAnalysisPayload(BaseModel):
    """Client-provided parameters for transfer analysis."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    player: str | None = Field(
        default=None,
        min_length=1,
        description=("Name of the target player. Provide exactly one of player or player_id."),
        examples=["Michael Olise"],
    )
    player_id: int | None = Field(
        default=None,
        gt=0,
        description=(
            "Stable identifier of the target player. Provide exactly one of player or player_id."
        ),
        examples=[978838],
    )
    minimum_minutes: float = Field(
        default=150.0,
        ge=0.0,
        description="Minimum tournament minutes required for candidates.",
    )
    minimum_role_confidence: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="Minimum role-confidence percentage.",
    )
    maximum_market_value: float | None = Field(
        default=None,
        ge=0.0,
        description="Optional maximum candidate market value.",
    )
    neutral_heatmap_score: float = Field(
        default=70.0,
        ge=0.0,
        le=100.0,
        description="Fallback heatmap score when spatial data is unavailable.",
    )

    @model_validator(mode="after")
    def validate_target_identifier(self) -> Self:
        """Require exactly one supported player identifier."""

        identifier_count = sum(
            identifier is not None
            for identifier in (
                self.player,
                self.player_id,
            )
        )

        if identifier_count != 1:
            raise ValueError("Provide exactly one of player or player_id.")

        return self


class TransferPlayerResponse(BaseModel):
    """Stable player fields shared by targets and recommendations."""

    model_config = ConfigDict(extra="allow")

    __pydantic_extra__: dict[str, JsonValue] = Field(init=False)

    player_id: int = Field(gt=0)
    player_name: str = Field(min_length=1)

    national_team_name: str | None = None
    country_name: str | None = None
    position: str | None = None

    age: float | None = Field(default=None, ge=0.0)
    height_cm: float | None = Field(default=None, ge=0.0)
    appearances: int | None = Field(default=None, ge=0)
    starts: int | None = Field(default=None, ge=0)
    minutes: float | None = Field(default=None, ge=0.0)

    weighted_rating: float | None = None
    market_value: float | None = Field(default=None, ge=0.0)
    market_value_currency: str | None = None

    archetype_cluster: int | None = None
    archetype: str | None = None
    spatial_role: str | None = None
    final_role: str | None = None
    lateral_profile: str | None = None
    vertical_profile: str | None = None
    mobility_profile: str | None = None

    role_confidence_pct: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )
    role_confidence_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )
    matches_with_position_data: int | None = Field(
        default=None,
        ge=0,
    )
    total_position_points: int | None = Field(
        default=None,
        ge=0,
    )

    spatial_reliability: float | None = None
    position_consistency_score: float | None = None
    weighted_mean_x: float | None = None
    weighted_mean_y: float | None = None
    weighted_x_std: float | None = None
    weighted_y_std: float | None = None
    spatial_spread: float | None = None

    age_score: float | None = None
    minutes_reliability_score: float | None = None
    rating_quality_score: float | None = None
    market_value_percentile_position: float | None = None
    data_reliability_score: float | None = None
    player_quality_score: float | None = None

    role_reason: str | None = None


class TransferTargetResponse(TransferPlayerResponse):
    """Target player returned by Transfer Intelligence."""


class TransferExplainabilityScoreResponse(BaseModel):
    """Mathematical composition of one recommendation score."""

    model_config = ConfigDict(extra="forbid")

    weighted_signal_total: float = Field(ge=0.0)
    bonus_total: float = Field(ge=0.0)
    pre_clip_score: float
    final_score: float = Field(ge=0.0, le=100.0)
    was_clipped: bool


class TransferExplainabilitySignalResponse(BaseModel):
    """One weighted input used by the recommendation scorer."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    description: str = Field(min_length=1)

    source_score: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
    )
    input_score: float = Field(
        ge=0.0,
        le=100.0,
    )
    weight: float = Field(
        ge=0.0,
        le=1.0,
    )
    weighted_contribution: float = Field(
        ge=0.0,
    )

    evidence_status: Literal[
        "available",
        "fallback",
        "missing",
    ]

    note: str | None = None


class TransferExplainabilityBonusResponse(BaseModel):
    """One explicit mode-specific recommendation bonus."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1)
    label: str = Field(min_length=1)
    configured_points: float = Field(ge=0.0)
    applied: bool
    applied_points: float = Field(ge=0.0)


class TransferExplainabilityReasonResponse(BaseModel):
    """One structured human-readable recommendation reason."""

    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=1)
    group: str = Field(min_length=1)
    text: str = Field(min_length=1)


class TransferRecommendationExplainabilityResponse(BaseModel):
    """Structured explanation of one transfer recommendation."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal[
        "immediate",
        "development",
        "value",
        "short_term",
    ]

    score: TransferExplainabilityScoreResponse
    signals: list[TransferExplainabilitySignalResponse]
    bonuses: list[TransferExplainabilityBonusResponse]
    reasons: list[TransferExplainabilityReasonResponse]


class TransferRecommendationResponse(TransferPlayerResponse):
    """Stable fields shared by every recommendation mode."""

    statistical_similarity_pct: float | None = None
    heatmap_cosine_similarity_pct: float | None = None
    occupation_overlap_pct: float | None = None
    lateral_profile_similarity_pct: float | None = None
    vertical_profile_similarity_pct: float | None = None
    peak_zone_similarity_pct: float | None = None
    peak_zone_distance: float | None = None
    entropy_similarity_pct: float | None = None
    heatmap_similarity_score_pct: float | None = None
    effective_heatmap_score_pct: float | None = None

    target_matches_with_heatmap: int | None = Field(
        default=None,
        ge=0,
    )
    candidate_matches_with_heatmap: int | None = Field(
        default=None,
        ge=0,
    )
    target_heatmap_points: int | None = Field(
        default=None,
        ge=0,
    )
    candidate_heatmap_points: int | None = Field(
        default=None,
        ge=0,
    )
    has_heatmap_similarity: bool | None = None

    role_fit_pct: float | None = None
    spatial_similarity_pct: float | None = None
    market_value_advantage_pct: float | None = None
    age_suitability_pct: float | None = None

    same_final_role: bool | None = None
    same_archetype: bool | None = None

    explainability: TransferRecommendationExplainabilityResponse

    recommendation_type: str
    recommendation_strength: str
    why_recommended: str


class ImmediateTransferRecommendationResponse(TransferRecommendationResponse):
    """Recommendation ranked for immediate first-team impact."""

    immediate_score: float
    immediate_rank: int = Field(ge=1)


class DevelopmentTransferRecommendationResponse(TransferRecommendationResponse):
    """Recommendation ranked as a development investment."""

    development_score: float
    development_rank: int = Field(ge=1)


class ValueTransferRecommendationResponse(TransferRecommendationResponse):
    """Recommendation ranked by market value opportunity."""

    value_score: float
    value_rank: int = Field(ge=1)


class ShortTermTransferRecommendationResponse(TransferRecommendationResponse):
    """Recommendation ranked as a short-term solution."""

    short_term_score: float
    short_term_rank: int = Field(ge=1)


class ImmediateTransferModeResponse(BaseModel):
    """Immediate-impact recruitment recommendations."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["immediate"]
    recommendations: list[ImmediateTransferRecommendationResponse]


class DevelopmentTransferModeResponse(BaseModel):
    """Development-investment recruitment recommendations."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["development"]
    recommendations: list[DevelopmentTransferRecommendationResponse]


class ValueTransferModeResponse(BaseModel):
    """Market-value recruitment recommendations."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["value"]
    recommendations: list[ValueTransferRecommendationResponse]


class ShortTermTransferModeResponse(BaseModel):
    """Short-term recruitment recommendations."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["short_term"]
    recommendations: list[ShortTermTransferRecommendationResponse]


class TransferModesResponse(BaseModel):
    """All supported Transfer Intelligence recruitment scenarios."""

    model_config = ConfigDict(extra="forbid")

    immediate: ImmediateTransferModeResponse
    development: DevelopmentTransferModeResponse
    value: ValueTransferModeResponse
    short_term: ShortTermTransferModeResponse


class TransferAnalysisResponse(BaseModel):
    """Structured transfer analysis API response."""

    model_config = ConfigDict(extra="forbid")

    target: TransferTargetResponse
    modes: TransferModesResponse


__all__ = [
    "DevelopmentTransferModeResponse",
    "HeatmapComparisonResponse",
    "HeatmapPlayerResponse",
    "HeatmapSimilarityResponse",
    "TransferExplainabilityBonusResponse",
    "TransferExplainabilityReasonResponse",
    "TransferExplainabilityScoreResponse",
    "TransferExplainabilitySignalResponse",
    "TransferRecommendationExplainabilityResponse",
    "DevelopmentTransferRecommendationResponse",
    "ImmediateTransferModeResponse",
    "ImmediateTransferRecommendationResponse",
    "ShortTermTransferModeResponse",
    "ShortTermTransferRecommendationResponse",
    "TransferAnalysisPayload",
    "TransferAnalysisResponse",
    "TransferModesResponse",
    "TransferPlayerResponse",
    "TransferRecommendationResponse",
    "TransferTargetResponse",
    "ValueTransferModeResponse",
    "ValueTransferRecommendationResponse",
]
