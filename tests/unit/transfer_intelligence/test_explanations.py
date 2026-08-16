from __future__ import annotations

import pandas as pd

from wc26.analytics.transfer_intelligence.explanations import (
    build_reason,
    build_reason_items,
)


def recommendation_row(
    *,
    same_final_role: bool = False,
    same_archetype: bool = False,
    statistical_similarity_pct: float = 0.0,
    role_fit_pct: float = 0.0,
    spatial_similarity_pct: float = 0.0,
    heatmap_similarity_score_pct: float | None = None,
    occupation_overlap_pct: float = 0.0,
    lateral_profile_similarity_pct: float = 0.0,
    vertical_profile_similarity_pct: float = 0.0,
    has_heatmap_similarity: bool = False,
    market_value_advantage_pct: float = 0.0,
    age: float = 25.0,
    data_reliability_score: float = 50.0,
) -> pd.Series:
    return pd.Series(
        {
            "same_final_role": same_final_role,
            "same_archetype": same_archetype,
            "statistical_similarity_pct": statistical_similarity_pct,
            "role_fit_pct": role_fit_pct,
            "spatial_similarity_pct": spatial_similarity_pct,
            "heatmap_similarity_score_pct": heatmap_similarity_score_pct,
            "occupation_overlap_pct": occupation_overlap_pct,
            "lateral_profile_similarity_pct": lateral_profile_similarity_pct,
            "vertical_profile_similarity_pct": vertical_profile_similarity_pct,
            "has_heatmap_similarity": has_heatmap_similarity,
            "market_value_advantage_pct": market_value_advantage_pct,
            "age": age,
            "data_reliability_score": data_reliability_score,
        }
    )


def test_build_reason_uses_structured_items_without_changing_text() -> None:
    row = recommendation_row(
        same_final_role=True,
        same_archetype=True,
        statistical_similarity_pct=80.0,
        role_fit_pct=90.0,
        spatial_similarity_pct=75.0,
    )

    items = build_reason_items(
        row,
        mode="immediate",
        target_heatmap_profile={},
    )

    result = build_reason(
        row,
        mode="immediate",
        target_heatmap_profile={},
    )

    assert result == "; ".join(item.text for item in items)

    assert result == (
        "same final role; "
        "same statistical archetype; "
        "very strong statistical similarity (80.0%); "
        "similar average-position profile (75.0%)"
    )


def test_reason_items_keep_one_reason_per_group() -> None:
    row = recommendation_row(
        same_final_role=True,
        role_fit_pct=95.0,
    )

    items = build_reason_items(
        row,
        mode="immediate",
        target_heatmap_profile={},
    )

    role_items = [item for item in items if item.group == "role"]

    assert len(role_items) == 1
    assert role_items[0].key == "same_final_role"
    assert role_items[0].text == "same final role"


def test_reason_items_do_not_treat_heatmap_fallback_as_measured_evidence() -> None:
    row = recommendation_row(
        statistical_similarity_pct=60.0,
        heatmap_similarity_score_pct=None,
        has_heatmap_similarity=False,
    )

    items = build_reason_items(
        row,
        mode="immediate",
        target_heatmap_profile={},
    )

    keys = {item.key for item in items}

    assert "statistical_similarity" in keys
    assert "heatmap_similarity" not in keys
    assert "heatmap_overlap" not in keys
    assert "heatmap_structure" not in keys
    assert "heatmap_zone" not in keys


def test_reason_items_preserve_measured_zero_heatmap_as_evidence_without_praise() -> None:
    row = recommendation_row(
        heatmap_similarity_score_pct=0.0,
        has_heatmap_similarity=True,
    )

    items = build_reason_items(
        row,
        mode="immediate",
        target_heatmap_profile={},
    )

    keys = {item.key for item in items}

    assert "heatmap_similarity" not in keys


def test_reason_items_limit_output_to_four_reasons() -> None:
    row = recommendation_row(
        same_final_role=True,
        same_archetype=True,
        statistical_similarity_pct=95.0,
        role_fit_pct=95.0,
        spatial_similarity_pct=95.0,
        heatmap_similarity_score_pct=95.0,
        occupation_overlap_pct=95.0,
        lateral_profile_similarity_pct=95.0,
        vertical_profile_similarity_pct=95.0,
        has_heatmap_similarity=True,
        market_value_advantage_pct=95.0,
    )

    items = build_reason_items(
        row,
        mode="value",
        target_heatmap_profile={},
    )

    assert len(items) == 4
    assert len({item.group for item in items}) == 4


def test_reason_items_return_balanced_profile_when_no_positive_reason_exists() -> None:
    row = recommendation_row()

    items = build_reason_items(
        row,
        mode="immediate",
        target_heatmap_profile={},
    )

    assert len(items) == 1
    assert items[0].key == "balanced_profile"
    assert items[0].group == "balanced"
    assert items[0].text == ("balanced profile across the decision criteria")


def test_development_reason_exposes_age_upside_structurally() -> None:
    row = recommendation_row(
        age=20.0,
    )

    items = build_reason_items(
        row,
        mode="development",
        target_heatmap_profile={},
    )

    assert items[0].key == "development_age_upside"
    assert items[0].group == "age"
    assert items[0].text == "elite age upside"


def test_short_term_reason_exposes_reliability_structurally() -> None:
    row = recommendation_row(
        data_reliability_score=80.0,
    )

    items = build_reason_items(
        row,
        mode="short_term",
        target_heatmap_profile={},
    )

    assert items[0].key == "data_reliability"
    assert items[0].group == "reliability"
    assert items[0].text == "reliable tournament sample"
