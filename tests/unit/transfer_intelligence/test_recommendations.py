from __future__ import annotations

import pandas as pd
import pytest

from wc26.analytics.transfer_intelligence import (
    recommendations,
)
from wc26.analytics.transfer_intelligence.config import (
    MODE_CONFIG,
)
from wc26.analytics.transfer_intelligence.explanations import (
    build_reason,
    classify_candidate,
    recommendation_strength,
)
from wc26.analytics.transfer_intelligence.recommendations import (
    filter_for_mode,
    generate_mode_results,
)
from wc26.analytics.transfer_intelligence.scoring import (
    calculate_mode_score,
)


def test_result_generation_uses_scoring_function() -> None:
    assert recommendations.calculate_mode_score is calculate_mode_score


def test_result_generation_uses_explanation_functions() -> None:
    assert recommendations.classify_candidate is classify_candidate
    assert recommendations.build_reason is build_reason
    assert recommendations.recommendation_strength is recommendation_strength


def candidate_row(
    player_id: int,
    *,
    age: float = 25.0,
    statistical_similarity_pct: float = 100.0,
    role_fit_pct: float = 100.0,
    player_quality_score: float = 100.0,
    data_reliability_score: float = 100.0,
) -> dict[str, float | int]:
    return {
        "player_id": player_id,
        "age": age,
        "statistical_similarity_pct": (statistical_similarity_pct),
        "role_fit_pct": role_fit_pct,
        "player_quality_score": player_quality_score,
        "data_reliability_score": data_reliability_score,
    }


@pytest.mark.parametrize(
    ("column", "threshold"),
    [
        (
            "statistical_similarity_pct",
            MODE_CONFIG["immediate"]["minimum_similarity"],
        ),
        (
            "role_fit_pct",
            MODE_CONFIG["immediate"]["minimum_role_fit"],
        ),
        (
            "player_quality_score",
            MODE_CONFIG["immediate"]["minimum_quality"],
        ),
        (
            "data_reliability_score",
            MODE_CONFIG["immediate"]["minimum_reliability"],
        ),
    ],
)
def test_filter_for_mode_rejects_scores_below_threshold(
    column: str,
    threshold: float,
) -> None:
    valid = candidate_row(
        1,
        age=25.0,
    )
    invalid = candidate_row(
        2,
        age=25.0,
    )
    invalid[column] = threshold - 0.01

    candidates = pd.DataFrame(
        [
            valid,
            invalid,
        ]
    )

    result = filter_for_mode(
        candidates,
        mode="immediate",
    )

    assert result["player_id"].tolist() == [1]


@pytest.mark.parametrize(
    "mode",
    [
        "immediate",
        "development",
    ],
)
def test_filter_for_mode_applies_maximum_age(
    mode: str,
) -> None:
    maximum_age = MODE_CONFIG[mode]["maximum_age"]

    assert maximum_age is not None

    candidates = pd.DataFrame(
        [
            candidate_row(
                1,
                age=maximum_age,
            ),
            candidate_row(
                2,
                age=maximum_age + 1,
            ),
        ]
    )

    result = filter_for_mode(
        candidates,
        mode=mode,
    )

    assert result["player_id"].tolist() == [1]


def test_filter_for_mode_applies_minimum_age() -> None:
    minimum_age = MODE_CONFIG["short_term"]["minimum_age"]

    assert minimum_age is not None

    candidates = pd.DataFrame(
        [
            candidate_row(
                1,
                age=minimum_age,
            ),
            candidate_row(
                2,
                age=minimum_age - 1,
            ),
        ]
    )

    result = filter_for_mode(
        candidates,
        mode="short_term",
    )

    assert result["player_id"].tolist() == [1]


def test_value_mode_does_not_filter_by_age() -> None:
    config = MODE_CONFIG["value"]

    assert config["minimum_age"] is None
    assert config["maximum_age"] is None

    candidates = pd.DataFrame(
        [
            candidate_row(
                1,
                age=18.0,
            ),
            candidate_row(
                2,
                age=40.0,
            ),
        ]
    )

    result = filter_for_mode(
        candidates,
        mode="value",
    )

    assert result["player_id"].tolist() == [1, 2]


