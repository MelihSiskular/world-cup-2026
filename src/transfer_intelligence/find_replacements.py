# -*- coding: utf-8 -*-
"""
Football Scouting Decision Engine v4

Scenario-specific player replacement recommendations combining:

- statistical similarity
- role fit
- average-position spatial similarity
- tournament heatmap occupation similarity
- player quality
- data reliability
- market-value advantage
- age suitability
- automatic recommendation labels
- automatic, data-driven explanation text

Run
---
python -m src.transfer_intelligence.find_replacements \
  --player "Michael Olise"
"""

from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


DEFAULT_FEATURES = Path(
    "data/processed/transfer_intelligence/"
    "transfer_feature_table.csv"
)

DEFAULT_SIMILARITY = Path(
    "data/processed/player_similarity/"
    "player_similarity_breakdown_long.csv"
)

DEFAULT_HEATMAP_SIMILARITY = Path(
    "data/processed/player_heatmaps/"
    "heatmap_similarity_long.csv"
)

DEFAULT_HEATMAP_PROFILES = Path(
    "data/processed/player_heatmaps/"
    "player_heatmap_profiles.csv"
)

DEFAULT_OUTPUT_DIR = Path(
    "data/processed/transfer_intelligence/"
    "replacement_results"
)


# Heatmap receives a meaningful but controlled weight.
# Each mode still reflects a different recruitment scenario.
MODE_CONFIG = {
    "immediate": {
        "minimum_similarity": 30.0,
        "minimum_role_fit": 35.0,
        "minimum_quality": 55.0,
        "minimum_reliability": 55.0,
        "minimum_age": None,
        "maximum_age": 31.0,
        "same_role_bonus": 6.0,
        "same_archetype_bonus": 2.0,
        "weights": {
            "statistical_similarity_pct": 0.20,
            "role_fit_pct": 0.23,
            "spatial_similarity_pct": 0.12,
            "effective_heatmap_score_pct": 0.12,
            "player_quality_score": 0.15,
            "data_reliability_score": 0.10,
            "market_value_advantage_pct": 0.04,
            "age_suitability_pct": 0.04,
        },
    },
    "development": {
        "minimum_similarity": 25.0,
        "minimum_role_fit": 5.0,
        "minimum_quality": 30.0,
        "minimum_reliability": 35.0,
        "minimum_age": None,
        "maximum_age": 23.0,
        "same_role_bonus": 4.0,
        "same_archetype_bonus": 4.0,
        "weights": {
            "statistical_similarity_pct": 0.19,
            "role_fit_pct": 0.11,
            "spatial_similarity_pct": 0.08,
            "effective_heatmap_score_pct": 0.10,
            "player_quality_score": 0.09,
            "data_reliability_score": 0.05,
            "market_value_advantage_pct": 0.14,
            "age_suitability_pct": 0.24,
        },
    },
    "value": {
        "minimum_similarity": 25.0,
        "minimum_role_fit": 25.0,
        "minimum_quality": 35.0,
        "minimum_reliability": 35.0,
        "minimum_age": None,
        "maximum_age": None,
        "same_role_bonus": 7.0,
        "same_archetype_bonus": 2.0,
        "weights": {
            "statistical_similarity_pct": 0.16,
            "role_fit_pct": 0.18,
            "spatial_similarity_pct": 0.08,
            "effective_heatmap_score_pct": 0.10,
            "player_quality_score": 0.09,
            "data_reliability_score": 0.08,
            "market_value_advantage_pct": 0.26,
            "age_suitability_pct": 0.05,
        },
    },
    "short_term": {
        "minimum_similarity": 20.0,
        "minimum_role_fit": 30.0,
        "minimum_quality": 45.0,
        "minimum_reliability": 50.0,
        "minimum_age": 29.0,
        "maximum_age": None,
        "same_role_bonus": 8.0,
        "same_archetype_bonus": 3.0,
        "weights": {
            "statistical_similarity_pct": 0.16,
            "role_fit_pct": 0.22,
            "spatial_similarity_pct": 0.08,
            "effective_heatmap_score_pct": 0.10,
            "player_quality_score": 0.14,
            "data_reliability_score": 0.19,
            "market_value_advantage_pct": 0.11,
            "age_suitability_pct": 0.00,
        },
    },
}


