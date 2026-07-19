# -*- coding: utf-8 -*-
"""
Calculate player heatmap similarity from tournament-level heatmap grids.

Inputs
------
data/processed/player_heatmaps/player_heatmap_profiles.csv
data/processed/player_heatmaps/player_heatmap_grids.npz

Optional metadata
-----------------
A player metadata table may be supplied to restrict comparisons to the same
position group. The script automatically looks for common columns such as:

    player_id
    analysis_position
    position_group
    position
    final_position_group

Outputs
-------
data/processed/player_heatmaps/heatmap_similarity_long.csv
data/processed/player_heatmaps/heatmap_similarity_top_matches.csv
data/processed/player_heatmaps/heatmap_similarity_matrix.npz

Examples
--------
# Compare players inside the same position group when metadata is available.
python -m src.player_heatmaps.calculate_heatmap_similarity

# Explicit metadata file.
python -m src.player_heatmaps.calculate_heatmap_similarity \
    --metadata data/processed/transfer_intelligence/transfer_feature_table.csv

# Compare every player with every other player.
python -m src.player_heatmaps.calculate_heatmap_similarity \
    --all-positions

# Keep only the top 25 neighbours per player.
python -m src.player_heatmaps.calculate_heatmap_similarity \
    --top-k 25

Metric definitions
------------------
heatmap_cosine_similarity:
    Cosine similarity between flattened normalized heatmap grids.

occupation_overlap:
    Sum of the cellwise minimum probability distributions.
    This is bounded between 0 and 1.

lateral_profile_similarity:
    Similarity between five lateral occupation shares.

vertical_profile_similarity:
    Similarity between four vertical occupation shares.

peak_zone_similarity:
    Similarity based on Euclidean distance between peak cells.

entropy_similarity:
    Similarity between normalized heatmap entropy values.

heatmap_similarity_score:
    Weighted, interpretable final score:
        cosine       50%
        overlap      20%
        lateral      10%
        vertical     10%
        peak zone     5%
        entropy       5%
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


DEFAULT_PROFILES = Path(
    "data/processed/player_heatmaps/"
    "player_heatmap_profiles.csv"
)

DEFAULT_GRIDS = Path(
    "data/processed/player_heatmaps/"
    "player_heatmap_grids.npz"
)

DEFAULT_OUTPUT_DIR = Path(
    "data/processed/player_heatmaps"
)

DEFAULT_METADATA_CANDIDATES = [
    Path(
        "data/processed/transfer_intelligence/"
        "transfer_feature_table.csv"
    ),
    Path(
        "data/processed/player_archetypes/"
        "player_archetypes.csv"
    ),
    Path(
        "data/processed/weekly_team_analysis/"
        "top_players_by_stage_position.csv"
    ),
]

POSITION_COLUMN_CANDIDATES = [
    "analysis_position",
    "position_group",
    "final_position_group",
    "broad_position",
    "position",
]

LATERAL_COLUMNS = [
    "left_wide_share",
    "left_half_space_share",
    "central_share",
    "right_half_space_share",
    "right_wide_share",
]

VERTICAL_COLUMNS = [
    "build_up_share",
    "middle_third_share",
    "advanced_middle_share",
    "final_third_share",
]


def first_existing_column(
    dataframe: pd.DataFrame,
    candidates: Iterable[str],
) -> str | None:
    for column in candidates:
        if column in dataframe.columns:
            return column

    return None


def safe_numeric(
    series: pd.Series,
) -> pd.Series:
    return pd.to_numeric(
        series,
        errors="coerce",
    )


def normalize_vector(
    values: np.ndarray,
) -> np.ndarray:
    values = np.asarray(
        values,
        dtype=np.float64,
    )

    total = values.sum()

    if total <= 0:
        return np.zeros_like(values)

    return values / total


def vector_similarity(
    first: np.ndarray,
    second: np.ndarray,
) -> float:
    """
    Distribution similarity in [0, 1].

    This uses total variation similarity:
        1 - 0.5 * sum(abs(p - q))
    """
    first = normalize_vector(first)
    second = normalize_vector(second)

    distance = 0.5 * np.abs(
        first - second
    ).sum()

    return float(
        np.clip(
            1.0 - distance,
            0.0,
            1.0,
        )
    )


def occupation_overlap(
    first: np.ndarray,
    second: np.ndarray,
) -> float:
    first = normalize_vector(
        first.reshape(-1)
    )

    second = normalize_vector(
        second.reshape(-1)
    )

    return float(
        np.minimum(
            first,
            second,
        ).sum()
    )


def peak_zone_similarity(
    first_x: float,
    first_y: float,
    second_x: float,
    second_y: float,
) -> tuple[float, float]:
    """
    Return similarity and raw normalized Euclidean distance.

    Coordinates are on the 0-100 SofaScore scale.
    Maximum possible diagonal distance is sqrt(100^2 + 100^2).
    """
    distance = float(
        np.hypot(
            first_x - second_x,
            first_y - second_y,
        )
    )

    maximum_distance = float(
        np.hypot(100.0, 100.0)
    )

    normalized_distance = (
        distance / maximum_distance
    )

    similarity = float(
        np.clip(
            1.0 - normalized_distance,
            0.0,
            1.0,
        )
    )

    return similarity, distance


def scalar_similarity(
    first: float,
    second: float,
    scale: float = 1.0,
) -> float:
    if scale <= 0:
        raise ValueError(
            "scale must be positive."
        )

    return float(
        np.clip(
            1.0
            - abs(first - second) / scale,
            0.0,
            1.0,
        )
    )


def discover_metadata(
    explicit_path: Path | None,
) -> Path | None:
    if explicit_path is not None:
        return (
            explicit_path
            if explicit_path.exists()
            else None
        )

    for candidate in (
        DEFAULT_METADATA_CANDIDATES
    ):
        if candidate.exists():
            return candidate

    return None


def normalize_position_group(
    value: object,
) -> str:
    if value is None or pd.isna(value):
        return "UNKNOWN"

    text = str(value).strip().upper()

    mappings = {
        "GK": "G",
        "GOALKEEPER": "G",
        "G": "G",
        "CB": "D",
        "LB": "D",
        "RB": "D",
        "LWB": "D",
        "RWB": "D",
        "DEFENDER": "D",
        "D": "D",
        "DM": "M",
        "CM": "M",
        "AM": "M",
        "LM": "M",
        "RM": "M",
        "MIDFIELDER": "M",
        "M": "M",
        "LW": "F",
        "RW": "F",
        "ST": "F",
        "CF": "F",
        "FORWARD": "F",
        "F": "F",
    }

    return mappings.get(
        text,
        text,
    )


def enrich_profiles_with_metadata(
    profiles: pd.DataFrame,
    metadata_path: Path | None,
) -> tuple[pd.DataFrame, str | None]:
    profiles = profiles.copy()

    if metadata_path is None:
        profiles["position_group"] = (
            "UNKNOWN"
        )

        return profiles, None

    metadata = pd.read_csv(
        metadata_path,
        low_memory=False,
    )

    if "player_id" not in metadata.columns:
        profiles["position_group"] = (
            "UNKNOWN"
        )

        return profiles, None

    position_column = (
        first_existing_column(
            metadata,
            POSITION_COLUMN_CANDIDATES,
        )
    )

    if position_column is None:
        profiles["position_group"] = (
            "UNKNOWN"
        )

        return profiles, None

    metadata = metadata[
        [
            "player_id",
            position_column,
        ]
    ].copy()

    metadata["player_id"] = (
        safe_numeric(
            metadata["player_id"]
        )
    )

    metadata = metadata.dropna(
        subset=["player_id"]
    )

    metadata["player_id"] = (
        metadata["player_id"]
        .astype("int64")
    )

    metadata["position_group"] = (
        metadata[position_column]
        .map(normalize_position_group)
    )

    metadata = (
        metadata[
            [
                "player_id",
                "position_group",
            ]
        ]
        .drop_duplicates("player_id")
    )

    profiles = profiles.merge(
        metadata,
        on="player_id",
        how="left",
    )

    profiles["position_group"] = (
        profiles["position_group"]
        .fillna("UNKNOWN")
    )

    return profiles, position_column


def load_inputs(
    profiles_path: Path,
    grids_path: Path,
    metadata_path: Path | None,
) -> tuple[
    pd.DataFrame,
    np.lib.npyio.NpzFile,
    str | None,
]:
    if not profiles_path.exists():
        raise FileNotFoundError(
            f"Profiles not found: {profiles_path}"
        )

    if not grids_path.exists():
        raise FileNotFoundError(
            f"Grids not found: {grids_path}"
        )

    profiles = pd.read_csv(
        profiles_path,
        low_memory=False,
    )

    required_columns = {
        "player_id",
        "player_name",
        "heatmap_entropy",
        "peak_cell_x",
        "peak_cell_y",
        *LATERAL_COLUMNS,
        *VERTICAL_COLUMNS,
    }

    missing = required_columns.difference(
        profiles.columns
    )

    if missing:
        raise ValueError(
            "Missing profile columns: "
            + ", ".join(sorted(missing))
        )

    profiles["player_id"] = (
        safe_numeric(
            profiles["player_id"]
        )
    )

    profiles = profiles.dropna(
        subset=["player_id"]
    )

    profiles["player_id"] = (
        profiles["player_id"]
        .astype("int64")
    )

    profiles, position_source = (
        enrich_profiles_with_metadata(
            profiles,
            metadata_path,
        )
    )

    grids = np.load(
        grids_path
    )

    available = set(
        grids.files
    )

    profiles = profiles[
        profiles["player_id"]
        .astype(str)
        .isin(available)
    ].copy()

    profiles = profiles.reset_index(
        drop=True
    )

    return (
        profiles,
        grids,
        position_source,
    )


def calculate_group_similarities(
    group: pd.DataFrame,
    grids: np.lib.npyio.NpzFile,
    top_k: int | None,
) -> tuple[
    list[dict[str, object]],
    dict[str, np.ndarray],
]:
    """
    Calculate pairwise similarities inside one position group.
    """
    player_ids = (
        group["player_id"]
        .astype(int)
        .tolist()
    )

    grid_matrix = np.vstack(
        [
            np.asarray(
                grids[str(player_id)],
                dtype=np.float64,
            ).reshape(-1)
            for player_id in player_ids
        ]
    )

    cosine_matrix = cosine_similarity(
        grid_matrix
    )

    rows: list[
        dict[str, object]
    ] = []

    matrix_outputs: dict[
        str,
        np.ndarray
    ] = {}

    final_matrix = np.eye(
        len(group),
        dtype=np.float32,
    )

    group_records = group.to_dict(
        "records"
    )

    for first_index, first in enumerate(
        group_records
    ):
        candidate_rows: list[
            dict[str, object]
        ] = []

        first_grid = grid_matrix[
            first_index
        ].reshape(
            int(first["grid_y"]),
            int(first["grid_x"]),
        )

        first_lateral = np.array(
            [
                float(first[column])
                for column in LATERAL_COLUMNS
            ],
            dtype=np.float64,
        )

        first_vertical = np.array(
            [
                float(first[column])
                for column in VERTICAL_COLUMNS
            ],
            dtype=np.float64,
        )

        for second_index, second in enumerate(
            group_records
        ):
            if first_index == second_index:
                continue

            second_grid = grid_matrix[
                second_index
            ].reshape(
                int(second["grid_y"]),
                int(second["grid_x"]),
            )

            cosine = float(
                cosine_matrix[
                    first_index,
                    second_index,
                ]
            )

            overlap = occupation_overlap(
                first_grid,
                second_grid,
            )

            lateral = vector_similarity(
                first_lateral,
                np.array(
                    [
                        float(second[column])
                        for column
                        in LATERAL_COLUMNS
                    ],
                    dtype=np.float64,
                ),
            )

            vertical = vector_similarity(
                first_vertical,
                np.array(
                    [
                        float(second[column])
                        for column
                        in VERTICAL_COLUMNS
                    ],
                    dtype=np.float64,
                ),
            )

            peak_similarity, peak_distance = (
                peak_zone_similarity(
                    float(first["peak_cell_x"]),
                    float(first["peak_cell_y"]),
                    float(second["peak_cell_x"]),
                    float(second["peak_cell_y"]),
                )
            )

            entropy = scalar_similarity(
                float(
                    first["heatmap_entropy"]
                ),
                float(
                    second["heatmap_entropy"]
                ),
                scale=1.0,
            )

            final_score = (
                cosine * 0.50
                + overlap * 0.20
                + lateral * 0.10
                + vertical * 0.10
                + peak_similarity * 0.05
                + entropy * 0.05
            )

            final_matrix[
                first_index,
                second_index,
            ] = final_score

            candidate_rows.append(
                {
                    "target_player_id": int(
                        first["player_id"]
                    ),
                    "target_player_name": str(
                        first["player_name"]
                    ),
                    "candidate_player_id": int(
                        second["player_id"]
                    ),
                    "candidate_player_name": str(
                        second["player_name"]
                    ),
                    "position_group": str(
                        first["position_group"]
                    ),
                    "target_matches_with_heatmap": int(
                        first[
                            "matches_with_heatmap"
                        ]
                    ),
                    "candidate_matches_with_heatmap": int(
                        second[
                            "matches_with_heatmap"
                        ]
                    ),
                    "target_heatmap_points": int(
                        first[
                            "heatmap_point_count"
                        ]
                    ),
                    "candidate_heatmap_points": int(
                        second[
                            "heatmap_point_count"
                        ]
                    ),
                    "heatmap_cosine_similarity": cosine,
                    "occupation_overlap": overlap,
                    "lateral_profile_similarity": lateral,
                    "vertical_profile_similarity": vertical,
                    "peak_zone_similarity": peak_similarity,
                    "peak_zone_distance": peak_distance,
                    "entropy_similarity": entropy,
                    "heatmap_similarity_score": final_score,
                }
            )

        candidate_rows.sort(
            key=lambda row: row[
                "heatmap_similarity_score"
            ],
            reverse=True,
        )

        if top_k is not None:
            candidate_rows = (
                candidate_rows[:top_k]
            )

        for rank, row in enumerate(
            candidate_rows,
            start=1,
        ):
            row[
                "heatmap_similarity_rank"
            ] = rank

            rows.append(row)

    matrix_key = (
        str(
            group["position_group"]
            .iloc[0]
        )
    )

    matrix_outputs[
        f"{matrix_key}_player_ids"
    ] = np.asarray(
        player_ids,
        dtype=np.int64,
    )

    matrix_outputs[
        f"{matrix_key}_similarity"
    ] = final_matrix

    return rows, matrix_outputs


def calculate_similarities(
    profiles: pd.DataFrame,
    grids: np.lib.npyio.NpzFile,
    *,
    all_positions: bool,
    top_k: int | None,
    minimum_matches: int,
    minimum_points: int,
) -> tuple[
    pd.DataFrame,
    dict[str, np.ndarray],
]:
    eligible = profiles[
        profiles[
            "matches_with_heatmap"
        ].ge(minimum_matches)
        & profiles[
            "heatmap_point_count"
        ].ge(minimum_points)
    ].copy()

    if all_positions:
        eligible[
            "comparison_group"
        ] = "ALL"
    else:
        eligible[
            "comparison_group"
        ] = eligible[
            "position_group"
        ]

        # Unknown positions would otherwise be compared as one arbitrary
        # group. Exclude them when position filtering is requested.
        eligible = eligible[
            eligible[
                "comparison_group"
            ].ne("UNKNOWN")
        ].copy()

    all_rows: list[
        dict[str, object]
    ] = []

    all_matrices: dict[
        str,
        np.ndarray
    ] = {}

    grouped = eligible.groupby(
        "comparison_group",
        sort=True,
    )

    for group_name, group in grouped:
        group = group.copy()

        # The internal calculation expects position_group as its label.
        group[
            "position_group"
        ] = str(group_name)

        if len(group) < 2:
            continue

        print(
            f"Calculating group={group_name} "
            f"players={len(group)}"
        )

        rows, matrices = (
            calculate_group_similarities(
                group,
                grids,
                top_k,
            )
        )

        all_rows.extend(rows)
        all_matrices.update(matrices)

    result = pd.DataFrame(
        all_rows
    )

    if not result.empty:
        result = result.sort_values(
            [
                "target_player_id",
                "heatmap_similarity_rank",
            ]
        ).reset_index(drop=True)

        percentage_columns = [
            "heatmap_cosine_similarity",
            "occupation_overlap",
            "lateral_profile_similarity",
            "vertical_profile_similarity",
            "peak_zone_similarity",
            "entropy_similarity",
            "heatmap_similarity_score",
        ]

        for column in percentage_columns:
            result[
                f"{column}_pct"
            ] = result[column] * 100.0

    return result, all_matrices


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Calculate pairwise player heatmap similarity."
        )
    )

    parser.add_argument(
        "--profiles",
        type=Path,
        default=DEFAULT_PROFILES,
    )

    parser.add_argument(
        "--grids",
        type=Path,
        default=DEFAULT_GRIDS,
    )

    parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=50,
        help=(
            "Number of neighbours retained per player. "
            "Use 0 to retain every comparison."
        ),
    )

    parser.add_argument(
        "--minimum-matches",
        type=int,
        default=2,
    )

    parser.add_argument(
        "--minimum-points",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--all-positions",
        action="store_true",
        help=(
            "Compare every eligible player instead of restricting "
            "comparisons to the same position group."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    metadata_path = discover_metadata(
        args.metadata
    )

    profiles, grids, position_source = (
        load_inputs(
            args.profiles,
            args.grids,
            metadata_path,
        )
    )

    top_k = (
        None
        if args.top_k == 0
        else max(1, args.top_k)
    )

    result, matrices = (
        calculate_similarities(
            profiles,
            grids,
            all_positions=args.all_positions,
            top_k=top_k,
            minimum_matches=max(
                1,
                args.minimum_matches,
            ),
            minimum_points=max(
                1,
                args.minimum_points,
            ),
        )
    )

    args.output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    long_path = (
        args.output_dir
        / "heatmap_similarity_long.csv"
    )

    result.to_csv(
        long_path,
        index=False,
        encoding="utf-8-sig",
    )

    top_path = (
        args.output_dir
        / "heatmap_similarity_top_matches.csv"
    )

    if result.empty:
        top_frame = result.copy()
    else:
        top_frame = result[
            result[
                "heatmap_similarity_rank"
            ].le(10)
        ].copy()

    top_frame.to_csv(
        top_path,
        index=False,
        encoding="utf-8-sig",
    )

    matrix_path = (
        args.output_dir
        / "heatmap_similarity_matrix.npz"
    )

    np.savez_compressed(
        matrix_path,
        **matrices,
    )

    print()
    print("=" * 82)
    print("HEATMAP SIMILARITY SUMMARY")
    print("=" * 82)
    print(
        f"Profiles loaded:        "
        f"{len(profiles):>8}"
    )
    print(
        f"Similarity rows:        "
        f"{len(result):>8}"
    )
    print(
        f"Targets represented:    "
        f"{result['target_player_id'].nunique() if not result.empty else 0:>8}"
    )
    print(
        f"Position metadata:      "
        f"{str(metadata_path) if metadata_path else 'not found'}"
    )
    print(
        f"Position source column: "
        f"{position_source or 'none'}"
    )

    if not result.empty:
        print(
            f"Median final score:     "
            f"{result['heatmap_similarity_score_pct'].median():>7.2f}%"
        )
        print(
            f"Median cosine score:    "
            f"{result['heatmap_cosine_similarity_pct'].median():>7.2f}%"
        )
        print(
            f"Median overlap:         "
            f"{result['occupation_overlap_pct'].median():>7.2f}%"
        )

    print()
    print("OUTPUTS")
    print(f"Long table: {long_path}")
    print(f"Top matches: {top_path}")
    print(f"Matrices:   {matrix_path}")


if __name__ == "__main__":
    main()
