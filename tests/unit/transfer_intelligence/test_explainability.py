from __future__ import annotations

import pandas as pd
import pytest

from wc26.analytics.transfer_intelligence.explainability import (
    build_recommendation_explainability,
)
from wc26.analytics.transfer_intelligence.scoring import (
    calculate_mode_score,
)


def explainable_candidate(
    *,
    effective_heatmap_score_pct: float = 80.0,
    heatmap_similarity_score_pct: float | None = 80.0,
    has_heatmap_similarity: bool = True,
    same_final_role: bool = True,
    same_archetype: bool = True,
) -> pd.Series:
    return pd.Series(
        {
            "statistical_similarity_pct": 80.0,
            "role_fit_pct": 90.0,
            "spatial_similarity_pct": 80.0,
            "effective_heatmap_score_pct": (effective_heatmap_score_pct),
            "heatmap_similarity_score_pct": (heatmap_similarity_score_pct),
            "occupation_overlap_pct": 85.0,
            "lateral_profile_similarity_pct": 90.0,
            "vertical_profile_similarity_pct": 90.0,
            "player_quality_score": 80.0,
            "data_reliability_score": 80.0,
            "market_value_advantage_pct": 50.0,
            "age_suitability_pct": 50.0,
            "same_final_role": same_final_role,
            "same_archetype": same_archetype,
            "age": 24.0,
        }
    )


def test_explainability_matches_existing_mode_score() -> None:
    row = explainable_candidate()

    explanation = build_recommendation_explainability(
        row,
        mode="immediate",
        target_heatmap_profile={},
    )

    existing_score = calculate_mode_score(
        pd.DataFrame([row.to_dict()]),
        mode="immediate",
    ).iloc[0]

    assert explanation.mode == "immediate"

    assert explanation.score.final_score == pytest.approx(existing_score)

    assert explanation.score.weighted_signal_total == pytest.approx(79.9)

    assert explanation.score.bonus_total == pytest.approx(8.0)

    assert explanation.score.pre_clip_score == pytest.approx(87.9)


def test_explainability_contains_all_weighted_signals_in_model_order() -> None:
    explanation = build_recommendation_explainability(
        explainable_candidate(),
        mode="immediate",
        target_heatmap_profile={},
    )

    assert [signal.key for signal in explanation.signals] == [
        "statistical_similarity_pct",
        "role_fit_pct",
        "spatial_similarity_pct",
        "effective_heatmap_score_pct",
        "player_quality_score",
        "data_reliability_score",
        "market_value_advantage_pct",
        "age_suitability_pct",
    ]

    assert [signal.label for signal in explanation.signals] == [
        "Statistical similarity",
        "Role fit",
        "Spatial similarity",
        "Heatmap evidence",
        "Player quality",
        "Data reliability",
        "Market advantage",
        "Age suitability",
    ]


def test_explainability_exposes_heatmap_fallback_without_calling_it_measured() -> None:
    explanation = build_recommendation_explainability(
        explainable_candidate(
            effective_heatmap_score_pct=70.0,
            heatmap_similarity_score_pct=None,
            has_heatmap_similarity=False,
        ),
        mode="immediate",
        target_heatmap_profile={},
    )

    signals = {signal.key: signal for signal in explanation.signals}

    heatmap = signals["effective_heatmap_score_pct"]

    assert heatmap.source_score is None
    assert heatmap.input_score == pytest.approx(70.0)
    assert heatmap.weight == pytest.approx(0.12)
    assert heatmap.weighted_contribution == pytest.approx(8.4)
    assert heatmap.evidence_status == "fallback"

    assert heatmap.note == (
        "Direct heatmap evidence is unavailable; "
        "the configured neutral fallback is used "
        "for scoring."
    )


def test_explainability_exposes_explicit_mode_bonuses() -> None:
    explanation = build_recommendation_explainability(
        explainable_candidate(
            same_final_role=True,
            same_archetype=False,
        ),
        mode="immediate",
        target_heatmap_profile={},
    )

    bonuses = {bonus.key: bonus for bonus in explanation.bonuses}

    same_role = bonuses["same_final_role"]

    assert same_role.configured_points == pytest.approx(6.0)
    assert same_role.applied is True
    assert same_role.applied_points == pytest.approx(6.0)

    same_archetype = bonuses["same_archetype"]

    assert same_archetype.configured_points == pytest.approx(2.0)
    assert same_archetype.applied is False
    assert same_archetype.applied_points == pytest.approx(0.0)


def test_explainability_reasons_remain_structured() -> None:
    explanation = build_recommendation_explainability(
        explainable_candidate(),
        mode="immediate",
        target_heatmap_profile={},
    )

    assert explanation.reasons

    assert explanation.reasons[0].key == ("same_final_role")
    assert explanation.reasons[0].group == "role"
    assert explanation.reasons[0].text == ("same final role")


def test_explainability_to_dict_is_api_ready() -> None:
    explanation = build_recommendation_explainability(
        explainable_candidate(),
        mode="immediate",
        target_heatmap_profile={},
    )

    payload = explanation.to_dict()

    assert payload["mode"] == "immediate"

    score = payload["score"]

    assert isinstance(score, dict)
    assert score["final_score"] == pytest.approx(87.9)

    signals = payload["signals"]

    assert isinstance(signals, list)
    assert len(signals) == 8

    bonuses = payload["bonuses"]

    assert isinstance(bonuses, list)
    assert len(bonuses) == 2

    reasons = payload["reasons"]

    assert isinstance(reasons, list)
    assert reasons
