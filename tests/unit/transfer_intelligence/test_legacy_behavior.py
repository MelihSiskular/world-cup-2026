from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from src.transfer_intelligence import find_replacements as legacy


def test_slugify_normalizes_accents_and_spaces() -> None:
    assert legacy.slugify("Michael Olise") == "michael_olise"
    assert legacy.slugify("Çağlar Söyüncü") == "caglar_soyuncu"
    assert legacy.slugify("  Player -- Name  ") == "player_name"


@pytest.mark.parametrize(
    ("value", "default", "expected"),
    [
        ("12.5", 0.0, 12.5),
        (10, 0.0, 10.0),
        (None, -1.0, -1.0),
        (np.nan, 25.0, 25.0),
        ("not-a-number", 7.0, 7.0),
    ],
)
def test_safe_float(
    value: object,
    default: float,
    expected: float,
) -> None:
    assert legacy.safe_float(value, default=default) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("  Michael OLISE  ", "michael olise"),
        ("Florian Wirtz", "florian wirtz"),
        (None, ""),
        (np.nan, ""),
    ],
)
def test_normalize_text(value: object, expected: str) -> None:
    assert legacy.normalize_text(value) == expected


@pytest.fixture
def players() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"player_id": 1, "player_name": "Michael Olise"},
            {"player_id": 2, "player_name": "Florian Wirtz"},
            {"player_id": 3, "player_name": "Alex Smith"},
            {"player_id": 4, "player_name": "Alex Jones"},
        ]
    )


def test_resolve_player_supports_case_insensitive_exact_match(
    players: pd.DataFrame,
) -> None:
    result = legacy.resolve_player(players, "michael olise")

    assert result["player_id"] == 1
    assert result["player_name"] == "Michael Olise"


def test_resolve_player_supports_unique_partial_match(
    players: pd.DataFrame,
) -> None:
    result = legacy.resolve_player(players, "Wirtz")

    assert result["player_id"] == 2


def test_resolve_player_rejects_missing_player(
    players: pd.DataFrame,
) -> None:
    with pytest.raises(ValueError, match="Player not found"):
        legacy.resolve_player(players, "Unknown Player")


def test_resolve_player_rejects_ambiguous_partial_match(
    players: pd.DataFrame,
) -> None:
    with pytest.raises(ValueError, match="Multiple players matched"):
        legacy.resolve_player(players, "Alex")


def test_same_value_score_rewards_only_exact_matches() -> None:
    values = pd.Series(["Playmaker", "Winger", None, "Playmaker"])

    result = legacy.same_value_score(
        values,
        target_value="Playmaker",
        match_score=25.0,
    )

    assert result.tolist() == [25.0, 0.0, 0.0, 25.0]


def test_market_value_advantage_uses_target_value_ratio() -> None:
    candidates = pd.DataFrame(
        {
            "market_value": [
                50_000_000,
                100_000_000,
                200_000_000,
            ]
        }
    )
    target = pd.Series({"market_value": 100_000_000})

    result = legacy.calculate_market_value_advantage(
        candidates,
        target,
    )

    assert result.tolist() == [75.0, 50.0, 0.0]


def test_age_suitability_rewards_younger_players() -> None:
    candidates = pd.DataFrame({"age": [22, 26, 30]})
    target = pd.Series({"age": 26})

    result = legacy.calculate_age_suitability(
        candidates,
        target,
    )

    assert result.tolist() == [87.0, 50.0, 1.0]


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (80.0, "Elite"),
        (79.99, "Strong"),
        (72.0, "Strong"),
        (64.0, "Good"),
        (56.0, "Moderate"),
        (55.99, "Low"),
    ],
)
def test_recommendation_strength_boundaries(
    score: float,
    expected: str,
) -> None:
    assert legacy.recommendation_strength(score) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (2_500_000, "€2.5M"),
        (25_000, "€25K"),
        (900, "€900"),
        (np.nan, "-"),
    ],
)
def test_format_market_value(
    value: float,
    expected: str,
) -> None:
    assert legacy.format_market_value(value) == expected


