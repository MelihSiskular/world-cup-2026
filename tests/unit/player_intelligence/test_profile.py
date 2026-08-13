"""Tests for enriched player-intelligence profiles."""

from __future__ import annotations

import pandas as pd

from wc26.analytics.player_intelligence import (
    MetricGroup,
    PositionGroup,
    build_player_intelligence_profile,
)


def build_dataframe() -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for index in range(20):
        player_id = index + 1

        rows.append(
            {
                "player_id": player_id,
                "player_primary_position": "M",
                "matches_played": 5,
                "starts": 4,
                "substitute_appearances": 1,
                "captain_appearances": 0,
                "total_minutes": 200,
                "formations_used": 2,
                "primary_formation": "4-2-3-1",
                "primary_lineup_position": "M",
                "stat_expectedAssists_per90": (index / 10),
                "stat_progressiveBallCarriesCount_per90": (2 + index / 10),
                "stat_possessionLostCtrl_per90": (30 - index),
                "stat_expectedGoals_per90": (index / 20),
                "stat_numberOfSprints_per90": (10 + index),
            }
        )

    return pd.DataFrame(rows)


def test_builds_tournament_context() -> None:
    profile = build_player_intelligence_profile(
        build_dataframe(),
        player_id=20,
    )

    assert profile.player_id == 20
    assert profile.position_group == PositionGroup.MIDFIELDER

    assert profile.tournament.matches == 5
    assert profile.tournament.starts == 4
    assert profile.tournament.minutes == 200
    assert profile.tournament.primary_formation == "4-2-3-1"


def test_groups_metrics_by_analytical_family() -> None:
    profile = build_player_intelligence_profile(
        build_dataframe(),
        player_id=20,
    )

    groups = {group.key: group for group in profile.groups}

    assert MetricGroup.CREATION in groups
    assert MetricGroup.PROGRESSION in groups
    assert MetricGroup.POSSESSION in groups
    assert MetricGroup.SCORING in groups
    assert MetricGroup.PHYSICAL in groups

    creation_keys = {metric.key for metric in groups[MetricGroup.CREATION].metrics}

    assert "expected_assists_per90" in creation_keys


def test_exposes_strengths_from_percentile_engine() -> None:
    profile = build_player_intelligence_profile(
        build_dataframe(),
        player_id=20,
    )

    strength_keys = {insight.metric_key for insight in profile.strengths}

    assert "expected_assists_per90" in strength_keys


def test_reports_target_sample_eligibility() -> None:
    dataframe = build_dataframe()

    dataframe.loc[
        dataframe["player_id"].eq(20),
        "total_minutes",
    ] = 90

    profile = build_player_intelligence_profile(
        dataframe,
        player_id=20,
    )

    assert profile.sample.target_minutes == 90

    assert profile.sample.minimum_peer_minutes == 180

    assert profile.sample.target_meets_peer_minimum is False


def test_low_minute_target_still_receives_percentiles() -> None:
    dataframe = build_dataframe()

    dataframe.loc[
        dataframe["player_id"].eq(20),
        "total_minutes",
    ] = 90

    profile = build_player_intelligence_profile(
        dataframe,
        player_id=20,
    )

    creation_group = next(group for group in profile.groups if (group.key == MetricGroup.CREATION))

    metric = next(
        metric for metric in creation_group.metrics if (metric.key == "expected_assists_per90")
    )

    assert metric.peer_count == 19
    assert metric.performance_percentile > 95
