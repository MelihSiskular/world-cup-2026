"""Enriched tournament scouting profile construction."""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from wc26.analytics.player_intelligence.insights import (
    PlayerInsight,
    build_player_insights,
)
from wc26.analytics.player_intelligence.metric_registry import (
    MetricGroup,
    MetricUnit,
    PositionGroup,
    metrics_for_group,
)
from wc26.analytics.player_intelligence.percentiles import (
    DEFAULT_MINIMUM_COHORT_MINUTES,
    DEFAULT_MINIMUM_PEER_COUNT,
    MetricPercentileResult,
    calculate_player_percentiles,
)


@dataclass(frozen=True, slots=True)
class TournamentSummary:
    """Tournament participation context for one player."""

    matches: int | None
    starts: int | None
    substitute_appearances: int | None
    captain_appearances: int | None
    minutes: float | None
    formations_used: int | None
    primary_formation: str | None
    primary_lineup_position: str | None


@dataclass(frozen=True, slots=True)
class PerformanceMetric:
    """One presentation-ready position-aware performance metric."""

    key: str
    label: str
    short_label: str
    unit: MetricUnit
    value: float
    performance_percentile: float
    peer_count: int


@dataclass(frozen=True, slots=True)
class PerformanceMetricGroup:
    """One analytical metric family."""

    key: MetricGroup
    metrics: tuple[PerformanceMetric, ...]


@dataclass(frozen=True, slots=True)
class SampleContext:
    """Sample-size information required to interpret the profile."""

    target_minutes: float | None
    minimum_peer_minutes: float
    target_meets_peer_minimum: bool | None


@dataclass(frozen=True, slots=True)
class PlayerIntelligenceProfile:
    """Backend-owned tournament player intelligence."""

    player_id: int
    position_group: PositionGroup
    tournament: TournamentSummary
    sample: SampleContext
    groups: tuple[PerformanceMetricGroup, ...]
    strengths: tuple[PlayerInsight, ...]
    watch_outs: tuple[PlayerInsight, ...]


def _optional_float(
    value: object,
) -> float | None:
    """Return one finite numeric value."""

    if value is None or value is pd.NA or value is pd.NaT:
        return None

    try:
        result = float(str(value).strip())
    except ValueError:
        return None

    if not math.isfinite(result):
        return None

    return result


def _optional_int(
    value: object,
) -> int | None:
    """Return one integer value."""

    numeric = _optional_float(value)

    if numeric is None:
        return None

    if not numeric.is_integer():
        return None

    return int(numeric)


def _optional_text(
    value: object,
) -> str | None:
    """Return normalized optional text."""

    if value is None or value is pd.NA or value is pd.NaT:
        return None

    text = str(value).strip()

    return text or None


def _find_player(
    dataframe: pd.DataFrame,
    *,
    player_id: int,
) -> pd.Series:
    """Return exactly one enriched player row."""

    if "player_id" not in dataframe.columns:
        raise ValueError("Player intelligence dataset is missing player_id.")

    ids = pd.to_numeric(
        dataframe["player_id"],
        errors="coerce",
    )

    matches = dataframe.loc[ids.eq(player_id)]

    if matches.empty:
        raise ValueError(f"Player not found in enriched tournament summary: {player_id}")

    if len(matches) != 1:
        raise ValueError(
            f"Enriched tournament summary returned multiple rows for player ID: {player_id}"
        )

    return matches.iloc[0]


def _build_tournament_summary(
    target: pd.Series,
) -> TournamentSummary:
    """Build tournament participation context."""

    return TournamentSummary(
        matches=_optional_int(target.get("matches_played")),
        starts=_optional_int(target.get("starts")),
        substitute_appearances=_optional_int(target.get("substitute_appearances")),
        captain_appearances=_optional_int(target.get("captain_appearances")),
        minutes=_optional_float(target.get("total_minutes")),
        formations_used=_optional_int(target.get("formations_used")),
        primary_formation=_optional_text(target.get("primary_formation")),
        primary_lineup_position=_optional_text(target.get("primary_lineup_position")),
    )


def _build_metric_groups(
    *,
    position_group: PositionGroup,
    percentile_metrics: tuple[
        MetricPercentileResult,
        ...,
    ],
) -> tuple[PerformanceMetricGroup, ...]:
    """Group percentile results using registry order."""

    result_by_key = {result.metric_key: result for result in percentile_metrics}

    groups: list[PerformanceMetricGroup] = []

    for metric_group in MetricGroup:
        metrics: list[PerformanceMetric] = []

        for definition in metrics_for_group(
            metric_group,
            position_group=position_group,
        ):
            percentile_result = result_by_key.get(definition.key)

            if percentile_result is None:
                continue

            metrics.append(
                PerformanceMetric(
                    key=definition.key,
                    label=definition.label,
                    short_label=(definition.short_label),
                    unit=definition.unit,
                    value=(percentile_result.value),
                    performance_percentile=(percentile_result.percentile),
                    peer_count=(percentile_result.peer_count),
                )
            )

        if metrics:
            groups.append(
                PerformanceMetricGroup(
                    key=metric_group,
                    metrics=tuple(metrics),
                )
            )

    return tuple(groups)


def build_player_intelligence_profile(
    dataframe: pd.DataFrame,
    *,
    player_id: int,
    minimum_cohort_minutes: float = (DEFAULT_MINIMUM_COHORT_MINUTES),
    minimum_peer_count: int = (DEFAULT_MINIMUM_PEER_COUNT),
) -> PlayerIntelligenceProfile:
    """Build one enriched, explainable tournament scouting profile."""

    target = _find_player(
        dataframe,
        player_id=player_id,
    )

    percentile_profile = calculate_player_percentiles(
        dataframe,
        player_id=player_id,
        minimum_cohort_minutes=(minimum_cohort_minutes),
        minimum_peer_count=(minimum_peer_count),
    )

    insight_summary = build_player_insights(percentile_profile)

    tournament = _build_tournament_summary(target)

    target_meets_peer_minimum = (
        None if tournament.minutes is None else (tournament.minutes >= minimum_cohort_minutes)
    )

    return PlayerIntelligenceProfile(
        player_id=player_id,
        position_group=(percentile_profile.position_group),
        tournament=tournament,
        sample=SampleContext(
            target_minutes=(tournament.minutes),
            minimum_peer_minutes=(minimum_cohort_minutes),
            target_meets_peer_minimum=(target_meets_peer_minimum),
        ),
        groups=_build_metric_groups(
            position_group=(percentile_profile.position_group),
            percentile_metrics=(percentile_profile.metrics),
        ),
        strengths=(insight_summary.strengths),
        watch_outs=(insight_summary.watch_outs),
    )


__all__ = [
    "PerformanceMetric",
    "PerformanceMetricGroup",
    "PlayerIntelligenceProfile",
    "SampleContext",
    "TournamentSummary",
    "build_player_intelligence_profile",
]
