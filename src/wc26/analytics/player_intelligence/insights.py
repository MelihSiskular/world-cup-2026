"""Strength and watch-out interpretation for player intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from wc26.analytics.player_intelligence.metric_registry import (
    METRIC_REGISTRY,
    MetricGroup,
    get_metric_definition,
)
from wc26.analytics.player_intelligence.percentiles import (
    MetricPercentileResult,
    PlayerPercentileProfile,
)

DEFAULT_STRENGTH_PERCENTILE: Final[float] = 85.0
DEFAULT_WATCH_OUT_PERCENTILE: Final[float] = 20.0
DEFAULT_MAX_STRENGTHS: Final[int] = 4
DEFAULT_MAX_WATCH_OUTS: Final[int] = 3


class InsightKind(StrEnum):
    """Semantic type of one player-intelligence insight."""

    STRENGTH = "strength"
    WATCH_OUT = "watch_out"


GROUP_LABELS: Final[dict[MetricGroup, str]] = {
    MetricGroup.CREATION: "Chance creation",
    MetricGroup.PROGRESSION: "Ball progression",
    MetricGroup.POSSESSION: "Possession",
    MetricGroup.DEFENDING: "Defensive contribution",
    MetricGroup.SCORING: "Scoring threat",
    MetricGroup.PHYSICAL: "Physical output",
    MetricGroup.GOALKEEPING: "Goalkeeping",
}


METRIC_ORDER: Final[dict[str, int]] = {
    metric.key: index for index, metric in enumerate(METRIC_REGISTRY)
}


@dataclass(frozen=True, slots=True)
class PlayerInsight:
    """One explainable strength or watch-out."""

    kind: InsightKind
    group: MetricGroup
    group_label: str
    metric_key: str
    metric_label: str
    metric_short_label: str
    value: float
    percentile: float
    peer_count: int
    evidence: str


@dataclass(frozen=True, slots=True)
class PlayerInsightSummary:
    """Selected strengths and watch-outs for one player."""

    strengths: tuple[PlayerInsight, ...]
    watch_outs: tuple[PlayerInsight, ...]


def _validate_configuration(
    *,
    strength_percentile: float,
    watch_out_percentile: float,
    max_strengths: int,
    max_watch_outs: int,
) -> None:
    """Validate insight-selection configuration."""

    if not 0 <= strength_percentile <= 100:
        raise ValueError("Strength percentile must be between 0 and 100.")

    if not 0 <= watch_out_percentile <= 100:
        raise ValueError("Watch-out percentile must be between 0 and 100.")

    if watch_out_percentile >= strength_percentile:
        raise ValueError("Watch-out percentile must be lower than strength percentile.")

    if max_strengths < 0:
        raise ValueError("Maximum strengths cannot be negative.")

    if max_watch_outs < 0:
        raise ValueError("Maximum watch-outs cannot be negative.")


def _require_percentile(
    metric: MetricPercentileResult,
) -> float:
    """Return percentile evidence required for an insight."""

    if metric.percentile is None:
        raise ValueError("Insight metric requires percentile evidence.")

    return metric.percentile


def _select_diverse_metrics(
    metrics: tuple[MetricPercentileResult, ...],
    *,
    highest_first: bool,
    limit: int,
) -> tuple[MetricPercentileResult, ...]:
    """Select the strongest metric from distinct analytical groups."""

    if limit == 0:
        return ()

    if highest_first:
        ordered = sorted(
            metrics,
            key=lambda metric: (
                -_require_percentile(metric),
                METRIC_ORDER[metric.metric_key],
            ),
        )
    else:
        ordered = sorted(
            metrics,
            key=lambda metric: (
                _require_percentile(metric),
                METRIC_ORDER[metric.metric_key],
            ),
        )

    selected: list[MetricPercentileResult] = []

    used_groups: set[MetricGroup] = set()

    for metric in ordered:
        definition = get_metric_definition(metric.metric_key)

        if definition.group in used_groups:
            continue

        selected.append(metric)

        used_groups.add(definition.group)

        if len(selected) >= limit:
            break

    return tuple(selected)


def _build_evidence(
    *,
    metric: MetricPercentileResult,
) -> str:
    """Build deterministic human-readable percentile evidence."""

    definition = get_metric_definition(metric.metric_key)
    percentile = _require_percentile(metric)

    return (
        f"{definition.short_label} ranks at the "
        f"{percentile:.1f} performance percentile "
        f"among {metric.peer_count} eligible "
        "same-position players."
    )


def _to_insight(
    metric: MetricPercentileResult,
    *,
    kind: InsightKind,
) -> PlayerInsight:
    """Convert one percentile metric into public insight metadata."""

    definition = get_metric_definition(metric.metric_key)
    percentile = _require_percentile(metric)

    return PlayerInsight(
        kind=kind,
        group=definition.group,
        group_label=GROUP_LABELS[definition.group],
        metric_key=metric.metric_key,
        metric_label=definition.label,
        metric_short_label=definition.short_label,
        value=metric.value,
        percentile=percentile,
        peer_count=metric.peer_count,
        evidence=_build_evidence(metric=metric),
    )


def build_player_insights(
    profile: PlayerPercentileProfile,
    *,
    strength_percentile: float = (DEFAULT_STRENGTH_PERCENTILE),
    watch_out_percentile: float = (DEFAULT_WATCH_OUT_PERCENTILE),
    max_strengths: int = (DEFAULT_MAX_STRENGTHS),
    max_watch_outs: int = (DEFAULT_MAX_WATCH_OUTS),
) -> PlayerInsightSummary:
    """Select explainable strengths and watch-outs from percentile evidence."""

    _validate_configuration(
        strength_percentile=strength_percentile,
        watch_out_percentile=watch_out_percentile,
        max_strengths=max_strengths,
        max_watch_outs=max_watch_outs,
    )

    strength_candidates = tuple(
        metric
        for metric in profile.metrics
        if metric.percentile is not None and metric.percentile >= strength_percentile
    )

    watch_out_candidates = tuple(
        metric
        for metric in profile.metrics
        if metric.percentile is not None and metric.percentile <= watch_out_percentile
    )

    selected_strengths = _select_diverse_metrics(
        strength_candidates,
        highest_first=True,
        limit=max_strengths,
    )

    selected_watch_outs = _select_diverse_metrics(
        watch_out_candidates,
        highest_first=False,
        limit=max_watch_outs,
    )

    return PlayerInsightSummary(
        strengths=tuple(
            _to_insight(
                metric,
                kind=InsightKind.STRENGTH,
            )
            for metric in selected_strengths
        ),
        watch_outs=tuple(
            _to_insight(
                metric,
                kind=InsightKind.WATCH_OUT,
            )
            for metric in selected_watch_outs
        ),
    )


__all__ = [
    "DEFAULT_MAX_STRENGTHS",
    "DEFAULT_MAX_WATCH_OUTS",
    "DEFAULT_STRENGTH_PERCENTILE",
    "DEFAULT_WATCH_OUT_PERCENTILE",
    "InsightKind",
    "PlayerInsight",
    "PlayerInsightSummary",
    "build_player_insights",
]
