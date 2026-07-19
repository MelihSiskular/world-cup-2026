# -*- coding: utf-8 -*-
"""
Heatmap overlay helpers for create_transfer_dashboard.py.

This module intentionally changes only the tactical mini-pitch rendering.
It uses the existing player_heatmap_grids.npz archive.

Target:
    yellow heatmap

Candidate:
    green heatmap

Shared high-density occupation:
    pale bright overlay
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


PITCH_BACKGROUND = "#06110D"
PITCH_STRIPE = "#173126"
PITCH_LINE = "#D6E5DE"
GRID_LINE = "#79A88C"

TARGET_HEATMAP_COLOR = "#F0C75A"
CANDIDATE_HEATMAP_COLOR = "#55D991"
OVERLAP_COLOR = "#FFF8B8"

WHITE = "#FFFFFF"
DARK_TEXT = "#06110D"
MUTED_TEXT = "#D8EEE2"


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def load_heatmap_grid_archive(
    path: Path,
) -> np.lib.npyio.NpzFile | None:
    if not path.exists():
        print(f"[HEATMAP] Grid archive not found: {path}")
        return None

    return np.load(path, allow_pickle=False)


def get_player_grid(
    archive: np.lib.npyio.NpzFile | None,
    player_id: Any,
) -> np.ndarray | None:
    if archive is None:
        return None

    numeric_id = safe_float(player_id, default=np.nan)

    if np.isnan(numeric_id):
        return None

    key = str(int(numeric_id))

    if key not in archive.files:
        return None

    grid = np.asarray(archive[key], dtype=np.float64)

    if grid.ndim != 2 or grid.size == 0:
        return None

    grid = np.nan_to_num(
        grid,
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    )

    total = grid.sum()

    if total <= 0:
        return None

    return grid / total


def hex_to_rgb(color: str) -> tuple[int, int, int]:
    value = color.lstrip("#")
    return (
        int(value[0:2], 16),
        int(value[2:4], 16),
        int(value[4:6], 16),
    )


def normalize_heatmap_for_display(
    grid: np.ndarray,
    *,
    shared_peak: float | None = None,
    floor_ratio: float = 0.08,
    gamma: float = 1.80,
) -> np.ndarray:
    peak = float(shared_peak) if shared_peak is not None else float(grid.max())

    if peak <= 0:
        return np.zeros_like(grid, dtype=np.float64)

    normalized = np.clip(grid / peak, 0.0, 1.0)

    adjusted = np.clip(
        (normalized - floor_ratio)
        / max(1.0 - floor_ratio, 1e-9),
        0.0,
        1.0,
    )

    return np.power(adjusted, gamma)


def build_rgba_heatmap(
    intensity: np.ndarray,
    color: str,
    *,
    max_alpha: float,
    highlight_color: str = "#FFF4B5",
) -> np.ndarray:
    base = np.asarray(hex_to_rgb(color), dtype=np.float64)
    highlight = np.asarray(hex_to_rgb(highlight_color), dtype=np.float64)

    rgba = np.zeros(
        (intensity.shape[0], intensity.shape[1], 4),
        dtype=np.uint8,
    )

    blend = np.power(intensity, 1.35)[..., None]
    rgb = base * (1.0 - blend) + highlight * blend

    rgba[..., :3] = np.clip(rgb, 0, 255).astype(np.uint8)
    rgba[..., 3] = np.clip(
        intensity * max_alpha * 255,
        0,
        255,
    ).astype(np.uint8)

    return rgba


def resize_grid_rgba(
    rgba: np.ndarray,
    width: int,
    height: int,
) -> Image.Image:
    flipped = np.flipud(rgba).copy()
    image = Image.fromarray(flipped, mode="RGBA")

    return image.resize(
        (width, height),
        Image.Resampling.BICUBIC,
    )


def draw_pitch_base(
    size: tuple[int, int],
    *,
    radius: int = 18,
) -> Image.Image:
    width, height = size

    pitch = Image.new("RGBA", size, (0, 0, 0, 0))
    background = Image.new("RGBA", size, PITCH_BACKGROUND)

    mask = Image.new("L", size, 0)
    mask_draw = ImageDraw.Draw(mask)

    mask_draw.rounded_rectangle(
        (0, 0, width - 1, height - 1),
        radius=radius,
        fill=255,
    )

    pitch.paste(background, (0, 0), mask)
    draw = ImageDraw.Draw(pitch, "RGBA")

    stripe_count = 12
    stripe_width = width / stripe_count

    for index in range(stripe_count):
        if index % 2 == 0:
            draw.rectangle(
                (
                    int(index * stripe_width),
                    0,
                    int((index + 1) * stripe_width),
                    height,
                ),
                fill=(*hex_to_rgb(PITCH_STRIPE), 58),
            )

    return pitch


def draw_pitch_lines(
    pitch: Image.Image,
    *,
    margin: int = 14,
) -> None:
    draw = ImageDraw.Draw(pitch, "RGBA")
    width, height = pitch.size

    x1 = margin
    y1 = margin
    x2 = width - margin - 1
    y2 = height - margin - 1

    line = (*hex_to_rgb(PITCH_LINE), 232)
    grid = (*hex_to_rgb(GRID_LINE), 120)

    draw.rectangle((x1, y1, x2, y2), outline=line, width=2)

    middle_x = (x1 + x2) // 2
    centre_y = (y1 + y2) // 2

    draw.line((middle_x, y1, middle_x, y2), fill=line, width=2)

    centre_radius = int(min(x2 - x1, y2 - y1) * 0.12)

    draw.ellipse(
        (
            middle_x - centre_radius,
            centre_y - centre_radius,
            middle_x + centre_radius,
            centre_y + centre_radius,
        ),
        outline=line,
        width=2,
    )

    draw.ellipse(
        (
            middle_x - 3,
            centre_y - 3,
            middle_x + 3,
            centre_y + 3,
        ),
        fill=line,
    )

    pitch_width = x2 - x1
    pitch_height = y2 - y1

    penalty_width = int(pitch_width * 16.5 / 105.0)
    penalty_height = int(pitch_height * 40.32 / 68.0)
    six_width = int(pitch_width * 5.5 / 105.0)
    six_height = int(pitch_height * 18.32 / 68.0)

    draw.rectangle(
        (
            x1,
            centre_y - penalty_height // 2,
            x1 + penalty_width,
            centre_y + penalty_height // 2,
        ),
        outline=line,
        width=2,
    )

    draw.rectangle(
        (
            x2 - penalty_width,
            centre_y - penalty_height // 2,
            x2,
            centre_y + penalty_height // 2,
        ),
        outline=line,
        width=2,
    )

    draw.rectangle(
        (
            x1,
            centre_y - six_height // 2,
            x1 + six_width,
            centre_y + six_height // 2,
        ),
        outline=line,
        width=2,
    )

    draw.rectangle(
        (
            x2 - six_width,
            centre_y - six_height // 2,
            x2,
            centre_y + six_height // 2,
        ),
        outline=line,
        width=2,
    )

    penalty_spot_offset = int(pitch_width * 11.0 / 105.0)

    for penalty_x in (
        x1 + penalty_spot_offset,
        x2 - penalty_spot_offset,
    ):
        draw.ellipse(
            (
                penalty_x - 2,
                centre_y - 2,
                penalty_x + 2,
                centre_y + 2,
            ),
            fill=line,
        )

    for fraction in (1 / 3, 2 / 3):
        tactical_x = x1 + int(pitch_width * fraction)
        draw.line(
            (tactical_x, y1, tactical_x, y2),
            fill=grid,
            width=1,
        )

    for fraction in (0.2, 0.4, 0.6, 0.8):
        tactical_y = y1 + int(pitch_height * fraction)
        draw.line(
            (x1, tactical_y, x2, tactical_y),
            fill=grid,
            width=1,
        )


def draw_mean_marker(
    pitch: Image.Image,
    *,
    mean_x: float,
    mean_y: float,
    color: str,
    letter: str,
    font_obj: ImageFont.FreeTypeFont,
    margin: int = 14,
) -> None:
    draw = ImageDraw.Draw(pitch)
    width, height = pitch.size

    x1 = margin
    y1 = margin
    x2 = width - margin - 1
    y2 = height - margin - 1

    plot_x = x1 + int(
        (x2 - x1)
        * np.clip(mean_x, 0, 100)
        / 100
    )

    plot_y = y2 - int(
        (y2 - y1)
        * np.clip(mean_y, 0, 100)
        / 100
    )

    radius = 11

    draw.ellipse(
        (
            plot_x - radius,
            plot_y - radius,
            plot_x + radius,
            plot_y + radius,
        ),
        fill=color,
        outline=WHITE,
        width=2,
    )

    bbox = draw.textbbox((0, 0), letter, font=font_obj)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    draw.text(
        (
            plot_x - text_width / 2,
            plot_y - text_height / 2 - 1,
        ),
        letter,
        font=font_obj,
        fill=DARK_TEXT,
    )


def draw_metric_badge(
    pitch: Image.Image,
    *,
    x: int,
    y: int,
    label: str,
    value: str,
    accent: str,
    label_font: ImageFont.FreeTypeFont,
    value_font: ImageFont.FreeTypeFont,
) -> None:
    draw = ImageDraw.Draw(pitch, "RGBA")

    label_box = draw.textbbox((0, 0), label, font=label_font)
    value_box = draw.textbbox((0, 0), value, font=value_font)

    badge_width = max(
        label_box[2] - label_box[0],
        value_box[2] - value_box[0],
    ) + 22

    badge_height = 45

    draw.rounded_rectangle(
        (
            x,
            y,
            x + badge_width,
            y + badge_height,
        ),
        radius=10,
        fill=(4, 20, 13, 190),
        outline=(*hex_to_rgb(accent), 210),
        width=1,
    )

    draw.text(
        (x + 11, y + 5),
        label,
        font=label_font,
        fill=MUTED_TEXT,
    )

    draw.text(
        (x + 11, y + 21),
        value,
        font=value_font,
        fill=accent,
    )


def create_heatmap_pitch(
    *,
    width: int,
    height: int,
    target: pd.Series,
    candidate: pd.Series,
    archive: np.lib.npyio.NpzFile | None,
    target_color: str,
    candidate_color: str,
    font_path: str,
) -> Image.Image:
    pitch = draw_pitch_base((width, height))

    target_grid = get_player_grid(
        archive,
        target.get("player_id"),
    )

    candidate_grid = get_player_grid(
        archive,
        candidate.get("player_id"),
    )

    if target_grid is not None and candidate_grid is not None:
        shared_peak = max(
            float(target_grid.max()),
            float(candidate_grid.max()),
        )

        target_intensity = normalize_heatmap_for_display(
            target_grid,
            shared_peak=shared_peak,
            floor_ratio=0.47,
            gamma=1.80,
        )

        candidate_intensity = normalize_heatmap_for_display(
            candidate_grid,
            shared_peak=shared_peak,
            floor_ratio=0.47,
            gamma=1.80,
        )

        target_rgba = build_rgba_heatmap(
            target_intensity,
            target_color,
            max_alpha=0.62,
        )

        candidate_rgba = build_rgba_heatmap(
            candidate_intensity,
            candidate_color,
            max_alpha=0.62,
        )

        overlap = np.minimum(
            target_intensity,
            candidate_intensity,
        )

        overlap_rgba = np.zeros(
            (overlap.shape[0], overlap.shape[1], 4),
            dtype=np.uint8,
        )

        overlap_rgba[..., :3] = np.asarray(
            hex_to_rgb(OVERLAP_COLOR),
            dtype=np.uint8,
        )

        overlap_rgba[..., 3] = np.clip(
            np.power(overlap, 1.40)
            * 0.72
            * 255,
            0,
            255,
        ).astype(np.uint8)

        pitch.alpha_composite(
            resize_grid_rgba(
                target_rgba,
                width,
                height,
            )
        )

        pitch.alpha_composite(
            resize_grid_rgba(
                candidate_rgba,
                width,
                height,
            )
        )

        pitch.alpha_composite(
            resize_grid_rgba(
                overlap_rgba,
                width,
                height,
            )
        )

    draw_pitch_lines(pitch)

    marker_font = ImageFont.truetype(
        font_path,
        size=11,
    )

    target_mean_x = safe_float(
        target.get(
            "heatmap_weighted_mean_x",
            target.get("weighted_mean_x", 55),
        ),
        default=55,
    )

    target_mean_y = safe_float(
        target.get(
            "heatmap_weighted_mean_y",
            target.get("weighted_mean_y", 50),
        ),
        default=50,
    )

    candidate_mean_x = safe_float(
        candidate.get(
            "heatmap_weighted_mean_x",
            candidate.get("weighted_mean_x", 55),
        ),
        default=55,
    )

    candidate_mean_y = safe_float(
        candidate.get(
            "heatmap_weighted_mean_y",
            candidate.get("weighted_mean_y", 50),
        ),
        default=50,
    )

    draw_mean_marker(
        pitch,
        mean_x=target_mean_x,
        mean_y=target_mean_y,
        color=target_color,
        letter="T",
        font_obj=marker_font,
    )

    draw_mean_marker(
        pitch,
        mean_x=candidate_mean_x,
        mean_y=candidate_mean_y,
        color=candidate_color,
        letter="A",
        font_obj=marker_font,
    )

    label_font = ImageFont.truetype(
        font_path,
        size=8,
    )

    value_font = ImageFont.truetype(
        font_path,
        size=11,
    )

    has_heatmap = bool(
        candidate.get(
            "has_heatmap_similarity",
            False,
        )
    )

    heatmap_score = candidate.get(
        "heatmap_similarity_score_pct"
    )

    overlap_score = candidate.get(
        "occupation_overlap_pct"
    )

    heatmap_text = (
        f"{float(heatmap_score):.1f}%"
        if has_heatmap and pd.notna(heatmap_score)
        else "N/A"
    )

    overlap_text = (
        f"{float(overlap_score):.1f}%"
        if has_heatmap and pd.notna(overlap_score)
        else "N/A"
    )

    draw_metric_badge(
        pitch,
        x=22,
        y=21,
        label="HEATMAP SIM",
        value=heatmap_text,
        accent=target_color,
        label_font=label_font,
        value_font=value_font,
    )

    draw_metric_badge(
        pitch,
        x=22,
        y=72,
        label="SHARED ZONES",
        value=overlap_text,
        accent=candidate_color,
        label_font=label_font,
        value_font=value_font,
    )

    return pitch


def draw_heatmap_mini_pitch(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    target: pd.Series,
    candidate: pd.Series,
    target_color: str,
    candidate_color: str,
    heatmap_archive: np.lib.npyio.NpzFile | None,
    font_path: str,
) -> None:
    x1, y1, x2, y2 = box

    width = max(1, x2 - x1)
    height = max(1, y2 - y1)

    pitch = create_heatmap_pitch(
        width=width,
        height=height,
        target=target,
        candidate=candidate,
        archive=heatmap_archive,
        target_color=target_color,
        candidate_color=candidate_color,
        font_path=font_path,
    )

    canvas.alpha_composite(
        pitch,
        (x1, y1),
    )