@pytest.mark.parametrize(
    ("mode", "age"),
    [
        ("immediate", 25.0),
        ("development", 22.0),
        ("value", 25.0),
        ("short_term", 30.0),
    ],
)
def test_generated_recommendations_include_structured_explainability(
    mode: str,
    age: float,
) -> None:
    candidates = pd.DataFrame(
        [
            {
                "player_id": 101,
                "age": age,
                "statistical_similarity_pct": 80.0,
                "role_fit_pct": 90.0,
                "spatial_similarity_pct": 80.0,
                "effective_heatmap_score_pct": 70.0,
                "heatmap_similarity_score_pct": None,
                "has_heatmap_similarity": False,
                "occupation_overlap_pct": 0.0,
                "lateral_profile_similarity_pct": 0.0,
                "vertical_profile_similarity_pct": 0.0,
                "player_quality_score": 80.0,
                "data_reliability_score": 80.0,
                "market_value_advantage_pct": 70.0,
                "age_suitability_pct": 80.0,
                "same_final_role": True,
                "same_archetype": True,
            }
        ]
    )

    result = generate_mode_results(
        candidates,
        mode=mode,
        target_heatmap_profile={},
    )

    assert len(result) == 1

    row = result.iloc[0]

    explanation = row["explainability"]

    assert isinstance(
        explanation,
        dict,
    )

    assert explanation["mode"] == mode

    score = explanation["score"]

    assert isinstance(
        score,
        dict,
    )

    assert score["final_score"] == pytest.approx(row[f"{mode}_score"])

    signals = explanation["signals"]

    assert isinstance(
        signals,
        list,
    )

    assert len(signals) == 8

    heatmap = next(signal for signal in signals if signal["key"] == "effective_heatmap_score_pct")

    assert heatmap["source_score"] is None
    assert heatmap["input_score"] == pytest.approx(70.0)
    assert heatmap["evidence_status"] == "fallback"

    bonuses = explanation["bonuses"]

    assert isinstance(
        bonuses,
        list,
    )

    assert len(bonuses) == 2

    reasons = explanation["reasons"]

    assert isinstance(
        reasons,
        list,
    )

    assert reasons

    assert row["why_recommended"] == "; ".join(reason["text"] for reason in reasons)


def test_explainability_does_not_change_existing_ranking_order() -> None:
    candidates = pd.DataFrame(
        [
            {
                "player_id": 1,
                "age": 25.0,
                "statistical_similarity_pct": 90.0,
                "role_fit_pct": 95.0,
                "spatial_similarity_pct": 90.0,
                "effective_heatmap_score_pct": 90.0,
                "heatmap_similarity_score_pct": 90.0,
                "has_heatmap_similarity": True,
                "occupation_overlap_pct": 90.0,
                "lateral_profile_similarity_pct": 90.0,
                "vertical_profile_similarity_pct": 90.0,
                "player_quality_score": 90.0,
                "data_reliability_score": 90.0,
                "market_value_advantage_pct": 70.0,
                "age_suitability_pct": 70.0,
                "same_final_role": True,
                "same_archetype": True,
            },
            {
                "player_id": 2,
                "age": 25.0,
                "statistical_similarity_pct": 70.0,
                "role_fit_pct": 70.0,
                "spatial_similarity_pct": 70.0,
                "effective_heatmap_score_pct": 70.0,
                "heatmap_similarity_score_pct": 70.0,
                "has_heatmap_similarity": True,
                "occupation_overlap_pct": 70.0,
                "lateral_profile_similarity_pct": 70.0,
                "vertical_profile_similarity_pct": 70.0,
                "player_quality_score": 70.0,
                "data_reliability_score": 70.0,
                "market_value_advantage_pct": 50.0,
                "age_suitability_pct": 50.0,
                "same_final_role": False,
                "same_archetype": False,
            },
        ]
    )

    result = generate_mode_results(
        candidates,
        mode="immediate",
        target_heatmap_profile={},
    )

    assert result["player_id"].tolist() == [
        1,
        2,
    ]

    assert result["immediate_rank"].tolist() == [
        1,
        2,
    ]

    assert result["immediate_score"].astype(float).is_monotonic_decreasing

    assert all(
        isinstance(
            explanation,
            dict,
        )
        for explanation in result["explainability"]
    )