def test_immediate_mode_score_uses_current_weights() -> None:
    candidates = pd.DataFrame(
        {
            "statistical_similarity_pct": [100.0],
            "role_fit_pct": [0.0],
            "spatial_similarity_pct": [0.0],
            "effective_heatmap_score_pct": [0.0],
            "player_quality_score": [0.0],
            "data_reliability_score": [0.0],
            "market_value_advantage_pct": [0.0],
            "age_suitability_pct": [0.0],
            "same_final_role": [False],
            "same_archetype": [False],
        }
    )

    result = legacy.calculate_mode_score(
        candidates,
        mode="immediate",
    )

    assert result.iloc[0] == pytest.approx(20.0)


def test_immediate_mode_adds_role_and_archetype_bonuses() -> None:
    candidates = pd.DataFrame(
        {
            "statistical_similarity_pct": [0.0],
            "role_fit_pct": [0.0],
            "spatial_similarity_pct": [0.0],
            "effective_heatmap_score_pct": [0.0],
            "player_quality_score": [0.0],
            "data_reliability_score": [0.0],
            "market_value_advantage_pct": [0.0],
            "age_suitability_pct": [0.0],
            "same_final_role": [True],
            "same_archetype": [True],
        }
    )

    result = legacy.calculate_mode_score(
        candidates,
        mode="immediate",
    )

    assert result.iloc[0] == pytest.approx(8.0)


def test_filter_for_immediate_mode_applies_thresholds() -> None:
    candidates = pd.DataFrame(
        [
            {
                "player_name": "Eligible Player",
                "statistical_similarity_pct": 70.0,
                "role_fit_pct": 70.0,
                "player_quality_score": 70.0,
                "data_reliability_score": 70.0,
                "age": 28.0,
            },
            {
                "player_name": "Low Reliability",
                "statistical_similarity_pct": 70.0,
                "role_fit_pct": 70.0,
                "player_quality_score": 70.0,
                "data_reliability_score": 40.0,
                "age": 28.0,
            },
            {
                "player_name": "Too Old",
                "statistical_similarity_pct": 70.0,
                "role_fit_pct": 70.0,
                "player_quality_score": 70.0,
                "data_reliability_score": 70.0,
                "age": 34.0,
            },
        ]
    )

    result = legacy.filter_for_mode(
        candidates,
        mode="immediate",
    )

    assert result["player_name"].tolist() == ["Eligible Player"]


def test_generate_mode_results_preserves_ranking_behavior() -> None:
    candidates = pd.DataFrame(
        [
            {
                "player_name": "Candidate A",
                "statistical_similarity_pct": 80.0,
                "role_fit_pct": 90.0,
                "spatial_similarity_pct": 80.0,
                "effective_heatmap_score_pct": 80.0,
                "heatmap_similarity_score_pct": 80.0,
                "occupation_overlap_pct": 80.0,
                "lateral_profile_similarity_pct": 80.0,
                "vertical_profile_similarity_pct": 80.0,
                "player_quality_score": 80.0,
                "data_reliability_score": 80.0,
                "market_value_advantage_pct": 50.0,
                "age_suitability_pct": 50.0,
                "same_final_role": True,
                "same_archetype": True,
                "has_heatmap_similarity": True,
                "age": 26.0,
            },
            {
                "player_name": "Candidate B",
                "statistical_similarity_pct": 60.0,
                "role_fit_pct": 60.0,
                "spatial_similarity_pct": 60.0,
                "effective_heatmap_score_pct": 60.0,
                "heatmap_similarity_score_pct": np.nan,
                "occupation_overlap_pct": np.nan,
                "lateral_profile_similarity_pct": np.nan,
                "vertical_profile_similarity_pct": np.nan,
                "player_quality_score": 60.0,
                "data_reliability_score": 60.0,
                "market_value_advantage_pct": 60.0,
                "age_suitability_pct": 60.0,
                "same_final_role": False,
                "same_archetype": False,
                "has_heatmap_similarity": False,
                "age": 27.0,
            },
        ]
    )

    result = legacy.generate_mode_results(
        base_candidates=candidates,
        mode="immediate",
        target_heatmap_profile={},
    )

    assert result["player_name"].tolist() == [
        "Candidate A",
        "Candidate B",
    ]
    assert result["immediate_rank"].tolist() == [1, 2]
    assert result.loc[0, "immediate_score"] == pytest.approx(87.9)
    assert result.loc[0, "recommendation_type"] == ("Direct tactical replacement")
    assert (
        "same final role"
        in result.loc[
            0,
            "why_recommended",
        ]
    )
