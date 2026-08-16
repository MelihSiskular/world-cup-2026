"""Transfer recommendation scoring rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, cast

import numpy as np
import pandas as pd

from wc26.analytics.transfer_intelligence.config import (
    MODE_CONFIG,
)

type ScoreEvidenceStatus = Literal[
    "available",
    "fallback",
    "missing",
]


@dataclass(frozen=True, slots=True)
class ModeSignalContribution:
    """One weighted signal used by a recruitment-mode score."""

    key: str
    source_score: float | None
    input_score: float
    weight: float
    weighted_contribution: float
    evidence_status: ScoreEvidenceStatus


@dataclass(frozen=True, slots=True)
class ModeBonusContribution:
    """One explicit mode-specific score bonus."""

    key: str
    configured_points: float
    applied: bool
    applied_points: float


@dataclass(frozen=True, slots=True)
class ModeScoreBreakdown:
    """Explain how one candidate's mode score was assembled."""

    mode: str
    signals: tuple[ModeSignalContribution, ...]
    bonuses: tuple[ModeBonusContribution, ...]
    weighted_signal_total: float
    bonus_total: float
    pre_clip_score: float
    final_score: float
    was_clipped: bool


def same_value_score(
    series: pd.Series,
    target_value: Any,
    match_score: float,
) -> pd.Series:
    if pd.isna(target_value):
        return pd.Series(
            0.0,
            index=series.index,
        )

    return pd.Series(
        np.where(
            series.fillna("__missing__").astype(str).eq(str(target_value)),
            match_score,
            0.0,
        ),
        index=series.index,
    )


def calculate_role_fit(
    candidates: pd.DataFrame,
    target: pd.Series,
) -> pd.Series:
    score = pd.Series(
        0.0,
        index=candidates.index,
    )

    score += same_value_score(
        candidates["final_role"],
        target.get("final_role"),
        45,
    )

    score += same_value_score(
        candidates["archetype"],
        target.get("archetype"),
        25,
    )

    score += same_value_score(
        candidates["spatial_role"],
        target.get("spatial_role"),
        12,
    )

    score += same_value_score(
        candidates["lateral_profile"],
        target.get("lateral_profile"),
        7,
    )

    score += same_value_score(
        candidates["vertical_profile"],
        target.get("vertical_profile"),
        6,
    )

    score += same_value_score(
        candidates["mobility_profile"],
        target.get("mobility_profile"),
        5,
    )

    confidence = pd.to_numeric(
        candidates["role_confidence_score"],
        errors="coerce",
    ).fillna(0)

    return (score * (0.80 + confidence.div(100).mul(0.20))).clip(0, 100).round(2)


def calculate_spatial_similarity(
    candidates: pd.DataFrame,
    target: pd.Series,
) -> pd.Series:
    columns = [
        "weighted_mean_x",
        "weighted_mean_y",
        "spatial_spread",
        "attacking_third_match_share",
        "middle_third_match_share",
        "defensive_third_match_share",
        "wide_lane_match_share",
        "half_space_match_share",
        "central_lane_match_share",
    ]

    usable = [
        column
        for column in columns
        if column in candidates.columns and pd.notna(target.get(column))
    ]

    if len(usable) < 3:
        return pd.Series(
            50.0,
            index=candidates.index,
        )

    matrix = candidates[usable].apply(
        pd.to_numeric,
        errors="coerce",
    )

    target_vector = pd.to_numeric(
        target[usable],
        errors="coerce",
    )

    medians = matrix.median()

    matrix = matrix.fillna(medians)

    target_vector = target_vector.fillna(medians)

    means = matrix.mean()

    standard_deviations = matrix.std(ddof=0).replace(0, 1)

    normalized_matrix = (matrix - means) / standard_deviations

    normalized_target = (target_vector - means) / standard_deviations

    distances = np.linalg.norm(
        normalized_matrix.to_numpy(dtype=float) - normalized_target.to_numpy(dtype=float),
        axis=1,
    )

    return (
        pd.Series(
            100 / (1 + distances / 2.5),
            index=candidates.index,
        )
        .clip(0, 100)
        .round(2)
    )


def calculate_market_value_advantage(
    candidates: pd.DataFrame,
    target: pd.Series,
) -> pd.Series:
    candidate_value = pd.to_numeric(
        candidates["market_value"],
        errors="coerce",
    )

    target_value = pd.to_numeric(
        pd.Series([target.get("market_value")]),
        errors="coerce",
    ).iloc[0]

    if pd.isna(target_value) or target_value <= 0:
        percentile = candidate_value.rank(
            pct=True,
            method="average",
        )

        return (1 - percentile).mul(100).fillna(50).round(2)

    ratio = candidate_value / target_value

    result = (100 - ratio.mul(50)).clip(0, 100).fillna(50).round(2)

    return cast("pd.Series[Any]", result)
    return cast("pd.Series[Any]", result)