HEATMAP_METRIC_COLUMNS = [
    "heatmap_cosine_similarity_pct",
    "occupation_overlap_pct",
    "lateral_profile_similarity_pct",
    "vertical_profile_similarity_pct",
    "peak_zone_similarity_pct",
    "peak_zone_distance",
    "entropy_similarity_pct",
    "heatmap_similarity_score_pct",
    "target_matches_with_heatmap",
    "candidate_matches_with_heatmap",
    "target_heatmap_points",
    "candidate_heatmap_points",
]


def slugify(text: str) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        str(text),
    )

    ascii_text = (
        normalized
        .encode("ascii", "ignore")
        .decode("ascii")
    )

    return (
        re.sub(
            r"[^a-zA-Z0-9]+",
            "_",
            ascii_text,
        )
        .strip("_")
        .lower()
    )


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    try:
        if value is None or pd.isna(value):
            return default

        return float(value)

    except (TypeError, ValueError):
        return default


def normalize_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""

    return str(value).strip().casefold()


def resolve_player(
    players: pd.DataFrame,
    query: str,
) -> pd.Series:
    exact = players[
        players["player_name"]
        .astype(str)
        .str.casefold()
        .eq(query.casefold())
    ]

    if len(exact) == 1:
        return exact.iloc[0]

    partial = players[
        players["player_name"]
        .astype(str)
        .str.contains(
            query,
            case=False,
            regex=False,
            na=False,
        )
    ]

    if len(partial) == 1:
        return partial.iloc[0]

    if partial.empty:
        raise ValueError(
            f"Player not found: {query}"
        )

    raise ValueError(
        "Multiple players matched: "
        + ", ".join(
            partial["player_name"]
            .drop_duplicates()
            .head(20)
            .tolist()
        )
    )


def load_similarity(
    path: Path,
) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Similarity file not found: {path}"
        )

    dataframe = pd.read_csv(
        path,
        low_memory=False,
    )

    required = {
        "source_player_id",
        "target_player_id",
        "overall_similarity_pct",
    }

    missing = required.difference(
        dataframe.columns
    )

    if missing:
        raise ValueError(
            "Missing similarity columns: "
            + ", ".join(sorted(missing))
        )

    result = dataframe[
        [
            "source_player_id",
            "target_player_id",
            "overall_similarity_pct",
        ]
    ].copy()

    for column in result.columns:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    return result.dropna()


def attach_similarity(
    candidates: pd.DataFrame,
    target: pd.Series,
    similarity: pd.DataFrame,
) -> pd.DataFrame:
    direct = similarity[
        similarity["source_player_id"].eq(
            target["player_id"]
        )
    ][
        [
            "target_player_id",
            "overall_similarity_pct",
        ]
    ].rename(
        columns={
            "target_player_id": "player_id",
            "overall_similarity_pct": (
                "statistical_similarity_pct"
            ),
        }
    )

    reverse = similarity[
        similarity["target_player_id"].eq(
            target["player_id"]
        )
    ][
        [
            "source_player_id",
            "overall_similarity_pct",
        ]
    ].rename(
        columns={
            "source_player_id": "player_id",
            "overall_similarity_pct": (
                "statistical_similarity_pct"
            ),
        }
    )

    pairwise = (
        pd.concat(
            [direct, reverse],
            ignore_index=True,
        )
        .sort_values(
            "statistical_similarity_pct",
            ascending=False,
        )
        .drop_duplicates(
            "player_id",
            keep="first",
        )
    )

    return candidates.merge(
        pairwise,
        on="player_id",
        how="left",
    )


def load_heatmap_similarity(
    path: Path,
) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Heatmap similarity file not found: {path}"
        )

    dataframe = pd.read_csv(
        path,
        low_memory=False,
    )

    required = {
        "target_player_id",
        "candidate_player_id",
        "heatmap_similarity_score_pct",
    }

    missing = required.difference(
        dataframe.columns
    )

    if missing:
        raise ValueError(
            "Missing heatmap similarity columns: "
            + ", ".join(sorted(missing))
        )

    available_columns = [
        column
        for column in (
            [
                "target_player_id",
                "candidate_player_id",
            ]
            + HEATMAP_METRIC_COLUMNS
        )
        if column in dataframe.columns
    ]

    result = dataframe[
        available_columns
    ].copy()

    for column in result.columns:
        if column not in {
            "target_player_name",
            "candidate_player_name",
            "position_group",
        }:
            result[column] = pd.to_numeric(
                result[column],
                errors="coerce",
            )

    return result.dropna(
        subset=[
            "target_player_id",
            "candidate_player_id",
            "heatmap_similarity_score_pct",
        ]
    )

