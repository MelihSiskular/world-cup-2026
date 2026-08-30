"""
Build tournament-level player heatmap profiles and normalized grids.

Input
-----
data/processed/player_heatmaps/player_heatmaps_match_level.csv

Outputs
-------
data/processed/player_heatmaps/player_heatmap_profiles.csv
data/processed/player_heatmaps/player_heatmap_grids.npz
data/processed/player_heatmaps/player_heatmap_grid_index.csv

Examples
--------
python -m src.player_heatmaps.build_player_heatmap_profiles

python -m src.player_heatmaps.build_player_heatmap_profiles \
    --grid-x 21 \
    --grid-y 14 \
    --sigma 1.2
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter

"""
RUN

python -m src.player_heatmaps.build_player_heatmap_profiles

"""
DEFAULT_INPUT = Path("data/processed/player_heatmaps/player_heatmaps_match_level.csv")

DEFAULT_OUTPUT_DIR = Path("data/processed/player_heatmaps")


def safe_divide(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator > 0 else 0.0


def normalized_entropy(values: np.ndarray) -> float:
    flat = np.asarray(values, dtype=np.float64).reshape(-1)
    total = flat.sum()

    if total <= 0:
        return 0.0

    probabilities = flat / total
    probabilities = probabilities[probabilities > 0]

    if probabilities.size <= 1:
        return 0.0

    entropy = -np.sum(probabilities * np.log(probabilities))
    maximum_entropy = math.log(probabilities.size)

    return float(entropy / maximum_entropy) if maximum_entropy > 0 else 0.0


def weighted_mean(
    values: np.ndarray,
    weights: np.ndarray,
) -> float:
    total = weights.sum()

    if total <= 0:
        return 0.0

    return float(np.sum(values * weights) / total)


def weighted_std(
    values: np.ndarray,
    weights: np.ndarray,
    mean: float,
) -> float:
    total = weights.sum()

    if total <= 0:
        return 0.0

    variance = np.sum(weights * np.square(values - mean)) / total

    return float(np.sqrt(max(variance, 0.0)))


def zone_share(
    values: np.ndarray,
    mask: np.ndarray,
) -> float:
    total = values.sum()

    if total <= 0:
        return 0.0

    return float(values[mask].sum() / total)


def assign_grid_indices(
    x: np.ndarray,
    y: np.ndarray,
    grid_x: int,
    grid_y: int,
) -> tuple[np.ndarray, np.ndarray]:
    x_index = np.floor(np.clip(x, 0, 100) / 100 * grid_x).astype(int)

    y_index = np.floor(np.clip(y, 0, 100) / 100 * grid_y).astype(int)

    return (
        np.clip(x_index, 0, grid_x - 1),
        np.clip(y_index, 0, grid_y - 1),
    )


def build_raw_grid(
    x: np.ndarray,
    y: np.ndarray,
    weights: np.ndarray,
    grid_x: int,
    grid_y: int,
) -> np.ndarray:
    grid = np.zeros(
        (grid_y, grid_x),
        dtype=np.float64,
    )

    x_index, y_index = assign_grid_indices(
        x,
        y,
        grid_x,
        grid_y,
    )

    np.add.at(
        grid,
        (y_index, x_index),
        weights,
    )

    return grid


def normalize_sum(grid: np.ndarray) -> np.ndarray:
    total = grid.sum()

    if total <= 0:
        return np.zeros_like(
            grid,
            dtype=np.float32,
        )

    return (grid / total).astype(np.float32)


def derive_profiles(
    input_path: Path,
    output_dir: Path,
    grid_x: int,
    grid_y: int,
    sigma: float,
    occupied_threshold: float,
    minimum_points: int,
) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    if not input_path.exists():
        raise FileNotFoundError(f"Heatmap input not found: {input_path}")

    dataframe = pd.read_csv(
        input_path,
        low_memory=False,
    )

    required_columns = {
        "player_id",
        "player_name",
        "event_id",
        "x",
        "y",
        "count",
    }

    missing = required_columns.difference(dataframe.columns)

    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))

    dataframe = dataframe.copy()

    for column in [
        "player_id",
        "event_id",
        "x",
        "y",
        "count",
        "minutes_played",
    ]:
        if column in dataframe.columns:
            dataframe[column] = pd.to_numeric(
                dataframe[column],
                errors="coerce",
            )

    dataframe = dataframe.dropna(
        subset=[
            "player_id",
            "event_id",
            "x",
            "y",
        ]
    )

    dataframe["count"] = dataframe["count"].fillna(1.0).clip(lower=0)

    dataframe = dataframe[dataframe["x"].between(0, 100) & dataframe["y"].between(0, 100)].copy()

    dataframe["player_id"] = dataframe["player_id"].astype("int64")

    dataframe["event_id"] = dataframe["event_id"].astype("int64")

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    profile_rows: list[dict[str, Any]] = []
    grids: dict[str, np.ndarray] = {}

    x_centres = (np.arange(grid_x) + 0.5) / grid_x * 100

    y_centres = (np.arange(grid_y) + 0.5) / grid_y * 100

    grid_x_mesh, grid_y_mesh = np.meshgrid(
        x_centres,
        y_centres,
    )

    # Saha genişliği: y ekseni
    lateral_masks = {
        "left_wide": grid_y_mesh < 20,
        "left_half_space": ((grid_y_mesh >= 20) & (grid_y_mesh < 40)),
        "central": ((grid_y_mesh >= 40) & (grid_y_mesh < 60)),
        "right_half_space": ((grid_y_mesh >= 60) & (grid_y_mesh < 80)),
        "right_wide": grid_y_mesh >= 80,
    }

    # Saha uzunluğu: x ekseni
    vertical_masks = {
        "build_up": grid_x_mesh < 25,
        "middle_third": ((grid_x_mesh >= 25) & (grid_x_mesh < 50)),
        "advanced_middle": ((grid_x_mesh >= 50) & (grid_x_mesh < 75)),
        "final_third": grid_x_mesh >= 75,
    }

    grouped = dataframe.groupby(
        "player_id",
        sort=True,
    )

    total_players = grouped.ngroups

    for index, (player_id, group) in enumerate(
        grouped,
        start=1,
    ):
        point_count = len(group)

        if point_count < minimum_points:
            continue

        x = group["x"].to_numpy(dtype=np.float64)
        y = group["y"].to_numpy(dtype=np.float64)
        weights = group["count"].to_numpy(dtype=np.float64)

        raw_grid = build_raw_grid(
            x=x,
            y=y,
            weights=weights,
            grid_x=grid_x,
            grid_y=grid_y,
        )

        smoothed_grid = (
            gaussian_filter(
                raw_grid,
                sigma=sigma,
                mode="constant",
            )
            if sigma > 0
            else raw_grid.copy()
        )

        probability_grid = normalize_sum(smoothed_grid)

        grids[str(int(player_id))] = probability_grid

        mean_x = weighted_mean(x, weights)
        mean_y = weighted_mean(y, weights)
        std_x = weighted_std(x, weights, mean_x)
        std_y = weighted_std(y, weights, mean_y)
        spatial_spread = float(np.sqrt(std_x**2 + std_y**2))

        maximum_cell = float(probability_grid.max())

        occupied_mask = (
            probability_grid >= maximum_cell * occupied_threshold
            if maximum_cell > 0
            else np.zeros_like(
                probability_grid,
                dtype=bool,
            )
        )

        peak_y_index, peak_x_index = np.unravel_index(
            np.argmax(probability_grid),
            probability_grid.shape,
        )

        player_name_mode = group["player_name"].dropna().astype(str).mode()

        team_name_mode = (
            group["team_name"].dropna().astype(str).mode()
            if "team_name" in group.columns
            else pd.Series(dtype=str)
        )

        team_id_mode = (
            group["team_id"].dropna().mode()
            if "team_id" in group.columns
            else pd.Series(dtype=float)
        )

        if "minutes_played" in group.columns:
            unique_minutes = group[["event_id", "minutes_played"]].drop_duplicates("event_id")

            minutes = unique_minutes["minutes_played"].sum(min_count=1)
        else:
            minutes = np.nan

        row: dict[str, Any] = {
            "player_id": int(player_id),
            "player_name": (player_name_mode.iloc[0] if not player_name_mode.empty else ""),
            "team_id": (
                int(team_id_mode.iloc[0])
                if not team_id_mode.empty and pd.notna(team_id_mode.iloc[0])
                else pd.NA
            ),
            "team_name": (team_name_mode.iloc[0] if not team_name_mode.empty else ""),
            "matches_with_heatmap": int(group["event_id"].nunique()),
            "heatmap_point_count": int(point_count),
            "weighted_point_count": float(weights.sum()),
            "minutes_with_heatmap": (float(minutes) if pd.notna(minutes) else np.nan),
            "weighted_mean_x": mean_x,
            "weighted_mean_y": mean_y,
            "weighted_std_x": std_x,
            "weighted_std_y": std_y,
            "spatial_spread": spatial_spread,
            "heatmap_entropy": normalized_entropy(probability_grid),
            "occupied_cell_count": int(occupied_mask.sum()),
            "occupied_cell_share": safe_divide(
                occupied_mask.sum(),
                probability_grid.size,
            ),
            "peak_cell_x": float(x_centres[peak_x_index]),
            "peak_cell_y": float(y_centres[peak_y_index]),
            "peak_cell_share": maximum_cell,
            "grid_x": grid_x,
            "grid_y": grid_y,
            "gaussian_sigma": sigma,
        }

        for zone_name, mask in lateral_masks.items():
            row[f"{zone_name}_share"] = zone_share(
                probability_grid,
                mask,
            )

        for zone_name, mask in vertical_masks.items():
            row[f"{zone_name}_share"] = zone_share(
                probability_grid,
                mask,
            )

        row["left_share"] = row["left_wide_share"] + row["left_half_space_share"]

        row["right_share"] = row["right_half_space_share"] + row["right_wide_share"]

        row["central_lane_share"] = row["central_share"]

        profile_rows.append(row)

        if index % 100 == 0 or index == total_players:
            print(f"[{index}/{total_players}] processed player_id={player_id} points={point_count}")

    profiles = pd.DataFrame(profile_rows)

    if not profiles.empty:
        profiles = profiles.sort_values(
            [
                "matches_with_heatmap",
                "heatmap_point_count",
            ],
            ascending=False,
        ).reset_index(drop=True)

    return profiles, grids


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Build normalized player heatmap grids and tournament-level heatmap profiles.")
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )

    parser.add_argument(
        "--grid-x",
        type=int,
        default=21,
    )

    parser.add_argument(
        "--grid-y",
        type=int,
        default=14,
    )

    parser.add_argument(
        "--sigma",
        type=float,
        default=1.2,
    )

    parser.add_argument(
        "--occupied-threshold",
        type=float,
        default=0.10,
    )

    parser.add_argument(
        "--minimum-points",
        type=int,
        default=10,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.grid_x < 2:
        raise ValueError("--grid-x must be at least 2.")

    if args.grid_y < 2:
        raise ValueError("--grid-y must be at least 2.")

    if args.sigma < 0:
        raise ValueError("--sigma cannot be negative.")

    if not 0 < args.occupied_threshold <= 1:
        raise ValueError("--occupied-threshold must be in (0, 1].")

    profiles, grids = derive_profiles(
        input_path=args.input,
        output_dir=args.output_dir,
        grid_x=args.grid_x,
        grid_y=args.grid_y,
        sigma=args.sigma,
        occupied_threshold=args.occupied_threshold,
        minimum_points=args.minimum_points,
    )

    profiles_path = args.output_dir / "player_heatmap_profiles.csv"

    profiles.to_csv(
        profiles_path,
        index=False,
        encoding="utf-8-sig",
    )

    grids_path = args.output_dir / "player_heatmap_grids.npz"

    np.savez_compressed(
        grids_path,
        **grids,
    )

    index_frame = profiles[
        [
            "player_id",
            "player_name",
            "team_name",
            "matches_with_heatmap",
            "heatmap_point_count",
            "grid_x",
            "grid_y",
        ]
    ].copy()

    index_frame["npz_key"] = index_frame["player_id"].astype(str)

    index_path = args.output_dir / "player_heatmap_grid_index.csv"

    index_frame.to_csv(
        index_path,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print("=" * 82)
    print("PLAYER HEATMAP PROFILE SUMMARY")
    print("=" * 82)
    print(f"Players written:       {len(profiles):>8}")
    print(f"Grids written:         {len(grids):>8}")

    if not profiles.empty:
        print(f"Median heatmap points: {profiles['heatmap_point_count'].median():>8.1f}")
        print(f"Median matches:        {profiles['matches_with_heatmap'].median():>8.1f}")
        print(f"Median entropy:        {profiles['heatmap_entropy'].median():>8.3f}")

    print()
    print("OUTPUTS")
    print(f"Profiles: {profiles_path}")
    print(f"Grids:    {grids_path}")
    print(f"Index:    {index_path}")


if __name__ == "__main__":
    main()
