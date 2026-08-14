"""Tests for position-aware percentile calculations."""

from __future__ import annotations

import pandas as pd
import pytest

from wc26.analytics.player_intelligence.metric_registry import (
    PositionGroup,
)
from wc26.analytics.player_intelligence.percentiles import (
    calculate_player_percentiles,
)


def build_midfielder_fixture() -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for index in range(20):
        rows.append(
            {
                "player_id": index + 1,
                "player_primary_position": "M",
                "total_minutes": 200,
                "stat_expectedAssists_per90": (index / 10),
                "stat_keyPass_per90": (index / 5),
                "stat_goalAssist_per90": (index / 20),
                "stat_bigChanceCreated_per90": (index / 10),
                "stat_totalProgression_per90": (100 + index),
                "stat_progressiveBallCarriesCount_per90": (2 + index / 10),
                "stat_totalProgressiveBallCarriesDistance_per90": (50 + index),
                "stat_ballCarriesCount_per90": (10 + index),
                "stat_totalPass_per90": (30 + index),
                "pass_accuracy_pct": (70 + index),
                "stat_touches_per90": (50 + index),
                "stat_possessionLostCtrl_per90": (30 - index),
                "stat_ballRecovery_per90": (2 + index / 10),
                "stat_totalTackle_per90": (1 + index / 10),
                "stat_wonTackle_per90": (index / 10),
                "stat_interceptionWon_per90": (index / 20),
                "duel_success_pct": (40 + index),
                "stat_expectedGoals_per90": (index / 20),
                "stat_totalShots_per90": (1 + index / 10),
                "stat_onTargetScoringAttempt_per90": (index / 20),
                "shot_on_target_pct": (25 + index),
                "stat_goals_per90": (index / 25),
                "stat_kilometersCovered_per90": (9 + index / 10),
                "stat_numberOfSprints_per90": (10 + index),
                "stat_topSpeed_max": (28 + index / 10),
            }
        )

    return pd.DataFrame(rows)


def metric_by_key(
    profile: object,
    key: str,
):
    metrics = profile.metrics

    return next(metric for metric in metrics if metric.metric_key == key)


def test_builds_same_position_percentiles() -> None:
    dataframe = build_midfielder_fixture()

    profile = calculate_player_percentiles(
        dataframe,
        player_id=20,
    )

    assert profile.position_group == PositionGroup.MIDFIELDER

    expected_assists = metric_by_key(
        profile,
        "expected_assists_per90",
    )

    assert expected_assists.value == pytest.approx(1.9)
    assert expected_assists.peer_count == 20
    assert expected_assists.percentile > 95


def test_lower_is_better_metric_is_inverted() -> None:
    dataframe = build_midfielder_fixture()

    profile = calculate_player_percentiles(
        dataframe,
        player_id=20,
    )

    possession_lost = metric_by_key(
        profile,
        "possession_lost_per90",
    )

    assert possession_lost.value == pytest.approx(11.0)

    assert possession_lost.percentile > 95


def test_target_does_not_need_to_meet_cohort_minimum_minutes() -> None:
    dataframe = build_midfielder_fixture()

    dataframe.loc[
        dataframe["player_id"].eq(20),
        "total_minutes",
    ] = 90

    profile = calculate_player_percentiles(
        dataframe,
        player_id=20,
    )

    expected_assists = metric_by_key(
        profile,
        "expected_assists_per90",
    )

    assert expected_assists.value == pytest.approx(1.9)

    assert expected_assists.peer_count == 19


def test_metric_value_is_preserved_when_peer_evidence_is_too_small() -> None:
    dataframe = build_midfielder_fixture()

    dataframe.loc[
        dataframe["player_id"] <= 15,
        "stat_expectedAssists_per90",
    ] = None

    profile = calculate_player_percentiles(
        dataframe,
        player_id=20,
        minimum_peer_count=10,
    )

    expected_assists = metric_by_key(
        profile,
        "expected_assists_per90",
    )

    assert expected_assists.value == pytest.approx(1.9)
    assert expected_assists.peer_count == 5
    assert expected_assists.percentile is None


def test_tied_distribution_stays_neutral() -> None:
    dataframe = build_midfielder_fixture()

    dataframe["stat_expectedAssists_per90"] = 0.5

    profile = calculate_player_percentiles(
        dataframe,
        player_id=10,
    )

    expected_assists = metric_by_key(
        profile,
        "expected_assists_per90",
    )

    assert expected_assists.percentile == pytest.approx(50.0)


def test_rejects_unknown_target_position() -> None:
    dataframe = build_midfielder_fixture()

    dataframe.loc[
        dataframe["player_id"].eq(1),
        "player_primary_position",
    ] = "X"

    with pytest.raises(
        ValueError,
        match="cannot be normalized",
    ):
        calculate_player_percentiles(
            dataframe,
            player_id=1,
        )