def calculate_age_suitability(
    candidates: pd.DataFrame,
    target: pd.Series,
) -> pd.Series:
    ages = pd.to_numeric(
        candidates["age"],
        errors="coerce",
    )

    target_age = pd.to_numeric(
        pd.Series([target.get("age")]),
        errors="coerce",
    ).iloc[0]

    base = ((34 - ages) / 16).clip(0, 1).mul(100)

    if pd.isna(target_age):
        return base.fillna(50).round(2)

    age_difference = ages - target_age

    adjustment = np.where(
        age_difference <= 0,
        np.minimum(
            -age_difference * 3,
            12,
        ),
        -np.minimum(
            age_difference * 6,
            40,
        ),
    )

    result = (base + adjustment).clip(0, 100).fillna(50).round(2)

    return cast("pd.Series[Any]", result)


def _optional_float(
    value: object,
) -> float | None:
    """Return one finite numeric scoring value when available."""

    numeric = pd.to_numeric(
        pd.Series([value], dtype="object"),
        errors="coerce",
    ).iloc[0]

    if pd.isna(numeric):
        return None

    return float(numeric)


def _optional_flag(
    value: object,
) -> bool:
    """Return a safe boolean flag for optional analytical values."""

    if value is None or value is pd.NA or value is pd.NaT:
        return False

    missing = (
        pd.Series(
            [value],
            dtype="object",
        )
        .isna()
        .iloc[0]
    )

    if bool(missing):
        return False

    return bool(value)


def build_mode_score_breakdown(
    row: pd.Series[Any],
    mode: str,
) -> ModeScoreBreakdown:
    """Build a structured explanation for one candidate mode score."""

    config = MODE_CONFIG[mode]

    weights = cast(
        dict[str, float],
        config["weights"],
    )

    signals: list[ModeSignalContribution] = []
    weighted_signal_total_raw = 0.0

    for key, weight in weights.items():
        scoring_value = _optional_float(row.get(key))

        input_score = 0.0 if scoring_value is None else scoring_value

        source_score = scoring_value

        evidence_status: ScoreEvidenceStatus = (
            "available" if scoring_value is not None else "missing"
        )

        if key == "effective_heatmap_score_pct":
            measured_heatmap_score = _optional_float(row.get("heatmap_similarity_score_pct"))

            has_direct_heatmap = _optional_flag(
                row.get(
                    "has_heatmap_similarity",
                    False,
                )
            )

            if has_direct_heatmap and measured_heatmap_score is not None:
                source_score = measured_heatmap_score
                evidence_status = "available"
            elif scoring_value is not None:
                source_score = None
                evidence_status = "fallback"
            else:
                source_score = None
                evidence_status = "missing"

        contribution = input_score * weight

        weighted_signal_total_raw += contribution

        signals.append(
            ModeSignalContribution(
                key=key,
                source_score=source_score,
                input_score=input_score,
                weight=weight,
                weighted_contribution=round(
                    contribution,
                    4,
                ),
                evidence_status=evidence_status,
            )
        )

    same_role_applied = _optional_flag(
        row.get(
            "same_final_role",
            False,
        )
    )

    same_archetype_applied = _optional_flag(
        row.get(
            "same_archetype",
            False,
        )
    )

    bonuses = (
        ModeBonusContribution(
            key="same_final_role",
            configured_points=config["same_role_bonus"],
            applied=same_role_applied,
            applied_points=(config["same_role_bonus"] if same_role_applied else 0.0),
        ),
        ModeBonusContribution(
            key="same_archetype",
            configured_points=config["same_archetype_bonus"],
            applied=same_archetype_applied,
            applied_points=(config["same_archetype_bonus"] if same_archetype_applied else 0.0),
        ),
    )

    bonus_total_raw = sum(bonus.applied_points for bonus in bonuses)

    pre_clip_score_raw = weighted_signal_total_raw + bonus_total_raw

    final_score = float(
        calculate_mode_score(
            pd.DataFrame([row.to_dict()]),
            mode,
        ).iloc[0]
    )

    return ModeScoreBreakdown(
        mode=mode,
        signals=tuple(signals),
        bonuses=bonuses,
        weighted_signal_total=round(
            weighted_signal_total_raw,
            2,
        ),
        bonus_total=round(
            bonus_total_raw,
            2,
        ),
        pre_clip_score=round(
            pre_clip_score_raw,
            2,
        ),
        final_score=final_score,
        was_clipped=(pre_clip_score_raw < 0.0 or pre_clip_score_raw > 100.0),
    )


def calculate_mode_score(
    candidates: pd.DataFrame,
    mode: str,
) -> pd.Series[Any]:
    config = MODE_CONFIG[mode]
    weights = cast(
        dict[str, float],
        config["weights"],
    )

    score = pd.Series(
        0.0,
        index=candidates.index,
        dtype=float,
    )

    for column, weight in weights.items():
        score += (
            pd.to_numeric(
                candidates[column],
                errors="coerce",
            ).fillna(0)
            * weight
        )

    score += np.where(
        candidates["same_final_role"],
        config["same_role_bonus"],
        0.0,
    )

    score += np.where(
        candidates["same_archetype"],
        config["same_archetype_bonus"],
        0.0,
    )

    result = score.clip(0, 100).round(2)

    return cast("pd.Series[Any]", result)


__all__ = [
    "ModeBonusContribution",
    "ModeScoreBreakdown",
    "ModeSignalContribution",
    "build_mode_score_breakdown",
    "calculate_age_suitability",
    "calculate_market_value_advantage",
    "calculate_mode_score",
    "calculate_role_fit",
    "calculate_spatial_similarity",
    "same_value_score",
]
