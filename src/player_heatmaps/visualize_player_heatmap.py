# -*- coding: utf-8 -*-
"""
Visualize tournament-level player heatmaps.

Inputs
------
data/processed/player_heatmaps/player_heatmap_profiles.csv
data/processed/player_heatmaps/player_heatmap_grids.npz

Outputs
-------
docs/images/player_heatmaps/

Modes
-----
single:
    One player's tournament heatmap.

compare:
    Two players shown side by side using a shared intensity scale.

overlay:
    Two players overlaid on one pitch:
    target = yellow
    candidate = green
    overlap = pale bright areas

Examples
--------
python -m src.player_heatmaps.visualize_player_heatmap \
    --player "Michael Olise" \
    --mode single

python -m src.player_heatmaps.visualize_player_heatmap \
    --player "Michael Olise" \
    --candidate "Stephen Eustaquio" \
    --mode compare

python -m src.player_heatmaps.visualize_player_heatmap \
    --player "Michael Olise" \
    --candidate "Stephen Eustaquio" \
    --mode overlay
"""

from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


DEFAULT_PROFILES = Path(
    "data/processed/player_heatmaps/"
    "player_heatmap_profiles.csv"
)

DEFAULT_GRIDS = Path(
    "data/processed/player_heatmaps/"
    "player_heatmap_grids.npz"
)

DEFAULT_OUTPUT_DIR = Path(
    "docs/images/player_heatmaps"
)


BACKGROUND = "#06110D"
PANEL = "#0B1B15"
PITCH = "#10251C"
PITCH_STRIPE = "#173126"
LINES = "#D6E5DE"
TEXT = "#F3FFF8"
TEXT_SOFT = "#AFC8BC"
TEXT_MUTED = "#7F9B8D"

TARGET_COLOR = "#F0C75A"
CANDIDATE_COLOR = "#55D991"

PITCH_LENGTH = 105.0
PITCH_WIDTH = 68.0


def slugify(value: str) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        str(value),
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


def clean_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return "-"

    return str(value).strip()


def load_profiles(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Profiles file not found: {path}"
        )

    dataframe = pd.read_csv(
        path,
        low_memory=False,
    )

    required = {
        "player_id",
        "player_name",
        "weighted_mean_x",
        "weighted_mean_y",
        "heatmap_point_count",
        "matches_with_heatmap",
        "heatmap_entropy",
    }

    missing = required.difference(
        dataframe.columns
    )

    if missing:
        raise ValueError(
            "Missing profile columns: "
            + ", ".join(sorted(missing))
        )

    dataframe["player_id"] = pd.to_numeric(
        dataframe["player_id"],
        errors="coerce",
    )

    return dataframe


