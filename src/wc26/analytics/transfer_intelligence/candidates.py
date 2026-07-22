"""Candidate preparation pipeline for transfer intelligence."""

from __future__ import annotations

import pandas as pd

from wc26.analytics.transfer_intelligence.matching import (
    attach_heatmap_profiles,
    attach_heatmap_similarity,
    attach_similarity,
)
from wc26.analytics.transfer_intelligence.scoring import (
    calculate_age_suitability,
    calculate_market_value_advantage,
    calculate_role_fit,
    calculate_spatial_similarity,
)


def prepare_candidate_base(
    players: pd.DataFrame,
    similarity: pd.DataFrame,
    heatmap_similarity: pd.DataFrame,
    heatmap_profiles: pd.DataFrame,
    target: pd.Series,
    minimum_minutes: float,
    minimum_role_confidence: float,
    maximum_market_value: float | None,
    neutral_heatmap_score: float,
) -> tuple[pd.DataFrame, dict[str, float]]:
    candidates = players[
        players["position"].eq(target["position"]) & ~players["player_id"].eq(target["player_id"])
    ].copy()

    candidates = candidates[
        pd.to_numeric(
            candidates["minutes"],
            errors="coerce",
        ).ge(minimum_minutes)
    ]

    candidates = candidates[
        pd.to_numeric(
            candidates["role_confidence_score"],
            errors="coerce",
        ).ge(minimum_role_confidence)
    ]

    if maximum_market_value is not None:
        candidates = candidates[
            pd.to_numeric(
                candidates["market_value"],
                errors="coerce",
            ).le(maximum_market_value)
        ]

    candidates = attach_similarity(
        candidates,
        target,
        similarity,
    )

    candidates = candidates[candidates["statistical_similarity_pct"].notna()].copy()

    candidates = attach_heatmap_similarity(
        candidates,
        target,
        heatmap_similarity,
        neutral_score=neutral_heatmap_score,
    )

    candidates, target_heatmap_profile = attach_heatmap_profiles(
        candidates,
        target,
        heatmap_profiles,
    )

    candidates["role_fit_pct"] = calculate_role_fit(
        candidates,
        target,
    )

    candidates["spatial_similarity_pct"] = calculate_spatial_similarity(
        candidates,
        target,
    )

    candidates["market_value_advantage_pct"] = calculate_market_value_advantage(
        candidates,
        target,
    )

    candidates["age_suitability_pct"] = calculate_age_suitability(
        candidates,
        target,
    )

    candidates["same_final_role"] = candidates["final_role"].eq(target["final_role"])

    candidates["same_archetype"] = candidates["archetype"].eq(target["archetype"])

    return candidates, target_heatmap_profile


__all__ = [
    "prepare_candidate_base",
]
