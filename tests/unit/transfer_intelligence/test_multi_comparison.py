"""Tests for generic multi-player comparison evidence."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from wc26.analytics.transfer_intelligence.catalog import (
    TransferDataCatalog,
)
from wc26.analytics.transfer_intelligence.errors import (
    InvalidMultiPlayerComparisonRequestError,
)
from wc26.analytics.transfer_intelligence.models import (
    MultiPlayerComparisonRequest,
)
from wc26.analytics.transfer_intelligence.multi_comparison import (
    run_multi_player_comparison_from_catalog,
)


def _player(
    player_id: int,
    player_name: str,
    *,
    position: str,
    market_value: float | None,
    spatial_values: tuple[
        float | None,
        float | None,
        float | None,
    ],
) -> dict[str, object]:
    weighted_mean_x, weighted_mean_y, spatial_spread = spatial_values

    return {
        "player_id": player_id,
        "player_name": player_name,
        "national_team_name": f"Team {player_id}",
        "country_name": f"Country {player_id}",
        "country_alpha3": f"C{player_id:02d}",
        "position": position,
        "final_role": "Central Half-Space Creator",
        "archetype": "Wide Creator",
        "spatial_role": "Right Half-Space",
        "lateral_profile": "Right",
        "vertical_profile": "Advanced",
        "mobility_profile": "Mobile",
        "age": 20 + player_id,
        "market_value": market_value,
        "market_value_currency": "EUR",
        "minutes": 500 + player_id,
        "role_confidence_score": 80.0,
        "data_reliability_score": 0.8,
        "player_quality_score": 75.0,
        "weighted_mean_x": weighted_mean_x,
        "weighted_mean_y": weighted_mean_y,
        "spatial_spread": spatial_spread,
    }


def _catalog() -> TransferDataCatalog:
    players = pd.DataFrame(
        [
            _player(
                1,
                "Target Player",
                position="M",
                market_value=100_000_000,
                spatial_values=(
                    50.0,
                    45.0,
                    12.0,
                ),
            ),
            _player(
                2,
                "Candidate Two",
                position="M",
                market_value=80_000_000,
                spatial_values=(
                    52.0,
                    46.0,
                    13.0,
                ),
            ),
            _player(
                3,
                "Candidate Three",
                position="M",
                market_value=60_000_000,
                spatial_values=(
                    65.0,
                    58.0,
                    20.0,
                ),
            ),
            _player(
                4,
                "Candidate Four",
                position="M",
                market_value=40_000_000,
                spatial_values=(
                    42.0,
                    38.0,
                    9.0,
                ),
            ),
            _player(
                5,
                "Missing Spatial Player",
                position="M",
                market_value=30_000_000,
                spatial_values=(
                    None,
                    None,
                    None,
                ),
            ),
            _player(
                6,
                "Different Position",
                position="F",
                market_value=50_000_000,
                spatial_values=(
                    70.0,
                    60.0,
                    18.0,
                ),
            ),
        ]
    )

    similarity = pd.DataFrame(
        [
            {
                "source_player_id": 1,
                "target_player_id": 2,
                "overall_similarity_pct": 91.0,
            },
            {
                "source_player_id": 3,
                "target_player_id": 1,
                "overall_similarity_pct": 82.0,
            },
        ]
    )

    heatmap_similarity = pd.DataFrame(
        [
            {
                "target_player_id": 1,
                "candidate_player_id": 2,
                "heatmap_similarity_score_pct": 88.0,
            },
            {
                "target_player_id": 3,
                "candidate_player_id": 1,
                "heatmap_similarity_score_pct": 76.0,
            },
        ]
    )

    tournament_summary = pd.DataFrame(
        [
            {
                "player_id": player_id,
                "stat_goalAssist": float(player_id + 4),
                "stat_goalAssist_per90": round(
                    (player_id + 4) / 12,
                    2,
                ),
                "stat_expectedAssists": float(player_id) + 0.5,
                "stat_expectedAssists_per90": float(player_id) / 10,
                "stat_keyPass": float(player_id * 3),
                "stat_keyPass_per90": float(player_id) / 2,
                "stat_bigChanceCreated": float(player_id + 1),
                "stat_bigChanceCreated_per90": float(player_id) / 5,
                "stat_totalProgression": float(player_id * 20),
                "stat_totalProgression_per90": float(player_id * 2),
                "stat_progressiveBallCarriesCount": float(player_id * 4),
                "stat_progressiveBallCarriesCount_per90": float(player_id) / 2,
                "stat_ballCarriesCount": float(player_id * 10),
                "stat_ballCarriesCount_per90": float(player_id),
                "stat_totalBallCarriesDistance": float(player_id * 100),
                "stat_totalBallCarriesDistance_per90": float(player_id * 10),
            }
            for player_id in range(1, 7)
        ]
    )

    return TransferDataCatalog(
        players=players,
        similarity=similarity,
        heatmap_similarity=(heatmap_similarity),
        heatmap_profiles=pd.DataFrame(),
        player_tournament_summary=(tournament_summary),
    )


def _request(
    *,
    target_player_id: int = 1,
    candidate_player_ids: tuple[
        int,
        ...,
    ] = (2,),
    role_metric_scope: str = "target",
) -> MultiPlayerComparisonRequest:
    return MultiPlayerComparisonRequest(
        target_player_id=target_player_id,
        candidate_player_ids=(candidate_player_ids),
        features=Path("features.csv"),
        similarity=Path("similarity.csv"),
        heatmap_similarity=Path("heatmap-similarity.csv"),
        heatmap_profiles=Path("heatmap-profiles.csv"),
        role_metric_scope=role_metric_scope,
    )


def test_preserves_requested_candidate_order_and_pair_evidence() -> None:
    result = run_multi_player_comparison_from_catalog(
        _request(
            candidate_player_ids=(
                3,
                2,
            ),
        ),
        _catalog(),
    )

    assert result.target.player_id == 1

    assert [candidate.player.player_id for candidate in result.candidates] == [
        3,
        2,
    ]

    assert result.candidates[0].evidence.statistical_similarity_pct == 82.0

    assert result.candidates[0].evidence.heatmap_similarity_score_pct == 76.0

    assert result.candidates[1].evidence.statistical_similarity_pct == 91.0

    assert result.candidates[1].evidence.heatmap_similarity_score_pct == 88.0


def test_compares_every_player_using_the_target_final_role_metrics() -> None:
    result = run_multi_player_comparison_from_catalog(
        _request(
            candidate_player_ids=(
                3,
                2,
            ),
        ),
        _catalog(),
    )

    assert [group.key for group in result.role_metrics] == [
        "creativity",
        "progression",
    ]

    assists = result.role_metrics[0].metrics[0]

    assert assists.key == "goalAssist"
    assert [value.player_id for value in assists.values] == [
        1,
        3,
        2,
    ]
    assert [value.total for value in assists.values] == [
        5.0,
        7.0,
        6.0,
    ]
    assert [value.per90 for value in assists.values] == [
        0.42,
        0.58,
        0.5,
    ]


def test_preserves_zero_and_reports_missing_role_metric_values() -> None:
    catalog = _catalog()

    catalog.player_tournament_summary.loc[
        catalog.player_tournament_summary["player_id"].eq(2),
        [
            "stat_goalAssist",
            "stat_goalAssist_per90",
        ],
    ] = pd.NA

    catalog.player_tournament_summary.loc[
        catalog.player_tournament_summary["player_id"].eq(4),
        [
            "stat_goalAssist",
            "stat_goalAssist_per90",
        ],
    ] = 0

    result = run_multi_player_comparison_from_catalog(
        _request(
            candidate_player_ids=(
                2,
                4,
            ),
        ),
        catalog,
    )

    values = result.role_metrics[0].metrics[0].values

    assert values[1].total is None
    assert values[1].per90 is None
    assert values[2].total == 0.0
    assert values[2].per90 == 0.0


def test_keeps_selected_player_when_pair_evidence_is_missing() -> None:
    result = run_multi_player_comparison_from_catalog(
        _request(
            candidate_player_ids=(4,),
        ),
        _catalog(),
    )

    candidate = result.candidates[0]

    assert candidate.player.player_id == 4

    assert candidate.evidence.statistical_similarity_pct is None

    assert candidate.evidence.heatmap_similarity_score_pct is None

    assert candidate.evidence.role_fit_pct is not None

    assert candidate.evidence.spatial_similarity_pct is not None

    assert candidate.evidence.market_value_advantage_pct is not None


def test_reports_missing_spatial_evidence_as_none() -> None:
    result = run_multi_player_comparison_from_catalog(
        _request(
            candidate_player_ids=(5,),
        ),
        _catalog(),
    )

    assert result.candidates[0].evidence.spatial_similarity_pct is None


@pytest.mark.parametrize(
    (
        "target_player_id",
        "candidate_player_ids",
        "message",
    ),
    [
        (
            0,
            (2,),
            "Target player ID must be",
        ),
        (
            1,
            (),
            "between one and three",
        ),
        (
            1,
            (2, 3, 4, 5),
            "between one and three",
        ),
        (
            1,
            (0,),
            "Candidate player IDs must be",
        ),
        (
            1,
            (1,),
            "must be unique",
        ),
        (
            1,
            (2, 2),
            "must be unique",
        ),
    ],
)
def test_rejects_invalid_comparison_identifier_sets(
    target_player_id: int,
    candidate_player_ids: tuple[
        int,
        ...,
    ],
    message: str,
) -> None:
    with pytest.raises(
        InvalidMultiPlayerComparisonRequestError,
        match=message,
    ):
        run_multi_player_comparison_from_catalog(
            _request(
                target_player_id=(target_player_id),
                candidate_player_ids=(candidate_player_ids),
            ),
            _catalog(),
        )


def test_rejects_candidates_from_a_different_position() -> None:
    with pytest.raises(
        InvalidMultiPlayerComparisonRequestError,
        match="must share",
    ):
        run_multi_player_comparison_from_catalog(
            _request(
                candidate_player_ids=(6,),
            ),
            _catalog(),
        )


def test_spatial_score_uses_the_complete_same_position_cohort() -> None:
    catalog = _catalog()

    single_result = run_multi_player_comparison_from_catalog(
        _request(
            candidate_player_ids=(2,),
        ),
        catalog,
    )

    multi_result = run_multi_player_comparison_from_catalog(
        _request(
            candidate_player_ids=(
                2,
                3,
            ),
        ),
        catalog,
    )

    assert (
        single_result.candidates[0].evidence.spatial_similarity_pct
        == multi_result.candidates[0].evidence.spatial_similarity_pct
    )


def test_serializes_null_evidence_without_fallback_scores() -> None:
    result = run_multi_player_comparison_from_catalog(
        _request(
            candidate_player_ids=(
                4,
                5,
            ),
        ),
        _catalog(),
    )

    payload = result.to_dict()

    candidates = payload["candidates"]

    assert isinstance(
        candidates,
        list,
    )

    assert candidates[0]["evidence"]["statistical_similarity_pct"] is None

    assert candidates[1]["evidence"]["spatial_similarity_pct"] is None


def test_combines_target_and_candidate_role_metric_duties() -> None:
    catalog = _catalog()

    catalog.players.loc[
        catalog.players["player_id"].eq(2),
        "final_role",
    ] = "Creative Central Midfielder"

    passing_columns = {
        "stat_totalPass": 120.0,
        "stat_totalPass_per90": 18.0,
        "stat_accuratePass": 105.0,
        "stat_accuratePass_per90": 15.5,
        "stat_totalLongBalls": 20.0,
        "stat_totalLongBalls_per90": 3.0,
        "stat_accurateLongBalls": 14.0,
        "stat_accurateLongBalls_per90": 2.1,
    }

    for (
        column,
        value,
    ) in passing_columns.items():
        catalog.player_tournament_summary[column] = value

    result = run_multi_player_comparison_from_catalog(
        _request(
            candidate_player_ids=(2,),
            role_metric_scope=("all_players"),
        ),
        catalog,
    )

    assert [group.key for group in result.role_metrics] == [
        "creativity",
        "passing_volume",
        "progression",
    ]

    metric_keys = [metric.key for group in result.role_metrics for metric in group.metrics]

    assert len(metric_keys) == len(set(metric_keys))

    total_pass = next(
        metric
        for group in result.role_metrics
        for metric in group.metrics
        if metric.key == "totalPass"
    )

    assert [value.player_id for value in total_pass.values] == [
        1,
        2,
    ]

    assert all(value.total == 120.0 for value in total_pass.values)


def test_target_role_metric_scope_remains_the_default() -> None:
    result = run_multi_player_comparison_from_catalog(
        _request(),
        _catalog(),
    )

    assert [group.key for group in result.role_metrics] == [
        "creativity",
        "progression",
    ]