def attach_heatmap_similarity(
    candidates: pd.DataFrame,
    target: pd.Series,
    heatmap_similarity: pd.DataFrame,
    neutral_score: float,
) -> pd.DataFrame:
    """
    Attach genuine target-to-candidate heatmap metrics.

    heatmap_similarity_score_pct:
        Real measured heatmap similarity. Remains NaN when unavailable.

    effective_heatmap_score_pct:
        Score used by the decision engine. Missing values receive the
        configured neutral score.
    """
    target_id = int(
        target["player_id"]
    )

    direct = heatmap_similarity[
        heatmap_similarity[
            "target_player_id"
        ].eq(target_id)
    ].copy()

    if not direct.empty:
        direct = direct.rename(
            columns={
                "candidate_player_id": "player_id",
            }
        )

        direct = direct.drop(
            columns=["target_player_id"],
            errors="ignore",
        )

    reverse = heatmap_similarity[
        heatmap_similarity[
            "candidate_player_id"
        ].eq(target_id)
    ].copy()

    if not reverse.empty:
        reverse = reverse.rename(
            columns={
                "target_player_id": "player_id",
                "candidate_matches_with_heatmap": (
                    "target_matches_with_heatmap"
                ),
                "target_matches_with_heatmap": (
                    "candidate_matches_with_heatmap"
                ),
                "candidate_heatmap_points": (
                    "target_heatmap_points"
                ),
                "target_heatmap_points": (
                    "candidate_heatmap_points"
                ),
            }
        )

        reverse = reverse.drop(
            columns=["candidate_player_id"],
            errors="ignore",
        )

    pairwise = pd.concat(
        [direct, reverse],
        ignore_index=True,
    )

    if not pairwise.empty:
        pairwise = (
            pairwise.sort_values(
                "heatmap_similarity_score_pct",
                ascending=False,
            )
            .drop_duplicates(
                "player_id",
                keep="first",
            )
        )

    result = candidates.merge(
        pairwise,
        on="player_id",
        how="left",
    )

    real_metric_columns = [
        "heatmap_cosine_similarity_pct",
        "occupation_overlap_pct",
        "lateral_profile_similarity_pct",
        "vertical_profile_similarity_pct",
        "peak_zone_similarity_pct",
        "entropy_similarity_pct",
        "heatmap_similarity_score_pct",
    ]

    for column in real_metric_columns:
        if column not in result.columns:
            result[column] = np.nan

        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    result["has_heatmap_similarity"] = (
        result[
            "heatmap_similarity_score_pct"
        ].notna()
    )

    result["effective_heatmap_score_pct"] = (
        result[
            "heatmap_similarity_score_pct"
        ].fillna(neutral_score)
    )

    if "peak_zone_distance" not in result.columns:
        result["peak_zone_distance"] = np.nan

    result["peak_zone_distance"] = pd.to_numeric(
        result["peak_zone_distance"],
        errors="coerce",
    )

    for column in [
        "target_matches_with_heatmap",
        "candidate_matches_with_heatmap",
        "target_heatmap_points",
        "candidate_heatmap_points",
    ]:
        if column not in result.columns:
            result[column] = np.nan

        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    return result

def load_heatmap_profiles(
    path: Path,
) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    dataframe = pd.read_csv(
        path,
        low_memory=False,
    )

    if "player_id" not in dataframe.columns:
        return pd.DataFrame()

    useful_columns = [
        "player_id",
        "left_wide_share",
        "left_half_space_share",
        "central_share",
        "right_half_space_share",
        "right_wide_share",
        "build_up_share",
        "middle_third_share",
        "advanced_middle_share",
        "final_third_share",
        "heatmap_entropy",
        "weighted_mean_x",
        "weighted_mean_y",
        "peak_cell_x",
        "peak_cell_y",
    ]

    available = [
        column
        for column in useful_columns
        if column in dataframe.columns
    ]

    result = dataframe[
        available
    ].copy()

    result["player_id"] = pd.to_numeric(
        result["player_id"],
        errors="coerce",
    )

    return result.dropna(
        subset=["player_id"]
    ).drop_duplicates(
        "player_id"
    )


