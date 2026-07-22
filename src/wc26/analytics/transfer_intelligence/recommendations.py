"""Recommendation filtering and result generation."""

from __future__ import annotations

import pandas as pd

from wc26.analytics.transfer_intelligence.config import (
    MODE_CONFIG,
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


__all__ = [
    "filter_for_mode",
]
