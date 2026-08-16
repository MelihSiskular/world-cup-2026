from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from wc26.analytics.transfer_intelligence.scoring import (
    build_mode_score_breakdown,
    calculate_age_suitability,
    calculate_market_value_advantage,
    calculate_mode_score,
    calculate_role_fit,
    calculate_spatial_similarity,
    same_value_score,
)


def test_same_value_score_returns_match_score_only_for_matches() -> None:
    values = pd.Series(
        [
            "Playmaker",
            "Winger",
            None,
            "Playmaker",
        ]
    )

    result = same_value_score(
        values,
        target_value="Playmaker",
        match_score=25.0,
    )

    assert result.tolist() == [
        25.0,
        0.0,
        0.0,
        25.0,
    ]


def test_same_value_score_returns_zero_for_missing_target() -> None:
    values = pd.Series(
        [
            "Playmaker",
            "Winger",
        ]
    )

    result = same_value_score(
        values,
        target_value=np.nan,
        match_score=25.0,
    )

    assert result.tolist() == [0.0, 0.0]


def test_role_fit_reaches_full_score_for_complete_match() -> None:
    candidates = pd.DataFrame(
        [
            {
                "final_role": "Advanced Playmaker",
                "archetype": "Creator",
                "spatial_role": "Right Half-Space",
                "lateral_profile": "Right",
                "vertical_profile": "Advanced",
                "mobility_profile": "Mobile",
                "role_confidence_score": 100.0,
            }
        ]
    )

    target = pd.Series(
        {
            "final_role": "Advanced Playmaker",
            "archetype": "Creator",
            "spatial_role": "Right Half-Space",
            "lateral_profile": "Right",
            "vertical_profile": "Advanced",
            "mobility_profile": "Mobile",
        }
    )

    result = calculate_role_fit(
        candidates,
        target,
    )

    assert result.iloc[0] == pytest.approx(100.0)


def test_role_fit_is_reduced_by_low_role_confidence() -> None:
    candidates = pd.DataFrame(
        [
            {
                "final_role": "Advanced Playmaker",
                "archetype": "Creator",
                "spatial_role": "Right Half-Space",
                "lateral_profile": "Right",
                "vertical_profile": "Advanced",
                "mobility_profile": "Mobile",
                "role_confidence_score": 0.0,
            }
        ]
    )

    target = pd.Series(
        {
            "final_role": "Advanced Playmaker",
            "archetype": "Creator",
            "spatial_role": "Right Half-Space",
            "lateral_profile": "Right",
            "vertical_profile": "Advanced",
            "mobility_profile": "Mobile",
        }
    )

    result = calculate_role_fit(
        candidates,
        target,
    )

    assert result.iloc[0] == pytest.approx(80.0)


def test_spatial_similarity_returns_neutral_score_with_too_few_features() -> None:
    candidates = pd.DataFrame(
        {
            "weighted_mean_x": [40.0, 60.0],
            "weighted_mean_y": [30.0, 70.0],
        }
    )

    target = pd.Series(
        {
            "weighted_mean_x": 40.0,
            "weighted_mean_y": 30.0,
        }
    )

    result = calculate_spatial_similarity(
        candidates,
        target,
    )

    assert result.tolist() == [50.0, 50.0]


def test_spatial_similarity_rewards_closer_profile() -> None:
    candidates = pd.DataFrame(
        [
            {
                "weighted_mean_x": 40.0,
                "weighted_mean_y": 30.0,
                "spatial_spread": 10.0,
            },
            {
                "weighted_mean_x": 80.0,
                "weighted_mean_y": 80.0,
                "spatial_spread": 30.0,
            },
        ]
    )

    target = pd.Series(
        {
            "weighted_mean_x": 40.0,
            "weighted_mean_y": 30.0,
            "spatial_spread": 10.0,
        }
    )

    result = calculate_spatial_similarity(
        candidates,
        target,
    )

    assert result.iloc[0] == pytest.approx(100.0)
    assert result.iloc[0] > result.iloc[1]


def test_market_value_advantage_rewards_lower_cost() -> None:
    candidates = pd.DataFrame(
        {
            "market_value": [
                50_000_000,
                100_000_000,
                200_000_000,
            ]
        }
    )

    target = pd.Series(
        {
            "market_value": 100_000_000,
        }
    )

    result = calculate_market_value_advantage(
        candidates,
        target,
    )

    assert result.tolist() == [
        75.0,
        50.0,
        0.0,
    ]


def test_market_value_advantage_uses_percentiles_without_target_value() -> None:
    candidates = pd.DataFrame(
        {
            "market_value": [
                10_000_000,
                20_000_000,
                30_000_000,
            ]
        }
    )

    target = pd.Series(
        {
            "market_value": np.nan,
        }
    )

    result = calculate_market_value_advantage(
        candidates,
        target,
    )

    assert result.tolist() == pytest.approx(
        [
            66.67,
            33.33,
            0.0,
        ]
    )


def test_age_suitability_uses_base_score_without_target_age() -> None:
    candidates = pd.DataFrame(
        {
            "age": [
                18.0,
                26.0,
                34.0,
            ]
        }
    )

    target = pd.Series(
        {
            "age": np.nan,
        }
    )

    result = calculate_age_suitability(
        candidates,
        target,
    )

    assert result.tolist() == [
        100.0,
        50.0,
        0.0,
    ]


