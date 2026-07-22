"""Recommendation filtering and result generation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from wc26.analytics.transfer_intelligence.config import (
    MODE_CONFIG,
)
from wc26.analytics.transfer_intelligence.explanations import (
    build_reason,
    classify_candidate,
    recommendation_strength,
)
from wc26.analytics.transfer_intelligence.scoring import (
    calculate_mode_score,
)


def filter_for_mode(
    candidates: pd.DataFrame,
    mode: str,
) -> pd.DataFrame:
    config = MODE_CONFIG[mode]
    result = candidates.copy()

    similarity = pd.to_numeric(
        result["statistical_similarity_pct"],
        errors="coerce",
    )

    role_fit = pd.to_numeric(
        result["role_fit_pct"],
        errors="coerce",
    )

    quality = pd.to_numeric(
        result["player_quality_score"],
        errors="coerce",
    )

    reliability = pd.to_numeric(
        result["data_reliability_score"],
        errors="coerce",
    )

    ages = pd.to_numeric(
        result["age"],
        errors="coerce",
    )

    mask = (
        similarity.ge(config["minimum_similarity"])
        & role_fit.ge(config["minimum_role_fit"])
        & quality.ge(config["minimum_quality"])
        & reliability.ge(config["minimum_reliability"])
    )

    if config["minimum_age"] is not None:
        mask &= ages.ge(config["minimum_age"])

    if config["maximum_age"] is not None:
        mask &= ages.le(config["maximum_age"])

    return result[mask].copy()


def generate_mode_results(
    base_candidates: pd.DataFrame,
    mode: str,
    target_heatmap_profile: dict[str, float],
) -> pd.DataFrame:
    result = filter_for_mode(
        base_candidates,
        mode,
    )

    if result.empty:
        return result

    result[f"{mode}_score"] = calculate_mode_score(
        result,
        mode,
    )

    result["recommendation_type"] = result.apply(
        lambda row: classify_candidate(
            row,
            mode,
        ),
        axis=1,
    )

    result["recommendation_strength"] = result[f"{mode}_score"].map(recommendation_strength)

    result["why_recommended"] = result.apply(
        lambda row: build_reason(
            row,
            mode,
            target_heatmap_profile,
        ),
        axis=1,
    )

    result = result.sort_values(
        [
            f"{mode}_score",
            "role_fit_pct",
            "effective_heatmap_score_pct",
            "statistical_similarity_pct",
            "player_quality_score",
        ],
        ascending=[
            False,
            False,
            False,
            False,
            False,
        ],
    ).reset_index(drop=True)

    result[f"{mode}_rank"] = np.arange(
        1,
        len(result) + 1,
    )

    return result


__all__ = ["filter_for_mode", "generate_mode_results"]