def attach_heatmap_profiles(
    candidates: pd.DataFrame,
    target: pd.Series,
    heatmap_profiles: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """
    Add candidate heatmap zone shares and return the target heatmap profile.
    """
    if heatmap_profiles.empty:
        return candidates, {}

    target_row = heatmap_profiles[
        heatmap_profiles["player_id"].eq(
            target["player_id"]
        )
    ]

    target_profile = (
        target_row.iloc[0].to_dict()
        if not target_row.empty
        else {}
    )

    candidate_profiles = heatmap_profiles.rename(
        columns={
            column: f"heatmap_{column}"
            for column in heatmap_profiles.columns
            if column != "player_id"
        }
    )

    result = candidates.merge(
        candidate_profiles,
        on="player_id",
        how="left",
    )

    return result, target_profile


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
            series.fillna("__missing__")
            .astype(str)
            .eq(str(target_value)),
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

    return (
        score
        * (
            0.80
            + confidence.div(100).mul(0.20)
        )
    ).clip(0, 100).round(2)


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
        if column in candidates.columns
        and pd.notna(target.get(column))
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

    matrix = matrix.fillna(
        medians
    )

    target_vector = target_vector.fillna(
        medians
    )

    means = matrix.mean()

    standard_deviations = (
        matrix.std(ddof=0)
        .replace(0, 1)
    )

    normalized_matrix = (
        matrix - means
    ) / standard_deviations

    normalized_target = (
        target_vector - means
    ) / standard_deviations

    distances = np.linalg.norm(
        normalized_matrix.to_numpy(
            dtype=float
        )
        - normalized_target.to_numpy(
            dtype=float
        ),
        axis=1,
    )

    return pd.Series(
        100 / (1 + distances / 2.5),
        index=candidates.index,
    ).clip(0, 100).round(2)


def calculate_market_value_advantage(
    candidates: pd.DataFrame,
    target: pd.Series,
) -> pd.Series:
    candidate_value = pd.to_numeric(
        candidates["market_value"],
        errors="coerce",
    )

    target_value = pd.to_numeric(
        pd.Series(
            [target.get("market_value")]
        ),
        errors="coerce",
    ).iloc[0]

    if pd.isna(target_value) or target_value <= 0:
        percentile = candidate_value.rank(
            pct=True,
            method="average",
        )

        return (
            1 - percentile
        ).mul(100).fillna(50).round(2)

    ratio = candidate_value / target_value

    return (
        100 - ratio.mul(50)
    ).clip(0, 100).fillna(50).round(2)


def calculate_age_suitability(
    candidates: pd.DataFrame,
    target: pd.Series,
) -> pd.Series:
    ages = pd.to_numeric(
        candidates["age"],
        errors="coerce",
    )

    target_age = pd.to_numeric(
        pd.Series(
            [target.get("age")]
        ),
        errors="coerce",
    ).iloc[0]

    base = (
        (34 - ages) / 16
    ).clip(0, 1).mul(100)

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

    return (
        base + adjustment
    ).clip(0, 100).fillna(50).round(2)


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
        players["position"].eq(
            target["position"]
        )
        & ~players["player_id"].eq(
            target["player_id"]
        )
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

    candidates = candidates[
        candidates[
            "statistical_similarity_pct"
        ].notna()
    ].copy()

    candidates = attach_heatmap_similarity(
        candidates,
        target,
        heatmap_similarity,
        neutral_score=neutral_heatmap_score,
    )

    candidates, target_heatmap_profile = (
        attach_heatmap_profiles(
            candidates,
            target,
            heatmap_profiles,
        )
    )

    candidates["role_fit_pct"] = (
        calculate_role_fit(
            candidates,
            target,
        )
    )

    candidates[
        "spatial_similarity_pct"
    ] = calculate_spatial_similarity(
        candidates,
        target,
    )

    candidates[
        "market_value_advantage_pct"
    ] = calculate_market_value_advantage(
        candidates,
        target,
    )

    candidates[
        "age_suitability_pct"
    ] = calculate_age_suitability(
        candidates,
        target,
    )

    candidates["same_final_role"] = (
        candidates["final_role"].eq(
            target["final_role"]
        )
    )

    candidates["same_archetype"] = (
        candidates["archetype"].eq(
            target["archetype"]
        )
    )

    return candidates, target_heatmap_profile


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
        similarity.ge(
            config["minimum_similarity"]
        )
        & role_fit.ge(
            config["minimum_role_fit"]
        )
        & quality.ge(
            config["minimum_quality"]
        )
        & reliability.ge(
            config["minimum_reliability"]
        )
    )

    if config["minimum_age"] is not None:
        mask &= ages.ge(
            config["minimum_age"]
        )

    if config["maximum_age"] is not None:
        mask &= ages.le(
            config["maximum_age"]
        )

    return result[mask].copy()


