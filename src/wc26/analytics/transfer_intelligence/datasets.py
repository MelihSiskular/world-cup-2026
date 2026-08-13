"""Dataset loading and validation for transfer intelligence."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from wc26.analytics.transfer_intelligence.config import (
    HEATMAP_METRIC_COLUMNS,
)
from wc26.analytics.transfer_intelligence.errors import (
    DatasetNotFoundError,
    InvalidDatasetError,
)


def load_player_features(
    path: Path,
) -> pd.DataFrame:
    """Load the shared player feature table."""

    if not path.exists():
        raise DatasetNotFoundError(f"Player feature table not found: {path}")

    try:
        return pd.read_csv(
            path,
            low_memory=False,
        )
    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
    ) as exception:
        raise InvalidDatasetError("Player feature table could not be read.") from exception


PLAYER_TOURNAMENT_SUMMARY_REQUIRED_COLUMNS = frozenset(
    {
        "player_id",
        "player_primary_position",
        "matches_played",
        "starts",
        "substitute_appearances",
        "captain_appearances",
        "total_minutes",
        "formations_used",
        "primary_formation",
        "primary_lineup_position",
    }
)


def load_player_tournament_summary(
    path: Path,
) -> pd.DataFrame:
    """Load the enriched tournament-level player summary."""

    if not path.exists():
        raise DatasetNotFoundError(f"Player tournament summary not found: {path}")

    try:
        dataframe = pd.read_csv(
            path,
            low_memory=False,
        )
    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
    ) as exception:
        raise InvalidDatasetError("Player tournament summary could not be read.") from exception

    missing_columns = PLAYER_TOURNAMENT_SUMMARY_REQUIRED_COLUMNS.difference(dataframe.columns)

    if missing_columns:
        raise InvalidDatasetError(
            "Missing player tournament summary columns: " + ", ".join(sorted(missing_columns))
        )

    player_ids = pd.to_numeric(
        dataframe["player_id"],
        errors="coerce",
    )

    if player_ids.isna().any():
        raise InvalidDatasetError("Player tournament summary contains an invalid player_id.")

    if not player_ids.gt(0).all():
        raise InvalidDatasetError("Player tournament summary contains a non-positive player_id.")

    if not player_ids.mod(1).eq(0).all():
        raise InvalidDatasetError("Player tournament summary contains a non-integer player_id.")

    result = dataframe.copy()

    result["player_id"] = player_ids.astype("int64")

    if result["player_id"].duplicated().any():
        raise InvalidDatasetError("Player tournament summary contains duplicate player IDs.")

    return result


def load_similarity(
    path: Path,
) -> pd.DataFrame:
    if not path.exists():
        raise DatasetNotFoundError(f"Similarity file not found: {path}")
    dataframe = pd.read_csv(
        path,
        low_memory=False,
    )

    required = {
        "source_player_id",
        "target_player_id",
        "overall_similarity_pct",
    }

    missing = required.difference(dataframe.columns)

    if missing:
        raise InvalidDatasetError("Missing similarity columns: " + ", ".join(sorted(missing)))
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


def load_heatmap_similarity(
    path: Path,
) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Heatmap similarity file not found: {path}")
    dataframe = pd.read_csv(
        path,
        low_memory=False,
    )

    required = {
        "target_player_id",
        "candidate_player_id",
        "heatmap_similarity_score_pct",
    }

    missing = required.difference(dataframe.columns)

    if missing:
        raise InvalidDatasetError(
            "Missing heatmap similarity columns: " + ", ".join(sorted(missing))
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

    result = dataframe[available_columns].copy()

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

    available = [column for column in useful_columns if column in dataframe.columns]

    result = dataframe[available].copy()

    result["player_id"] = pd.to_numeric(
        result["player_id"],
        errors="coerce",
    )

    return result.dropna(subset=["player_id"]).drop_duplicates("player_id")


__all__ = [
    "PLAYER_TOURNAMENT_SUMMARY_REQUIRED_COLUMNS",
    "load_heatmap_profiles",
    "load_heatmap_similarity",
    "load_player_features",
    "load_player_tournament_summary",
    "load_similarity",
]