def resolve_player(
    profiles: pd.DataFrame,
    query: str,
) -> pd.Series:
    exact = profiles[
        profiles["player_name"]
        .astype(str)
        .str.casefold()
        .eq(query.casefold())
    ]

    if len(exact) == 1:
        return exact.iloc[0]

    partial = profiles[
        profiles["player_name"]
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


def load_grid(
    grids: np.lib.npyio.NpzFile,
    player_id: int,
) -> np.ndarray:
    key = str(int(player_id))

    if key not in grids.files:
        raise KeyError(
            f"Grid not found for player_id={key}"
        )

    return np.asarray(
        grids[key],
        dtype=np.float64,
    )


def pitch_x(value: float) -> float:
    return float(value) / 100.0 * PITCH_LENGTH


def pitch_y(value: float) -> float:
    return float(value) / 100.0 * PITCH_WIDTH


def normalize_for_display(
    grid: np.ndarray,
    *,
    shared_peak: float | None = None,
    floor_ratio: float = 0.16,
    gamma: float = 1.75,
) -> np.ndarray:
    """
    Prepare probability grid for visual display.

    Important behavior:
    - Very low density is removed.
    - Medium density remains translucent.
    - Only genuine peaks become strongly visible.

    Higher gamma values make the heatmap more selective.
    """
    peak = (
        float(shared_peak)
        if shared_peak is not None
        else float(grid.max())
    )

    if peak <= 0:
        return np.zeros_like(
            grid,
            dtype=np.float64,
        )

    normalized = np.clip(
        grid / peak,
        0.0,
        1.0,
    )

    # Remove weak background activity.
    adjusted = np.clip(
        (
            normalized
            - floor_ratio
        )
        / max(
            1.0 - floor_ratio,
            1e-9,
        ),
        0.0,
        1.0,
    )

    # Make only the strongest areas visually dominant.
    return np.power(
        adjusted,
        gamma,
    )


def hex_to_rgb(
    color: str,
) -> tuple[float, float, float]:
    color = color.lstrip("#")

    return (
        int(color[0:2], 16) / 255.0,
        int(color[2:4], 16) / 255.0,
        int(color[4:6], 16) / 255.0,
    )


def colorize_grid(
    grid: np.ndarray,
    color: str,
    *,
    shared_peak: float | None = None,
    floor_ratio: float = 0.16,
    gamma: float = 1.75,
    max_alpha: float = 0.82,
) -> np.ndarray:
    """
    Convert a probability grid into an RGBA heatmap.

    Low-density cells remain transparent. Peak cells are brighter and more
    opaque, while the pitch remains visible below the heat layer.
    """
    intensity = normalize_for_display(
        grid,
        shared_peak=shared_peak,
        floor_ratio=floor_ratio,
        gamma=gamma,
    )

    base_rgb = np.array(
        hex_to_rgb(color),
        dtype=np.float64,
    )

    highlight_rgb = np.array(
        (1.0, 0.98, 0.78),
        dtype=np.float64,
    )

    rgba = np.zeros(
        (*intensity.shape, 4),
        dtype=np.float64,
    )

    blend = np.power(
        intensity,
        1.35,
    )[..., None]

    rgba[..., :3] = (
        base_rgb * (1.0 - blend)
        + highlight_rgb * blend
    )

    rgba[..., 3] = (
        intensity * max_alpha
    )

    return rgba


def draw_pitch(
    axis: plt.Axes,
) -> None:
    """
    Draw a horizontal 105 x 68 metre football pitch.
    """
    axis.set_facecolor(PITCH)

    # Subtle mowing stripes.
    stripe_count = 12
    stripe_width = PITCH_LENGTH / stripe_count

    for stripe in range(stripe_count):
        if stripe % 2 == 0:
            axis.axvspan(
                stripe * stripe_width,
                (stripe + 1) * stripe_width,
                color=PITCH_STRIPE,
                alpha=0.22,
                zorder=0,
            )

    # Outer pitch.
    axis.plot(
        [
            0,
            PITCH_LENGTH,
            PITCH_LENGTH,
            0,
            0,
        ],
        [
            0,
            0,
            PITCH_WIDTH,
            PITCH_WIDTH,
            0,
        ],
        color=LINES,
        linewidth=1.35,
        alpha=0.92,
        zorder=20,
    )

    halfway_x = PITCH_LENGTH / 2
    centre_y = PITCH_WIDTH / 2

    axis.plot(
        [halfway_x, halfway_x],
        [0, PITCH_WIDTH],
        color=LINES,
        linewidth=1.05,
        alpha=0.90,
        zorder=20,
    )

    centre_circle = plt.Circle(
        (
            halfway_x,
            centre_y,
        ),
        9.15,
        fill=False,
        color=LINES,
        linewidth=1.05,
        alpha=0.90,
        zorder=20,
    )

    axis.add_patch(
        centre_circle
    )

    axis.scatter(
        [halfway_x],
        [centre_y],
        s=8,
        color=LINES,
        alpha=0.95,
        zorder=21,
    )

    penalty_area_length = 16.5
    penalty_area_width = 40.32
    penalty_area_bottom = (
        PITCH_WIDTH
        - penalty_area_width
    ) / 2
    penalty_area_top = (
        PITCH_WIDTH
        + penalty_area_width
    ) / 2

    six_yard_length = 5.5
    six_yard_width = 18.32
    six_yard_bottom = (
        PITCH_WIDTH
        - six_yard_width
    ) / 2
    six_yard_top = (
        PITCH_WIDTH
        + six_yard_width
    ) / 2

    # Left penalty area.
    axis.plot(
        [
            0,
            penalty_area_length,
            penalty_area_length,
            0,
        ],
        [
            penalty_area_bottom,
            penalty_area_bottom,
            penalty_area_top,
            penalty_area_top,
        ],
        color=LINES,
        linewidth=1.0,
        alpha=0.90,
        zorder=20,
    )

    # Right penalty area.
    axis.plot(
        [
            PITCH_LENGTH,
            PITCH_LENGTH - penalty_area_length,
            PITCH_LENGTH - penalty_area_length,
            PITCH_LENGTH,
        ],
        [
            penalty_area_bottom,
            penalty_area_bottom,
            penalty_area_top,
            penalty_area_top,
        ],
        color=LINES,
        linewidth=1.0,
        alpha=0.90,
        zorder=20,
    )

    # Six-yard boxes.
    axis.plot(
        [
            0,
            six_yard_length,
            six_yard_length,
            0,
        ],
        [
            six_yard_bottom,
            six_yard_bottom,
            six_yard_top,
            six_yard_top,
        ],
        color=LINES,
        linewidth=1.0,
        alpha=0.90,
        zorder=20,
    )

    axis.plot(
        [
            PITCH_LENGTH,
            PITCH_LENGTH - six_yard_length,
            PITCH_LENGTH - six_yard_length,
            PITCH_LENGTH,
        ],
        [
            six_yard_bottom,
            six_yard_bottom,
            six_yard_top,
            six_yard_top,
        ],
        color=LINES,
        linewidth=1.0,
        alpha=0.90,
        zorder=20,
    )

    penalty_spot_distance = 11.0

    axis.scatter(
        [
            penalty_spot_distance,
            PITCH_LENGTH - penalty_spot_distance,
        ],
        [
            centre_y,
            centre_y,
        ],
        s=8,
        color=LINES,
        alpha=0.95,
        zorder=21,
    )

    # Goals.
    goal_width = 7.32
    goal_bottom = (
        PITCH_WIDTH
        - goal_width
    ) / 2
    goal_top = (
        PITCH_WIDTH
        + goal_width
    ) / 2
    goal_depth = 1.8

    axis.plot(
        [
            -goal_depth,
            0,
            0,
            -goal_depth,
            -goal_depth,
        ],
        [
            goal_bottom,
            goal_bottom,
            goal_top,
            goal_top,
            goal_bottom,
        ],
        color=LINES,
        linewidth=1.0,
        alpha=0.90,
        zorder=20,
    )

    axis.plot(
        [
            PITCH_LENGTH + goal_depth,
            PITCH_LENGTH,
            PITCH_LENGTH,
            PITCH_LENGTH + goal_depth,
            PITCH_LENGTH + goal_depth,
        ],
        [
            goal_bottom,
            goal_bottom,
            goal_top,
            goal_top,
            goal_bottom,
        ],
        color=LINES,
        linewidth=1.0,
        alpha=0.90,
        zorder=20,
    )

    axis.set_xlim(
        -3.0,
        PITCH_LENGTH + 3.0,
    )

    axis.set_ylim(
        -1.0,
        PITCH_WIDTH + 1.0,
    )

    # Equal scale gives the real 105:68 pitch ratio.
    axis.set_aspect(
        "equal",
        adjustable="box",
    )

    axis.set_xticks([])
    axis.set_yticks([])

    for spine in axis.spines.values():
        spine.set_visible(False)


def add_heatmap(
    axis: plt.Axes,
    rgba: np.ndarray,
    *,
    zorder: int = 5,
) -> None:
    axis.imshow(
        rgba,
        origin="lower",
        extent=(
            0,
            PITCH_LENGTH,
            0,
            PITCH_WIDTH,
        ),
        interpolation="bicubic",
        zorder=zorder,
    )


def add_profile_footer(
    axis: plt.Axes,
    row: pd.Series,
    color: str,
) -> None:
    text = (
        f"{int(row['matches_with_heatmap'])} matches  |  "
        f"{int(row['heatmap_point_count'])} points  |  "
        f"Mean ({row['weighted_mean_x']:.1f}, "
        f"{row['weighted_mean_y']:.1f})  |  "
        f"Entropy {row['heatmap_entropy']:.3f}"
    )

    axis.text(
        0.5,
        -0.105,
        text,
        transform=axis.transAxes,
        ha="center",
        va="top",
        fontsize=8.5,
        color=TEXT_MUTED,
    )

    mean_x = pitch_x(
        row["weighted_mean_x"]
    )
    mean_y = pitch_y(
        row["weighted_mean_y"]
    )

    axis.scatter(
        [mean_x],
        [mean_y],
        s=82,
        facecolor=color,
        edgecolor="#FFFFFF",
        linewidth=1.25,
        zorder=25,
    )


def draw_single(
    row: pd.Series,
    grid: np.ndarray,
    output_path: Path,
    color: str = TARGET_COLOR,
) -> None:
    figure = plt.figure(
        figsize=(15.5, 9),
        dpi=180,
        facecolor=BACKGROUND,
    )

    axis = figure.add_axes(
        [0.065, 0.15, 0.87, 0.70]
    )

    draw_pitch(axis)

    rgba = colorize_grid(
        grid,
        color,
        floor_ratio=0.18,
        gamma=1.80,
        max_alpha=0.82,
    )

    add_heatmap(
        axis,
        rgba,
    )

    figure.text(
        0.065,
        0.94,
        clean_text(
            row["player_name"]
        ).upper(),
        fontsize=28,
        fontweight="bold",
        color=TEXT,
    )

    figure.text(
        0.065,
        0.902,
        "TOURNAMENT HEATMAP PROFILE",
        fontsize=14,
        fontweight="bold",
        color=color,
    )

    add_profile_footer(
        axis,
        row,
        color,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    figure.savefig(
        output_path,
        dpi=180,
        facecolor=figure.get_facecolor(),
        bbox_inches=None,
    )

    plt.close(figure)


def draw_compare(
    target_row: pd.Series,
    target_grid: np.ndarray,
    candidate_row: pd.Series,
    candidate_grid: np.ndarray,
    output_path: Path,
) -> None:
    figure = plt.figure(
        figsize=(19, 8.4),
        dpi=180,
        facecolor=BACKGROUND,
    )

    axes = [
        figure.add_axes(
            [0.035, 0.16, 0.455, 0.68]
        ),
        figure.add_axes(
            [0.510, 0.16, 0.455, 0.68]
        ),
    ]

    rows = [
        target_row,
        candidate_row,
    ]

    grids = [
        target_grid,
        candidate_grid,
    ]

    colors = [
        TARGET_COLOR,
        CANDIDATE_COLOR,
    ]

    labels = [
        "TARGET",
        "ALTERNATIVE",
    ]

    for axis, row, grid, color, label in zip(
            axes,
            rows,
            grids,
            colors,
            labels,
    ):
        draw_pitch(axis)

        rgba = colorize_grid(
            grid,
            color,
            shared_peak=None,
            floor_ratio=0.12,
            gamma=1.45,
            max_alpha=0.82,
        )

        add_heatmap(
            axis,
            rgba,
        )

        axis.set_title(
            (
                f"{label}\n"
                f"{clean_text(row['player_name'])}"
            ),
            fontsize=14,
            fontweight="bold",
            color=color,
            pad=12,
        )

        add_profile_footer(
            axis,
            row,
            color,
        )

    figure.text(
        0.04,
        0.95,
        "HEATMAP PROFILE COMPARISON",
        fontsize=25,
        fontweight="bold",
        color=TEXT,
    )

    figure.text(
        0.04,
        0.91,
        (
            f"{clean_text(target_row['player_name'])} vs "
            f"{clean_text(candidate_row['player_name'])}"
        ),
        fontsize=13,
        color=TEXT_SOFT,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    figure.savefig(
        output_path,
        dpi=180,
        facecolor=figure.get_facecolor(),
        bbox_inches=None,
    )

    plt.close(figure)


def draw_overlay(
    target_row: pd.Series,
    target_grid: np.ndarray,
    candidate_row: pd.Series,
    candidate_grid: np.ndarray,
    output_path: Path,
) -> None:
    figure = plt.figure(
        figsize=(15.5, 9),
        dpi=180,
        facecolor=BACKGROUND,
    )

    axis = figure.add_axes(
        [0.065, 0.15, 0.87, 0.70]
    )

    draw_pitch(axis)

    shared_peak = max(
        float(target_grid.max()),
        float(candidate_grid.max()),
    )

    target_intensity = normalize_for_display(
        target_grid,
        shared_peak=None,
        floor_ratio=0.12,
        gamma=1.45,
    )

    candidate_intensity = normalize_for_display(
        candidate_grid,
        shared_peak=None,
        floor_ratio=0.12,
        gamma=1.45,
    )

    target_rgba = colorize_grid(
        target_grid,
        TARGET_COLOR,
        shared_peak=None,
        floor_ratio=0.12,
        gamma=1.45,
        max_alpha=0.68,
    )

    candidate_rgba = colorize_grid(
        candidate_grid,
        CANDIDATE_COLOR,
        shared_peak=None,
        floor_ratio=0.12,
        gamma=1.45,
        max_alpha=0.68,
    )

    overlap = np.sqrt(
        target_intensity
        * candidate_intensity
    )

    overlap_rgba = np.zeros(
        (*overlap.shape, 4),
        dtype=np.float64,
    )

    overlap_rgba[..., :3] = (
        1.0,
        0.98,
        0.72,
    )

    overlap_rgba[..., 3] = (
            np.power(overlap, 1.40)
            * 0.72
    )

    add_heatmap(
        axis,
        target_rgba,
        zorder=4,
    )

    add_heatmap(
        axis,
        candidate_rgba,
        zorder=5,
    )

    add_heatmap(
        axis,
        overlap_rgba,
        zorder=6,
    )

    target_mean_x = pitch_x(
        target_row["weighted_mean_x"]
    )
    target_mean_y = pitch_y(
        target_row["weighted_mean_y"]
    )

    candidate_mean_x = pitch_x(
        candidate_row["weighted_mean_x"]
    )
    candidate_mean_y = pitch_y(
        candidate_row["weighted_mean_y"]
    )

    axis.scatter(
        [target_mean_x],
        [target_mean_y],
        s=100,
        facecolor=TARGET_COLOR,
        edgecolor="#FFFFFF",
        linewidth=1.4,
        zorder=25,
        label=clean_text(
            target_row["player_name"]
        ),
    )

    axis.scatter(
        [candidate_mean_x],
        [candidate_mean_y],
        s=100,
        facecolor=CANDIDATE_COLOR,
        edgecolor="#FFFFFF",
        linewidth=1.4,
        zorder=25,
        label=clean_text(
            candidate_row["player_name"]
        ),
    )

    legend = axis.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, -0.145),
        ncol=2,
        frameon=False,
        fontsize=10,
    )

    for text_item in legend.get_texts():
        text_item.set_color(
            TEXT_SOFT
        )

    figure.text(
        0.065,
        0.94,
        "HEATMAP OCCUPATION OVERLAY",
        fontsize=26,
        fontweight="bold",
        color=TEXT,
    )

    figure.text(
        0.065,
        0.902,
        (
            f"{clean_text(target_row['player_name'])} vs "
            f"{clean_text(candidate_row['player_name'])}"
        ),
        fontsize=13,
        color=TEXT_SOFT,
    )

    figure.text(
        0.065,
        0.04,
        (
            "Yellow: target occupation  |  "
            "Green: alternative occupation  |  "
            "Bright overlap: shared high-density zones"
        ),
        fontsize=10,
        color=TEXT_MUTED,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    figure.savefig(
        output_path,
        dpi=180,
        facecolor=figure.get_facecolor(),
        bbox_inches=None,
    )

    plt.close(figure)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Visualize player tournament heatmap profiles."
        )
    )

    parser.add_argument(
        "--player",
        required=True,
    )

    parser.add_argument(
        "--candidate",
        default=None,
    )

    parser.add_argument(
        "--mode",
        choices=[
            "single",
            "compare",
            "overlay",
        ],
        default="single",
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
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    profiles = load_profiles(
        args.profiles
    )

    grids = np.load(
        args.grids
    )

    target_row = resolve_player(
        profiles,
        args.player,
    )

    target_grid = load_grid(
        grids,
        int(target_row["player_id"]),
    )

    if args.mode == "single":
        output_path = (
            args.output_dir
            / "single"
            / (
                f"{slugify(args.player)}_"
                "tournament_heatmap.png"
            )
        )

        draw_single(
            target_row,
            target_grid,
            output_path,
        )

    else:
        if not args.candidate:
            raise ValueError(
                "--candidate is required for "
                f"mode={args.mode}"
            )

        candidate_row = resolve_player(
            profiles,
            args.candidate,
        )

        candidate_grid = load_grid(
            grids,
            int(candidate_row["player_id"]),
        )

        output_path = (
            args.output_dir
            / args.mode
            / (
                f"{slugify(args.player)}_vs_"
                f"{slugify(args.candidate)}_"
                f"{args.mode}.png"
            )
        )

        if args.mode == "compare":
            draw_compare(
                target_row,
                target_grid,
                candidate_row,
                candidate_grid,
                output_path,
            )

        elif args.mode == "overlay":
            draw_overlay(
                target_row,
                target_grid,
                candidate_row,
                candidate_grid,
                output_path,
            )

    print(
        "Heatmap visualization created:"
    )
    print(output_path)


if __name__ == "__main__":
    main()