def test_immediate_mode_applies_weights_and_bonuses() -> None:
    candidates = pd.DataFrame(
        {
            "statistical_similarity_pct": [80.0],
            "role_fit_pct": [90.0],
            "spatial_similarity_pct": [80.0],
            "effective_heatmap_score_pct": [80.0],
            "player_quality_score": [80.0],
            "data_reliability_score": [80.0],
            "market_value_advantage_pct": [50.0],
            "age_suitability_pct": [50.0],
            "same_final_role": [True],
            "same_archetype": [True],
        }
    )

    result = calculate_mode_score(
        candidates,
        mode="immediate",
    )

    assert result.iloc[0] == pytest.approx(87.9)


def _immediate_score_candidate(
    *,
    statistical_similarity_pct: float = 80.0,
    role_fit_pct: float = 90.0,
    spatial_similarity_pct: float = 80.0,
    effective_heatmap_score_pct: float = 80.0,
    heatmap_similarity_score_pct: float | None = 80.0,
    has_heatmap_similarity: bool = True,
    player_quality_score: float = 80.0,
    data_reliability_score: float = 80.0,
    market_value_advantage_pct: float = 50.0,
    age_suitability_pct: float = 50.0,
    same_final_role: bool = True,
    same_archetype: bool = True,
) -> pd.Series:
    return pd.Series(
        {
            "statistical_similarity_pct": statistical_similarity_pct,
            "role_fit_pct": role_fit_pct,
            "spatial_similarity_pct": spatial_similarity_pct,
            "effective_heatmap_score_pct": effective_heatmap_score_pct,
            "heatmap_similarity_score_pct": heatmap_similarity_score_pct,
            "has_heatmap_similarity": has_heatmap_similarity,
            "player_quality_score": player_quality_score,
            "data_reliability_score": data_reliability_score,
            "market_value_advantage_pct": market_value_advantage_pct,
            "age_suitability_pct": age_suitability_pct,
            "same_final_role": same_final_role,
            "same_archetype": same_archetype,
        }
    )


def test_mode_score_breakdown_matches_existing_score() -> None:
    candidate = _immediate_score_candidate()

    breakdown = build_mode_score_breakdown(
        candidate,
        mode="immediate",
    )

    existing_score = calculate_mode_score(
        pd.DataFrame([candidate.to_dict()]),
        mode="immediate",
    ).iloc[0]

    assert breakdown.final_score == pytest.approx(existing_score)
    assert breakdown.weighted_signal_total == pytest.approx(79.9)
    assert breakdown.bonus_total == pytest.approx(8.0)
    assert breakdown.pre_clip_score == pytest.approx(87.9)
    assert breakdown.final_score == pytest.approx(87.9)
    assert breakdown.was_clipped is False

    assert [signal.key for signal in breakdown.signals] == [
        "statistical_similarity_pct",
        "role_fit_pct",
        "spatial_similarity_pct",
        "effective_heatmap_score_pct",
        "player_quality_score",
        "data_reliability_score",
        "market_value_advantage_pct",
        "age_suitability_pct",
    ]

    assert [bonus.key for bonus in breakdown.bonuses] == [
        "same_final_role",
        "same_archetype",
    ]


def test_mode_score_breakdown_reports_score_clipping() -> None:
    candidate = _immediate_score_candidate(
        statistical_similarity_pct=100.0,
        role_fit_pct=100.0,
        spatial_similarity_pct=100.0,
        effective_heatmap_score_pct=100.0,
        heatmap_similarity_score_pct=100.0,
        player_quality_score=100.0,
        data_reliability_score=100.0,
        market_value_advantage_pct=100.0,
        age_suitability_pct=100.0,
    )

    breakdown = build_mode_score_breakdown(
        candidate,
        mode="immediate",
    )

    assert breakdown.weighted_signal_total == pytest.approx(100.0)
    assert breakdown.bonus_total == pytest.approx(8.0)
    assert breakdown.pre_clip_score == pytest.approx(108.0)
    assert breakdown.final_score == pytest.approx(100.0)
    assert breakdown.was_clipped is True


def test_mode_score_breakdown_distinguishes_heatmap_fallback() -> None:
    candidate = _immediate_score_candidate(
        effective_heatmap_score_pct=70.0,
        heatmap_similarity_score_pct=None,
        has_heatmap_similarity=False,
    )

    breakdown = build_mode_score_breakdown(
        candidate,
        mode="immediate",
    )

    signals = {signal.key: signal for signal in breakdown.signals}

    heatmap = signals["effective_heatmap_score_pct"]

    assert heatmap.source_score is None
    assert heatmap.input_score == pytest.approx(70.0)
    assert heatmap.weight == pytest.approx(0.12)
    assert heatmap.weighted_contribution == pytest.approx(8.4)
    assert heatmap.evidence_status == "fallback"


def test_mode_score_breakdown_keeps_measured_zero_distinct_from_missing() -> None:
    candidate = _immediate_score_candidate(
        effective_heatmap_score_pct=0.0,
        heatmap_similarity_score_pct=0.0,
        has_heatmap_similarity=True,
    )

    breakdown = build_mode_score_breakdown(
        candidate,
        mode="immediate",
    )

    signals = {signal.key: signal for signal in breakdown.signals}

    heatmap = signals["effective_heatmap_score_pct"]

    assert heatmap.source_score == pytest.approx(0.0)
    assert heatmap.input_score == pytest.approx(0.0)
    assert heatmap.weighted_contribution == pytest.approx(0.0)
    assert heatmap.evidence_status == "available"
