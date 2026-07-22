"""Configuration for transfer recommendation scenarios."""

from pathlib import Path
from typing import Final

DEFAULT_FEATURES: Final[Path] = Path(
    "data/processed/transfer_intelligence/transfer_feature_table.csv"
)

DEFAULT_SIMILARITY: Final[Path] = Path(
    "data/processed/player_similarity/player_similarity_breakdown_long.csv"
)

DEFAULT_HEATMAP_SIMILARITY: Final[Path] = Path(
    "data/processed/player_heatmaps/heatmap_similarity_long.csv"
)

DEFAULT_HEATMAP_PROFILES: Final[Path] = Path(
    "data/processed/player_heatmaps/player_heatmap_profiles.csv"
)

DEFAULT_OUTPUT_DIR: Final[Path] = Path("data/processed/transfer_intelligence/replacement_results")


# Heatmap receives a meaningful but controlled weight.
# Each mode reflects a different recruitment scenario.
MODE_CONFIG: Final[dict[str, dict[str, object]]] = {
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


HEATMAP_METRIC_COLUMNS: Final[list[str]] = [
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


__all__ = [
    "DEFAULT_FEATURES",
    "DEFAULT_HEATMAP_PROFILES",
    "DEFAULT_HEATMAP_SIMILARITY",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_SIMILARITY",
    "HEATMAP_METRIC_COLUMNS",
    "MODE_CONFIG",
]