def calculate_mode_score(
    candidates: pd.DataFrame,
    mode: str,
) -> pd.Series:
    config = MODE_CONFIG[mode]

    score = pd.Series(
        0.0,
        index=candidates.index,
    )

    for column, weight in config[
        "weights"
    ].items():
        score += (
            pd.to_numeric(
                candidates[column],
                errors="coerce",
            )
            .fillna(0)
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

    return score.clip(0, 100).round(2)

def format_optional_score(
    value: Any,
) -> str:
    if value is None or pd.isna(value):
        return "N/A"

    return f"{float(value):.2f}"


def classify_candidate(
        row: pd.Series,
        mode: str,
) -> str:
    same_role = bool(
        row["same_final_role"]
    )

    same_archetype = bool(
        row["same_archetype"]
    )

    has_heatmap = bool(
        row.get(
            "has_heatmap_similarity",
            False,
        )
    )

    similarity = safe_float(
        row["statistical_similarity_pct"]
    )

    role_fit = safe_float(
        row["role_fit_pct"]
    )

    heatmap_fit = safe_float(
        row["effective_heatmap_score_pct"]
    )

    quality = safe_float(
        row["player_quality_score"]
    )

    value_advantage = safe_float(
        row["market_value_advantage_pct"]
    )

    # ----------------------------------------------------------
    # Immediate replacement
    # ----------------------------------------------------------
    if mode == "immediate":
        if (
                same_role
                and role_fit >= 85
                and quality >= 65
                and (
                not has_heatmap
                or heatmap_fit >= 75
        )
        ):
            return "Direct tactical replacement"

        if (
                has_heatmap
                and similarity >= 75
                and heatmap_fit >= 80
        ):
            return (
                "High-continuity "
                "playing-profile alternative"
            )

        if role_fit >= 65:
            return "Strong tactical alternative"

        return "Adaptable first-team option"

    # ----------------------------------------------------------
    # Development prospect
    # ----------------------------------------------------------
    if mode == "development":
        if (
                same_role
                and role_fit >= 75
        ):
            return "Long-term direct replacement"

        if (
                similarity >= 60
                and same_archetype
        ):
            return (
                "High-upside statistical prospect"
            )

        if (
                has_heatmap
                and heatmap_fit >= 85
        ):
            return (
                "Developmental "
                "occupation-profile match"
            )

        return "Long-term tactical project"

    # ----------------------------------------------------------
    # Value alternative
    # ----------------------------------------------------------
    if mode == "value":
        if (
                same_role
                and value_advantage >= 65
        ):
            return (
                "Best-value direct replacement"
            )

        if (
                has_heatmap
                and heatmap_fit >= 85
                and value_advantage >= 60
        ):
            return (
                "High-value "
                "occupation-profile match"
            )

        if value_advantage >= 80:
            return "Low-cost adaptable option"

        return "Balanced value alternative"

    # ----------------------------------------------------------
    # Short-term experienced option
    # ----------------------------------------------------------
    if mode == "short_term":
        if (
                same_role
                and role_fit >= 75
        ):
            return (
                "Experienced direct replacement"
            )

        if (
                same_archetype
                and similarity >= 55
        ):
            return "Experienced profile match"

        if (
                has_heatmap
                and heatmap_fit >= 85
        ):
            return (
                "Experienced "
                "occupation-profile match"
            )

        return (
            "Short-term tactical alternative"
        )

    raise ValueError(
        f"Unsupported recommendation mode: {mode}"
    )


def dominant_heatmap_zone(
    profile: dict[str, float],
    prefix: str = "",
) -> tuple[str, str]:
    lateral = {
        "left wide lane": safe_float(
            profile.get(f"{prefix}left_wide_share")
        ),
        "left half-space": safe_float(
            profile.get(
                f"{prefix}left_half_space_share"
            )
        ),
        "central lane": safe_float(
            profile.get(f"{prefix}central_share")
        ),
        "right half-space": safe_float(
            profile.get(
                f"{prefix}right_half_space_share"
            )
        ),
        "right wide lane": safe_float(
            profile.get(f"{prefix}right_wide_share")
        ),
    }

    vertical = {
        "build-up third": safe_float(
            profile.get(f"{prefix}build_up_share")
        ),
        "middle third": safe_float(
            profile.get(
                f"{prefix}middle_third_share"
            )
        ),
        "advanced middle third": safe_float(
            profile.get(
                f"{prefix}advanced_middle_share"
            )
        ),
        "final third": safe_float(
            profile.get(f"{prefix}final_third_share")
        ),
    }

    lateral_zone = max(
        lateral,
        key=lateral.get,
    )

    vertical_zone = max(
        vertical,
        key=vertical.get,
    )

    return lateral_zone, vertical_zone


def heatmap_difference_reason(
    row: pd.Series,
    target_heatmap_profile: dict[str, float],
) -> str | None:
    if (
        not target_heatmap_profile
        or not bool(
            row.get(
                "has_heatmap_similarity",
                False,
            )
        )
    ):
        return None

    candidate_profile = {
        column.replace(
            "heatmap_",
            "",
            1,
        ): value
        for column, value in row.items()
        if str(column).startswith(
            "heatmap_"
        )
    }

    target_lateral, target_vertical = (
        dominant_heatmap_zone(
            target_heatmap_profile
        )
    )

    candidate_lateral, candidate_vertical = (
        dominant_heatmap_zone(
            candidate_profile
        )
    )

    if (
        target_lateral == candidate_lateral
        and target_vertical
        == candidate_vertical
    ):
        return (
            f"replicates the target's {target_lateral} "
            f"and {target_vertical} occupation"
        )

    if target_lateral == candidate_lateral:
        return (
            f"uses the same {target_lateral}, "
            f"but operates more in the {candidate_vertical}"
        )

    if target_vertical == candidate_vertical:
        return (
            f"matches the target's {target_vertical} depth "
            f"with more {candidate_lateral} occupation"
        )

    return (
        f"operates mainly in the {candidate_lateral} "
        f"and {candidate_vertical}"
    )


def build_reason(
    row: pd.Series,
    mode: str,
    target_heatmap_profile: dict[str, float],
) -> str:
    reasons: list[
        tuple[int, str, str]
    ] = []

    if bool(row["same_final_role"]):
        reasons.append(
            (
                100,
                "role",
                "same final role",
            )
        )

    if bool(row["same_archetype"]):
        reasons.append(
            (
                92,
                "archetype",
                "same statistical archetype",
            )
        )

    statistical = safe_float(
        row["statistical_similarity_pct"]
    )

    role_fit = safe_float(
        row["role_fit_pct"]
    )

    spatial = safe_float(
        row["spatial_similarity_pct"]
    )

    heatmap = safe_float(
        row.get(
            "heatmap_similarity_score_pct"
        )
    )

    overlap = safe_float(
        row["occupation_overlap_pct"]
    )

    lateral = safe_float(
        row["lateral_profile_similarity_pct"]
    )

    vertical = safe_float(
        row["vertical_profile_similarity_pct"]
    )

    value = safe_float(
        row["market_value_advantage_pct"]
    )

    if statistical >= 75:
        reasons.append(
            (
                88,
                "statistics",
                (
                    "very strong statistical similarity "
                    f"({statistical:.1f}%)"
                ),
            )
        )
    elif statistical >= 55:
        reasons.append(
            (
                74,
                "statistics",
                (
                    "good statistical similarity "
                    f"({statistical:.1f}%)"
                ),
            )
        )

    if role_fit >= 85:
        reasons.append(
            (
                96,
                "role",
                (
                    "elite tactical fit "
                    f"({role_fit:.1f}%)"
                ),
            )
        )
    elif role_fit >= 65:
        reasons.append(
            (
                82,
                "role",
                (
                    "strong tactical fit "
                    f"({role_fit:.1f}%)"
                ),
            )
        )

    if spatial >= 70:
        reasons.append(
            (
                76,
                "average_position",
                (
                    "similar average-position profile "
                    f"({spatial:.1f}%)"
                ),
            )
        )

    if bool(
        row.get(
            "has_heatmap_similarity",
            False,
        )
    ):
        if heatmap >= 90:
            reasons.append(
                (
                    94,
                    "heatmap",
                    (
                        "elite heatmap occupation similarity "
                        f"({heatmap:.1f}%)"
                    ),
                )
            )
        elif heatmap >= 82:
            reasons.append(
                (
                    84,
                    "heatmap",
                    (
                        "strong heatmap occupation similarity "
                        f"({heatmap:.1f}%)"
                    ),
                )
            )
        elif heatmap >= 72:
            reasons.append(
                (
                    70,
                    "heatmap",
                    (
                        "useful heatmap occupation similarity "
                        f"({heatmap:.1f}%)"
                    ),
                )
            )

        if overlap >= 80:
            reasons.append(
                (
                    86,
                    "heatmap_overlap",
                    (
                        "high shared-zone occupation "
                        f"({overlap:.1f}%)"
                    ),
                )
            )

        if lateral >= 90 and vertical >= 90:
            reasons.append(
                (
                    89,
                    "heatmap_structure",
                    "closely matches both lateral and vertical usage",
                )
            )

        zone_reason = heatmap_difference_reason(
            row,
            target_heatmap_profile,
        )

        if zone_reason:
            reasons.append(
                (
                    78,
                    "heatmap_zone",
                    zone_reason,
                )
            )

    if value >= 80:
        reasons.append(
            (
                91 if mode == "value" else 72,
                "market",
                "major price advantage",
            )
        )
    elif value >= 60:
        reasons.append(
            (
                76 if mode == "value" else 64,
                "market",
                "useful price advantage",
            )
        )

    if mode == "development":
        age = safe_float(
            row["age"],
            default=99,
        )

        if age <= 20:
            reasons.append(
                (
                    95,
                    "age",
                    "elite age upside",
                )
            )
        elif age <= 23:
            reasons.append(
                (
                    84,
                    "age",
                    "strong development age",
                )
            )

    if mode == "short_term":
        reliability = safe_float(
            row["data_reliability_score"]
        )

        if reliability >= 65:
            reasons.append(
                (
                    88,
                    "reliability",
                    "reliable tournament sample",
                )
            )

    reasons.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    selected: list[str] = []
    used_groups: set[str] = set()

    for _, group, text in reasons:
        if group in used_groups:
            continue

        selected.append(text)
        used_groups.add(group)

        if len(selected) >= 4:
            break

    if not selected:
        selected.append(
            "balanced profile across the decision criteria"
        )

    return "; ".join(selected)


def recommendation_strength(
    score: float,
) -> str:
    if score >= 80:
        return "Elite"

    if score >= 72:
        return "Strong"

    if score >= 64:
        return "Good"

    if score >= 56:
        return "Moderate"

    return "Low"


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

    result[f"{mode}_score"] = (
        calculate_mode_score(
            result,
            mode,
        )
    )

    result[
        "recommendation_type"
    ] = result.apply(
        lambda row: classify_candidate(
            row,
            mode,
        ),
        axis=1,
    )

    result[
        "recommendation_strength"
    ] = result[
        f"{mode}_score"
    ].map(
        recommendation_strength
    )

    result["why_recommended"] = (
        result.apply(
            lambda row: build_reason(
                row,
                mode,
                target_heatmap_profile,
            ),
            axis=1,
        )
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

def format_market_value(
    value: Any,
) -> str:
    if pd.isna(value):
        return "-"

    value = float(value)
    euro = "\u20ac"

    if value >= 1_000_000:
        return (
            f"{euro}"
            f"{value / 1_000_000:.1f}M"
        )

    if value >= 1_000:
        return (
            f"{euro}"
            f"{value / 1_000:.0f}K"
        )

    return f"{euro}{value:.0f}"
def print_report(
    target: pd.Series,
    results: dict[str, pd.DataFrame],
    top_n: int,
) -> None:
    print("=" * 120)
    print(
        "FOOTBALL SCOUTING DECISION ENGINE V4"
    )
    print("=" * 120)
    print()
    print(
        f"Target Player:  "
        f"{target['player_name']}"
    )
    print(
        f"Position:       "
        f"{target['position']}"
    )
    print(
        f"Archetype:      "
        f"{target['archetype']}"
    )
    print(
        f"Final Role:     "
        f"{target['final_role']}"
    )
    print(
        f"Age:            "
        f"{target['age']}"
    )
    print(
        f"Market Value:   "
        f"{format_market_value(target['market_value'])}"
    )

    titles = {
        "immediate": (
            "IMMEDIATE REPLACEMENTS"
        ),
        "development": (
            "DEVELOPMENT PROSPECTS"
        ),
        "value": (
            "BEST VALUE OPTIONS"
        ),
        "short_term": (
            "SHORT-TERM EXPERIENCED OPTIONS"
        ),
    }

    for mode, title in titles.items():
        print()
        print(title)
        print("-" * 120)

        result = results[mode]

        if result.empty:
            print(
                "No eligible candidates."
            )
            continue

        columns = [
            f"{mode}_rank",
            "player_name",
            "national_team_name",
            "age",
            "market_value",
            "final_role",
            "statistical_similarity_pct",
            "role_fit_pct",
            "spatial_similarity_pct",
            "heatmap_similarity_score_pct",
            "occupation_overlap_pct",
            f"{mode}_score",
            "recommendation_type",
            "why_recommended",
        ]

        display = result.head(
            top_n
        )[columns].rename(
            columns={
                "national_team_name": "team",
                "statistical_similarity_pct": (
                    "stat_sim"
                ),
                "spatial_similarity_pct": (
                    "spatial_sim"
                ),
                "heatmap_similarity_score_pct": "heatmap_sim",

                "occupation_overlap_pct": (
                    "heatmap_overlap"
                ),
                f"{mode}_score": (
                    "decision_score"
                ),
            }
        )

        formatters = {
            "age": lambda value: f"{value:.1f}",
            "market_value": format_market_value,
            "stat_sim": format_optional_score,
            "role_fit_pct": format_optional_score,
            "spatial_sim": format_optional_score,
            "heatmap_sim": format_optional_score,
            "heatmap_overlap": format_optional_score,
            "decision_score": format_optional_score,
        }

        print(
            display.to_string(
                index=False,
                formatters=formatters,
            )
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--player",
        required=True,
    )

    parser.add_argument(
        "--features",
        type=Path,
        default=DEFAULT_FEATURES,
    )

    parser.add_argument(
        "--similarity",
        type=Path,
        default=DEFAULT_SIMILARITY,
    )

    parser.add_argument(
        "--heatmap-similarity",
        type=Path,
        default=DEFAULT_HEATMAP_SIMILARITY,
    )

    parser.add_argument(
        "--heatmap-profiles",
        type=Path,
        default=DEFAULT_HEATMAP_PROFILES,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )

    parser.add_argument(
        "--minimum-minutes",
        type=float,
        default=150,
    )

    parser.add_argument(
        "--minimum-role-confidence",
        type=float,
        default=50,
    )

    parser.add_argument(
        "--maximum-market-value",
        type=float,
        default=None,
    )

    parser.add_argument(
        "--neutral-heatmap-score",
        type=float,
        default=70.0,
        help=(
            "Neutral score assigned when a candidate has no "
            "available heatmap comparison."
        ),
    )

    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    players = pd.read_csv(
        args.features,
        low_memory=False,
    )

    players["player_id"] = pd.to_numeric(
        players["player_id"],
        errors="coerce",
    )

    similarity = load_similarity(
        args.similarity
    )

    heatmap_similarity = (
        load_heatmap_similarity(
            args.heatmap_similarity
        )
    )

    heatmap_profiles = (
        load_heatmap_profiles(
            args.heatmap_profiles
        )
    )

    target = resolve_player(
        players,
        args.player,
    )

    (
        base_candidates,
        target_heatmap_profile,
    ) = prepare_candidate_base(
        players=players,
        similarity=similarity,
        heatmap_similarity=heatmap_similarity,
        heatmap_profiles=heatmap_profiles,
        target=target,
        minimum_minutes=args.minimum_minutes,
        minimum_role_confidence=(
            args.minimum_role_confidence
        ),
        maximum_market_value=(
            args.maximum_market_value
        ),
        neutral_heatmap_score=(
            args.neutral_heatmap_score
        ),
    )

    results = {
        mode: generate_mode_results(
            base_candidates,
            mode,
            target_heatmap_profile,
        )
        for mode in MODE_CONFIG
    }

    args.output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    player_slug = slugify(
        target["player_name"]
    )

    for mode, result in results.items():
        if result.empty:
            continue

        output_path = (
            args.output_dir
            / (
                f"{player_slug}_{mode}"
                "_recommendations.csv"
            )
        )

        result.to_csv(
            output_path,
            index=False,
            encoding="utf-8-sig",
        )

    print_report(
        target,
        results,
        args.top_n,
    )

    print()
    print(
        f"Output directory: "
        f"{args.output_dir}"
    )


if __name__ == "__main__":
    main()
