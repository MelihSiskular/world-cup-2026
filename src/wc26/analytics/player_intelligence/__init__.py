"""Reusable player-intelligence analytics."""

from wc26.analytics.player_intelligence.insights import (
    DEFAULT_MAX_STRENGTHS,
    DEFAULT_MAX_WATCH_OUTS,
    DEFAULT_STRENGTH_PERCENTILE,
    DEFAULT_WATCH_OUT_PERCENTILE,
    InsightKind,
    PlayerInsight,
    PlayerInsightSummary,
    build_player_insights,
)
from wc26.analytics.player_intelligence.metric_registry import (
    METRIC_REGISTRY,
    MetricDefinition,
    MetricGroup,
    MetricUnit,
    PositionGroup,
    get_metric_definition,
    metrics_for_group,
    metrics_for_position_group,
)
from wc26.analytics.player_intelligence.percentiles import (
    DEFAULT_MINIMUM_COHORT_MINUTES,
    DEFAULT_MINIMUM_PEER_COUNT,
    MetricPercentileResult,
    PlayerPercentileProfile,
    calculate_player_percentiles,
)
from wc26.analytics.player_intelligence.positions import (
    normalize_position_group,
)
from wc26.analytics.player_intelligence.profile import (
    PerformanceMetric,
    PerformanceMetricGroup,
    PlayerIntelligenceProfile,
    SampleContext,
    TournamentSummary,
    build_player_intelligence_profile,
)

__all__ = [
    "PerformanceMetric",
    "PerformanceMetricGroup",
    "PlayerIntelligenceProfile",
    "SampleContext",
    "TournamentSummary",
    "build_player_intelligence_profile",
    "DEFAULT_MAX_STRENGTHS",
    "DEFAULT_MAX_WATCH_OUTS",
    "DEFAULT_MINIMUM_COHORT_MINUTES",
    "DEFAULT_MINIMUM_PEER_COUNT",
    "DEFAULT_STRENGTH_PERCENTILE",
    "DEFAULT_WATCH_OUT_PERCENTILE",
    "METRIC_REGISTRY",
    "InsightKind",
    "MetricDefinition",
    "MetricGroup",
    "MetricPercentileResult",
    "MetricUnit",
    "PlayerInsight",
    "PlayerInsightSummary",
    "PlayerPercentileProfile",
    "PositionGroup",
    "build_player_insights",
    "calculate_player_percentiles",
    "get_metric_definition",
    "metrics_for_group",
    "metrics_for_position_group",
    "normalize_position_group",
]
