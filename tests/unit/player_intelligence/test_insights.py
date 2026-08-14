"""Tests for strengths and watch-out interpretation."""

from __future__ import annotations

import pytest

from wc26.analytics.player_intelligence.insights import (
    InsightKind,
    build_player_insights,
)
from wc26.analytics.player_intelligence.metric_registry import (
    MetricGroup,
    PositionGroup,
)
from wc26.analytics.player_intelligence.percentiles import (
    MetricPercentileResult,
    PlayerPercentileProfile,
)


def build_profile(
    metrics: tuple[MetricPercentileResult, ...],
) -> PlayerPercentileProfile:
    return PlayerPercentileProfile(
        player_id=978838,
        position_group=PositionGroup.MIDFIELDER,
        minimum_cohort_minutes=180,
        metrics=metrics,
    )


def metric(
    key: str,
    percentile: float | None,
    *,
    value: float = 1.0,
    peer_count: int = 100,
) -> MetricPercentileResult:
    return MetricPercentileResult(
        metric_key=key,
        value=value,
        percentile=percentile,
        peer_count=peer_count,
    )


def test_selects_strengths_from_distinct_metric_groups() -> None:
    profile = build_profile(
        (
            metric(
                "expected_assists_per90",
                99,
            ),
            metric(
                "key_passes_per90",
                98,
            ),
            metric(
                "progressive_carries_per90",
                97,
            ),
            metric(
                "expected_goals_per90",
                96,
            ),
            metric(
                "sprints_per90",
                91,
            ),
        )
    )

    summary = build_player_insights(profile)

    assert [insight.metric_key for insight in summary.strengths] == [
        "expected_assists_per90",
        "progressive_carries_per90",
        "expected_goals_per90",
        "sprints_per90",
    ]


def test_watch_outs_use_performance_percentile() -> None:
    profile = build_profile(
        (
            metric(
                "possession_lost_per90",
                5,
                value=18,
            ),
        )
    )

    summary = build_player_insights(profile)

    assert len(summary.watch_outs) == 1

    insight = summary.watch_outs[0]

    assert insight.kind == InsightKind.WATCH_OUT

    assert insight.metric_key == "possession_lost_per90"

    assert insight.percentile == 5


def test_metric_without_percentile_does_not_generate_insight() -> None:
    profile = build_profile(
        (
            metric(
                "expected_assists_per90",
                None,
                value=0.4533,
                peer_count=5,
            ),
        )
    )

    summary = build_player_insights(profile)

    assert summary.strengths == ()
    assert summary.watch_outs == ()


def test_neutral_metrics_do_not_generate_insights() -> None:
    profile = build_profile(
        (
            metric(
                "expected_assists_per90",
                60,
            ),
            metric(
                "progressive_carries_per90",
                55,
            ),
        )
    )

    summary = build_player_insights(profile)

    assert summary.strengths == ()
    assert summary.watch_outs == ()


def test_threshold_boundaries_are_inclusive() -> None:
    profile = build_profile(
        (
            metric(
                "expected_assists_per90",
                85,
            ),
            metric(
                "possession_lost_per90",
                20,
            ),
        )
    )

    summary = build_player_insights(profile)

    assert len(summary.strengths) == 1

    assert len(summary.watch_outs) == 1


def test_insight_contains_backend_owned_evidence() -> None:
    profile = build_profile(
        (
            metric(
                "expected_assists_per90",
                98.8,
                value=0.4533,
                peer_count=216,
            ),
        )
    )

    summary = build_player_insights(profile)

    insight = summary.strengths[0]

    assert insight.group == MetricGroup.CREATION

    assert insight.group_label == "Chance creation"

    assert insight.metric_short_label == "xA / 90"

    assert insight.evidence == (
        "xA / 90 ranks at the 98.8 performance percentile among 216 eligible same-position players."
    )


def test_rejects_overlapping_thresholds() -> None:
    profile = build_profile(())

    with pytest.raises(
        ValueError,
        match="lower than",
    ):
        build_player_insights(
            profile,
            strength_percentile=50,
            watch_out_percentile=50,
        )
