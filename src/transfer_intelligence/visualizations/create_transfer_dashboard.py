# -*- coding: utf-8 -*-
"""
python -m src.transfer_intelligence.visualizations.create_transfer_dashboard \
    --player "Michael Olise" \
    --mode value
"""

from __future__ import annotations

import argparse
import io
import re
import unicodedata
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from scipy.stats import norm
from src.assets.asset_manager import (
    load_country_flag,
    load_player_image,
    load_team_logo,
)
from src.transfer_intelligence.visualizations.heatmap_dashboard_helpers import (
    draw_heatmap_mini_pitch,
    load_heatmap_grid_archive,
)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

DEFAULT_FEATURES = Path(
    "data/processed/transfer_intelligence/"
    "transfer_feature_table.csv"
)

DEFAULT_HEATMAP_GRIDS = Path(
    "data/processed/player_heatmaps/"
    "player_heatmap_grids.npz"
)

DEFAULT_RESULTS_DIR = Path(
    "data/processed/transfer_intelligence/"
    "replacement_results"
)

DEFAULT_OUTPUT_DIR = Path(
    "docs/images/transfer_intelligence/"
    "premium_dashboards"
)

DEFAULT_SPATIAL_PROFILES = Path(
    "data/processed/player_positioning/"
    "player_spatial_profiles.csv"
)

DEFAULT_ARCHETYPE_PROFILES = Path(
    "data/processed/player_archetypes/"
    "player_archetypes.csv"
)


# ---------------------------------------------------------------------------
# Design system
# ---------------------------------------------------------------------------

CANVAS_WIDTH = 2400
CANVAS_HEIGHT = 1840

BACKGROUND = "#06110D"
PANEL = "#0B1B15"
PANEL_ALT = "#10251C"
PANEL_LIGHT = "#153127"
BORDER = "#294A3B"

TEXT = "#F4FFF8"
TEXT_SOFT = "#ADC2B8"
TEXT_MUTED = "#789486"

GRID = "#1D392D"
WHITE = "#FFFFFF"

MODE_CONFIG = {
    "immediate": {
        "score_column": "immediate_score",
        "rank_column": "immediate_rank",
        "title": "READY-NOW REPLACEMENTS",
        "subtitle": (
            "First-team options balancing tactical fit, "
            "tournament performance and evidence reliability."
        ),
        "accent": "#54D6A4",
        "zone": "READY-NOW VALUE ZONE",
    },
    "development": {
        "score_column": "development_score",
        "rank_column": "development_rank",
        "title": "DEVELOPMENT PROSPECTS",
        "subtitle": (
            "Young profiles assessed through long-term upside, "
            "similarity and recruitment cost."
        ),
        "accent": "#72C7FF",
        "zone": "HIGH-UPSIDE ZONE",
    },
    "value": {
        "score_column": "value_score",
        "rank_column": "value_rank",
        "title": "BEST VALUE ALTERNATIVES",
        "subtitle": (
            "Candidates balancing role suitability, "
            "performance evidence and market cost."
        ),
        "accent": "#F0C75A",
        "zone": "MARKET OPPORTUNITY ZONE",
    },
    "short_term": {
        "score_column": "short_term_score",
        "rank_column": "short_term_rank",
        "title": "SHORT-TERM SOLUTIONS",
        "subtitle": (
            "Experienced profiles offering reliable and "
            "immediate squad coverage."
        ),
        "accent": "#FF9A78",
        "zone": "LOW-RISK VALUE ZONE",
    },
}



ROLE_INTELLIGENCE = {
    "Advanced Central Playmaker": {
        "function": (
            "Creates and progresses possession from advanced central zones, "
            "connecting midfield with the final attacking line."
        ),
        "behaviours": [
            "Receives between midfield and attack",
            "Operates centrally or inside the half-spaces",
            "Creates chances through progressive actions",
            "Maintains an advanced positional profile",
        ],
        "requirements": [
            "Creativity",
            "Progression",
            "Passing Volume",
            "Ball Security",
        ],
    },
    "Central Tempo Controller": {
        "function": (
            "Controls the speed, direction and circulation of possession from "
            "stable central build-up positions."
        ),
        "behaviours": [
            "Offers consistently during build-up",
            "Connects defensive and attacking phases",
            "Circulates possession under pressure",
            "Maintains central positional stability",
        ],
        "requirements": [
            "Passing Volume",
            "Progression",
            "Ball Security",
            "Press Resistance",
        ],
    },
    "Holding Ball-Winner": {
        "function": (
            "Protects central areas, regains possession and provides a stable "
            "defensive platform ahead of the back line."
        ),
        "behaviours": [
            "Screens the defensive line",
            "Contests central duels and second balls",
            "Supports safe build-up circulation",
            "Maintains disciplined central positioning",
        ],
        "requirements": [
            "Defensive Work",
            "Ball Recoveries",
            "Duel Strength",
            "Ball Security",
        ],
    },
    "Possession-Secure Poacher": {
        "function": (
            "Occupies high-value finishing areas while retaining possession "
            "securely during short attacking combinations."
        ),
        "behaviours": [
            "Attacks central penalty-area spaces",
            "Offers short secure combinations",
            "Preserves advanced central positioning",
            "Prioritises finishing opportunities",
        ],
        "requirements": [
            "Finishing",
            "Scoring Threat",
            "Ball Security",
            "Movement",
        ],
    },
}

RADAR_DIMENSIONS = [
    (
        "Creativity",
        [
            "archetype_score_creativity",
        ],
    ),
    (
        "Progression",
        [
            "archetype_score_progression",
        ],
    ),
    (
        "Passing Volume",
        [
            "archetype_score_passing_volume",
        ],
    ),
    (
        "Ball Security",
        [
            "archetype_score_ball_security",
        ],
    ),
    (
        "Dribbling",
        [
            "archetype_score_dribbling",
        ],
    ),
    (
        "Scoring Threat",
        [
            "archetype_score_scoring_threat",
        ],
    ),
    (
        "Defensive Work",
        [
            "archetype_score_defensive_work",
        ],
    ),
    (
        "Wide Creation",
        [
            "archetype_score_wide_creation",
        ],
    ),
]
SPATIAL_ALIASES = {
    "mean_x": ["mean_x", "weighted_mean_x", "avg_x", "average_x"],
    "mean_y": ["mean_y", "weighted_mean_y", "avg_y", "average_y"],
    "spatial_spread": [
        "spatial_spread", "weighted_spatial_spread", "spread", "avg_spread"
    ],
    "lateral_profile": [
        "lateral_profile", "horizontal_profile", "lateral_zone"
    ],
    "vertical_profile": [
        "vertical_profile", "vertical_zone", "pitch_depth_profile"
    ],
    "mobility_profile": [
        "mobility_profile", "mobility", "movement_profile"
    ],
    "spatial_role": ["spatial_role", "spatial_zone", "positioning_role"],
}

# ---------------------------------------------------------------------------
# Text and formatting
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(text))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")

    return (
        re.sub(r"[^a-zA-Z0-9]+", "_", ascii_text)
        .strip("_")
        .lower()
    )


def clean_text(value: Any) -> str:
    if value is None or pd.isna(value):
        return "-"

    text = unicodedata.normalize("NFKC", str(value))

    replacements = {
        "€": "EUR ",
        "·": " | ",
        "–": "-",
        "—": "-",
        "’": "'",
        "“": '"',
        "”": '"',
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return "".join(
        character
        for character in text
        if ord(character) >= 32
    ).strip()


def format_market_value(value: Any) -> str:
    if value is None or pd.isna(value):
        return "-"

    number = float(value)

    if number >= 1_000_000:
        return f"EUR {number / 1_000_000:.0f}M"

    if number >= 1_000:
        return f"EUR {number / 1_000:.0f}K"

    return f"EUR {number:.0f}"


def format_age(value: Any) -> str:
    if value is None or pd.isna(value):
        return "-"

    return f"{float(value):.1f}"


def format_score(value: Any) -> str:
    if value is None or pd.isna(value):
        return "-"

    return f"{float(value):.1f}"


# ---------------------------------------------------------------------------
# Fonts
# ---------------------------------------------------------------------------

def system_font_path(bold: bool = False) -> str:
    properties = font_manager.FontProperties(
        family="DejaVu Sans",
        weight="bold" if bold else "normal",
    )

    return font_manager.findfont(
        properties,
        fallback_to_default=True,
    )


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        system_font_path(bold),
        size=size,
    )


def fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    start_size: int,
    minimum_size: int,
    bold: bool = True,
) -> ImageFont.FreeTypeFont:
    for size in range(start_size, minimum_size - 1, -1):
        selected = font(size, bold=bold)
        bbox = draw.textbbox((0, 0), text, font=selected)

        if bbox[2] - bbox[0] <= max_width:
            return selected

    return font(minimum_size, bold=bold)

def wrap_text(
    draw,
    text,
    font_obj,
    max_width,
    max_lines=2,
):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = word if not current else f"{current} {word}"

        bbox = draw.textbbox(
            (0, 0),
            test,
            font=font_obj,
        )

        width = bbox[2] - bbox[0]

        if width <= max_width:
            current = test
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    lines = lines[:max_lines]

    if len(lines) == max_lines:
        last = lines[-1]

        while True:
            bbox = draw.textbbox(
                (0, 0),
                last + "...",
                font=font_obj,
            )

            width = bbox[2] - bbox[0]

            if width <= max_width:
                break

            last = last[:-1]

        lines[-1] = last + "..."

    return lines
def truncate_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    selected_font: ImageFont.FreeTypeFont,
    max_width: int,
) -> str:
    if draw.textbbox((0, 0), text, font=selected_font)[2] <= max_width:
        return text

    suffix = "..."

    while text:
        candidate = text[:-1] + suffix

        if draw.textbbox(
            (0, 0),
            candidate,
            font=selected_font,
        )[2] <= max_width:
            return candidate

        text = text[:-1]

    return suffix


def first_present_value(
    row: pd.Series,
    aliases: list[str],
):
    for column in aliases:
        if column not in row.index:
            continue
        value = row.get(column)
        if pd.notna(value):
            return value
    return np.nan

def z_score_to_percentile(
    value,
) -> float:
    if value is None or pd.isna(value):
        return np.nan

    z_score = float(value)

    percentile = norm.cdf(
        z_score
    ) * 100

    return float(
        np.clip(
            percentile,
            0,
            100,
        )
    )

def normalize_profile_value(value: Any) -> float:
    """Normalize percentile, 0-1, 0-10 or z-score values to 0-100."""
    if value is None or pd.isna(value):
        return np.nan

    number = float(value)

    if 0 <= number <= 1:
        return float(np.clip(number * 100, 0, 100))

    if -4 <= number < 0:
        return float(np.clip(50 + number * 15, 0, 100))

    if 1 < number <= 4:
        # Positive standardized values are much more likely than raw 1-4 scores.
        return float(np.clip(50 + number * 15, 0, 100))

    if 4 < number <= 10:
        return float(np.clip(number * 10, 0, 100))

    return float(np.clip(number, 0, 100))



def extract_radar_profile(
    row: pd.Series,
) -> tuple[list[str], list[float], list[str]]:
    labels: list[str] = []
    values: list[float] = []
    missing: list[str] = []

    for label, aliases in RADAR_DIMENSIONS:
        raw_value = first_present_value(
            row,
            aliases,
        )

        if raw_value is None or pd.isna(raw_value):
            labels.append(label)
            values.append(np.nan)
            missing.append(label)
            continue

        percentile = z_score_to_percentile(
            raw_value
        )

        labels.append(label)
        values.append(percentile)

    return labels, values, missing
def enrich_with_optional_profiles(
    dataframe: pd.DataFrame,
    path: Path,
    prefix: str,
) -> pd.DataFrame:
    """Merge an optional player profile table without overwriting core fields."""
    if not path.exists():
        return dataframe

    extra = pd.read_csv(path, low_memory=False)

    if "player_id" not in extra.columns:
        return dataframe

    extra = extra.copy()
    extra["player_id"] = pd.to_numeric(extra["player_id"], errors="coerce")
    extra = extra.dropna(subset=["player_id"]).drop_duplicates("player_id")

    rename_map = {
        column: f"{prefix}_{column}"
        for column in extra.columns
        if column != "player_id" and column in dataframe.columns
    }
    extra = extra.rename(columns=rename_map)

    merged = dataframe.merge(extra, on="player_id", how="left")

    for original, renamed in rename_map.items():
        if original in merged.columns:
            merged[original] = merged[original].combine_first(merged[renamed])
        else:
            merged[original] = merged[renamed]

    return merged.drop(columns=list(rename_map.values()), errors="ignore")


def canonical_spatial_value(
    row: pd.Series,
    field: str,
):
    return first_present_value(row, SPATIAL_ALIASES[field])


def role_intelligence_for(
    role_name: str,
) -> dict[str, Any]:
    if role_name in ROLE_INTELLIGENCE:
        return ROLE_INTELLIGENCE[role_name]

    lowered = role_name.casefold()

    if "tempo" in lowered or "controller" in lowered:
        return ROLE_INTELLIGENCE["Central Tempo Controller"]

    if "playmaker" in lowered or "creator" in lowered:
        return ROLE_INTELLIGENCE["Advanced Central Playmaker"]

    if "ball-winner" in lowered or "holding" in lowered:
        return ROLE_INTELLIGENCE["Holding Ball-Winner"]

    if "poacher" in lowered or "striker" in lowered:
        return ROLE_INTELLIGENCE["Possession-Secure Poacher"]

    return {
        "function": (
            "Combines a tournament statistical archetype with a distinct "
            "spatial profile to perform a repeatable tactical function."
        ),
        "behaviours": [
            "Operates in the role's dominant pitch zones",
            "Reflects the player's statistical archetype",
            "Maintains role-specific positional behaviour",
            "Supports the team's tactical structure",
        ],
        "requirements": [
            "Role Fit", "Tournament Quality", "Spatial Alignment", "Reliability"
        ],
    }


# ---------------------------------------------------------------------------
# Basic drawing utilities
# ---------------------------------------------------------------------------

def draw_panel(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    *,
    fill: str = PANEL,
    outline: str = BORDER,
    radius: int = 28,
    width: int = 2,
    shadow: bool = True,
) -> None:
    x1, y1, x2, y2 = box

    if shadow:
        shadow_layer = Image.new(
            "RGBA",
            canvas.size,
            (0, 0, 0, 0),
        )

        shadow_draw = ImageDraw.Draw(shadow_layer)

        shadow_draw.rounded_rectangle(
            (x1 + 9, y1 + 12, x2 + 9, y2 + 12),
            radius=radius,
            fill=(0, 0, 0, 95),
        )

        shadow_layer = shadow_layer.filter(
            ImageFilter.GaussianBlur(14)
        )

        canvas.alpha_composite(shadow_layer)

    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle(
        box,
        radius=radius,
        fill=fill,
        outline=outline,
        width=width,
    )
def circle_crop(
    image: Image.Image,
    size: int,
    border_color: str,
    border_width: int = 5,
    zoom: float = 1.16,
    vertical_offset: int = 0,
) -> Image.Image:
    image = image.convert("RGBA")

    # Fotoğrafı büyüt. Böylece görseldeki beyaz dış boşluk azalır.
    crop_size = int(size / zoom)

    image = ImageOps.fit(
        image,
        (crop_size, crop_size),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )

    # Büyütülen kırpılmış görseli tekrar hedef boyuta getir.
    image = image.resize(
        (size, size),
        Image.Resampling.LANCZOS,
    )

    # Dikey konumu gerektiğinde ayarlamak için.
    shifted = Image.new(
        "RGBA",
        (size, size),
        (0, 0, 0, 0),
    )

    shifted.alpha_composite(
        image,
        (0, vertical_offset),
    )

    # Tam daire maske.
    mask = Image.new(
        "L",
        (size, size),
        0,
    )

    mask_draw = ImageDraw.Draw(mask)

    mask_draw.ellipse(
        (0, 0, size - 1, size - 1),
        fill=255,
    )

    result = Image.new(
        "RGBA",
        (size, size),
        (0, 0, 0, 0),
    )

    result.paste(
        shifted,
        (0, 0),
        mask,
    )

    # Border tamamen canvas içinde çizilir.
    border_draw = ImageDraw.Draw(result)

    inset = max(
        1,
        border_width // 2,
    )

    border_draw.ellipse(
        (
            inset,
            inset,
            size - inset - 1,
            size - inset - 1,
        ),
        outline=border_color,
        width=border_width,
    )

    return result
def paste_contained(
    canvas: Image.Image,
    image: Image.Image | None,
    box: tuple[int, int, int, int],
) -> None:
    if image is None:
        return

    x1, y1, x2, y2 = box
    width = x2 - x1
    height = y2 - y1

    contained = ImageOps.contain(
        image.convert("RGBA"),
        (width, height),
        method=Image.Resampling.LANCZOS,
    )

    x = x1 + (width - contained.width) // 2
    y = y1 + (height - contained.height) // 2

    canvas.alpha_composite(contained, (x, y))


def draw_metric_pill(
    canvas: Image.Image,
    x: int,
    y: int,
    width: int,
    label: str,
    value: str,
    accent: str,
) -> None:
    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle(
        (x, y, x + width, y + 62),
        radius=18,
        fill=PANEL_LIGHT,
        outline=BORDER,
        width=2,
    )



    draw.text(
        (x + 16, y + 31),
        value,
        font=font(19, bold=True),
        fill=accent,
    )


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def resolve_result_path(
    player_name: str,
    mode: str,
    results_dir: Path,
    explicit_input: Path | None,
) -> Path:
    if explicit_input is not None:
        return explicit_input

    expected = (
        results_dir
        / f"{slugify(player_name)}_{mode}_recommendations.csv"
    )

    if expected.exists():
        return expected

    matches = list(
        results_dir.glob(
            f"{slugify(player_name)}_{mode}_recommendations*.csv"
        )
    )

    if len(matches) == 1:
        return matches[0]

    if not matches:
        raise FileNotFoundError(
            f"Recommendation CSV not found: {expected}"
        )

    raise RuntimeError(
        "Multiple candidate files found: "
        + ", ".join(str(path) for path in matches)
    )


def load_feature_table(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Feature table not found: {path}"
        )

    dataframe = pd.read_csv(path, low_memory=False)

    if "player_id" not in dataframe.columns:
        raise ValueError(
            "Feature table must contain player_id."
        )

    dataframe["player_id"] = pd.to_numeric(
        dataframe["player_id"],
        errors="coerce",
    )

    return dataframe


def first_existing_value(
    row: pd.Series,
    candidates: list[str],
):
    for column in candidates:
        if column not in row.index:
            continue

        value = row.get(column)

        if pd.notna(value) and str(value).strip() not in {"", "-", "nan", "None"}:
            return value

    return np.nan


def resolve_target(
    features: pd.DataFrame,
    player_name: str,
) -> pd.Series:
    exact = features[
        features["player_name"]
        .astype(str)
        .str.casefold()
        .eq(player_name.casefold())
    ]

    if len(exact) == 1:
        raw = exact.iloc[0].copy()

    else:
        partial = features[
            features["player_name"]
            .astype(str)
            .str.contains(
                player_name,
                case=False,
                regex=False,
            )
        ]

        if len(partial) == 1:
            raw = partial.iloc[0].copy()

        elif partial.empty:
            raise ValueError(
                f"Target player not found: {player_name}"
            )

        else:
            raise ValueError(
                "Multiple target players matched: "
                + ", ".join(
                    partial["player_name"]
                    .drop_duplicates()
                    .head(20)
                    .tolist()
                )
            )

    normalized = raw.copy()

    field_candidates = {
        "player_id": [
            "player_id",
            "id",
        ],
        "player_name": [
            "player_name",
            "name",
        ],
        "national_team_id": [
            "national_team_id",
            "team_id",
            "player_team_id",
        ],
        "national_team_name": [
            "national_team_name",
            "team",
            "team_name",
            "player_team_name",
        ],
        "final_role": [
            "final_role",
            "role",
            "role_name",
            "player_role",
        ],
        "archetype": [
            "archetype",
            "archetype_name",
            "player_archetype",
        ],
        "age": [
            "age",
            "player_age",
        ],
        "market_value": [
            "market_value",
            "market_value_eur",
            "value_eur",
        ],
        "weighted_rating": [
            "weighted_rating",
            "rating",
            "tournament_rating",
        ],
        "role_confidence": [
            "role_confidence",
            "confidence",
            "final_role_confidence",
        ],
        "player_quality_score": [
            "player_quality_score",
            "quality_score",
            "tournament_profile_quality_score",
        ],
    }

    for canonical, candidates in field_candidates.items():
        normalized[canonical] = first_existing_value(
            raw,
            candidates,
        )

    return normalized


def prepare_candidates(
    recommendations: pd.DataFrame,
    features: pd.DataFrame,
    mode: str,
) -> pd.DataFrame:
    config = MODE_CONFIG[mode]
    score_column = config["score_column"]

    if score_column not in recommendations.columns:
        raise ValueError(
            f"Missing score column: {score_column}"
        )

    recommendations = recommendations.copy()

    numeric_columns = [
        "player_id",
        "market_value",
        score_column,
        "role_fit_pct",
        "statistical_similarity_pct",
        "spatial_similarity_pct",
        "player_quality_score",
        "data_reliability_score",
        "market_value_advantage_pct",
        "age",
        "weighted_rating",
        "heatmap_similarity_score_pct",
        "effective_heatmap_score_pct",
        "occupation_overlap_pct",
        "lateral_profile_similarity_pct",
        "vertical_profile_similarity_pct",
        "peak_zone_similarity_pct",
        "peak_zone_distance",
        "entropy_similarity_pct",
    ]

    for column in numeric_columns:
        if column in recommendations.columns:
            recommendations[column] = pd.to_numeric(
                recommendations[column],
                errors="coerce",
            )

    base_feature_columns = [
        "player_id",
        "national_team_id",
        "national_team_name",
        "final_role",
        "archetype",
        "age",
        "weighted_rating",
        "market_value",
        "role_confidence",
        "confidence",
        "player_quality_score",
    ]

    optional_profile_columns = set()

    for _, aliases in RADAR_DIMENSIONS:
        optional_profile_columns.update(aliases)

    for aliases in SPATIAL_ALIASES.values():
        optional_profile_columns.update(aliases)

    feature_columns = base_feature_columns + sorted(optional_profile_columns)

    feature_columns = [
        column
        for column in feature_columns
        if column in features.columns
    ]

    metadata = (
        features[feature_columns]
        .drop_duplicates("player_id")
        .copy()
    )

    rename_map = {
        column: f"feature_{column}"
        for column in metadata.columns
        if column != "player_id"
    }

    metadata = metadata.rename(
        columns=rename_map
    )

    recommendations = recommendations.merge(
        metadata,
        on="player_id",
        how="left",
    )

    mergeable_columns = [
        column
        for column in feature_columns
        if column != "player_id"
    ]

    for column in mergeable_columns:
        feature_column = f"feature_{column}"

        if feature_column not in recommendations.columns:
            continue

        if column not in recommendations.columns:
            recommendations[column] = recommendations[
                feature_column
            ]
        else:
            recommendations[column] = recommendations[
                column
            ].combine_first(
                recommendations[feature_column]
            )

    recommendations = recommendations.drop(
        columns=[
            column
            for column in recommendations.columns
            if column.startswith("feature_")
        ],
        errors="ignore",
    )

    recommendations = recommendations.dropna(
        subset=[
            "player_id",
            "market_value",
            score_column,
        ]
    )

    return recommendations.sort_values(
        score_column,
        ascending=False,
    ).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Candidate selection logic
# ---------------------------------------------------------------------------

def choose_decision_candidates(
    dataframe: pd.DataFrame,
    mode: str,
) -> dict[str, pd.Series]:
    """
    Select four distinct recruitment candidates whenever possible.

    BEST OVERALL
        Highest scenario score with role fit and quality as tie-breakers.

    BEST VALUE
        Strong scenario result with a meaningful price advantage.

    PREMIUM OPTION
        Elite-quality candidate. Market value is not penalised.

    CLOSEST ROLE PROFILE
        Highest tactical and spatial role match.
    """
    score_column = MODE_CONFIG[mode]["score_column"]

    overall = dataframe.sort_values(
        [score_column, "role_fit_pct", "player_quality_score"],
        ascending=False,
    ).iloc[0]

    selected_ids = {int(overall["player_id"])}

    value_frame = dataframe.copy()
    value_frame["_value_metric"] = (
        value_frame[score_column].fillna(0) * 0.45
        + value_frame["market_value_advantage_pct"].fillna(0) * 0.40
        + value_frame["role_fit_pct"].fillna(0) * 0.15
    )

    value_pool = value_frame[
        ~value_frame["player_id"].astype(int).isin(selected_ids)
    ]

    if value_pool.empty:
        value_pool = value_frame

    value = value_pool.sort_values(
        "_value_metric",
        ascending=False,
    ).iloc[0]

    selected_ids.add(int(value["player_id"]))

    premium_frame = dataframe.copy()

    # weighted_rating is on a 0-10 scale, so convert it to a percentage-like scale.
    rating_component = (
        premium_frame["weighted_rating"].fillna(0) * 10
    )

    premium_frame["_premium_metric"] = (
        premium_frame["player_quality_score"].fillna(0) * 0.50
        + rating_component * 0.25
        + premium_frame["role_fit_pct"].fillna(0) * 0.15
        + premium_frame["statistical_similarity_pct"].fillna(0) * 0.10
    )

    market_median = premium_frame["market_value"].median()
    quality_threshold = premium_frame["player_quality_score"].quantile(0.60)

    premium_pool = premium_frame[
        premium_frame["player_quality_score"].ge(quality_threshold)
        & premium_frame["market_value"].ge(market_median)
        & ~premium_frame["player_id"].astype(int).isin(selected_ids)
    ]

    if premium_pool.empty:
        premium_pool = premium_frame[
            premium_frame["player_quality_score"].ge(quality_threshold)
            & ~premium_frame["player_id"].astype(int).isin(selected_ids)
        ]

    if premium_pool.empty:
        premium_pool = premium_frame[
            ~premium_frame["player_id"].astype(int).isin(selected_ids)
        ]

    if premium_pool.empty:
        premium_pool = premium_frame

    premium = premium_pool.sort_values(
        "_premium_metric",
        ascending=False,
    ).iloc[0]

    selected_ids.add(int(premium["player_id"]))

    role_pool = dataframe[
        ~dataframe["player_id"].astype(int).isin(selected_ids)
    ]

    if role_pool.empty:
        role_pool = dataframe

    role = role_pool.sort_values(
        ["role_fit_pct", "spatial_similarity_pct", score_column],
        ascending=False,
    ).iloc[0]

    return {
        "BEST OVERALL": overall,
        "BEST VALUE": value,
        "PREMIUM OPTION": premium,
        "CLOSEST ROLE PROFILE": role,
    }

def build_recommendation_reasons(
    row: pd.Series,
    target: pd.Series,
    category: str,
    mode: str,
    max_reasons: int = 4,
) -> list[str]:
    """
    Generate category-specific, data-driven transfer explanations.

    Each reason is based on:
    - role compatibility
    - statistical similarity
    - spatial similarity
    - tournament quality
    - market value
    - age
    - final role / archetype / spatial-profile matches
    """

    reasons: list[
        tuple[float, str]
    ] = []

    score_column = MODE_CONFIG[
        mode
    ]["score_column"]

    decision_score = safe_float(
        row.get(score_column)
    )

    role_fit = safe_float(
        row.get("role_fit_pct")
    )

    statistical_similarity = safe_float(
        row.get(
            "statistical_similarity_pct"
        )
    )

    spatial_similarity = safe_float(
        row.get(
            "spatial_similarity_pct"
        )
    )

    quality = safe_float(
        row.get(
            "player_quality_score"
        )
    )

    reliability = safe_float(
        row.get(
            "data_reliability_score"
        )
    )

    rating = safe_float(
        row.get(
            "weighted_rating"
        )
    )

    target_rating = safe_float(
        target.get(
            "weighted_rating"
        )
    )

    age = safe_float(
        row.get("age")
    )

    target_age = safe_float(
        target.get("age")
    )

    market_value = safe_float(
        row.get(
            "market_value"
        )
    )

    target_market_value = safe_float(
        target.get(
            "market_value"
        )
    )

    market_advantage = safe_float(
        row.get(
            "market_value_advantage_pct"
        )
    )

    same_final_role = same_profile(
        row,
        target,
        "final_role",
    )

    same_archetype = same_profile(
        row,
        target,
        "archetype",
    )

    same_lateral_profile = same_profile(
        row,
        target,
        "lateral_profile",
    )

    same_vertical_profile = same_profile(
        row,
        target,
        "vertical_profile",
    )

    same_spatial_role = same_profile(
        row,
        target,
        "spatial_role",
    )

    same_mobility_profile = same_profile(
        row,
        target,
        "mobility_profile",
    )

    # ----------------------------------------------------------
    # Shared football-profile observations
    # ----------------------------------------------------------

    if same_final_role:
        reasons.append(
            (
                100,
                "Performs the same final role as the target",
            )
        )

    elif role_fit >= 90:
        reasons.append(
            (
                96,
                f"Elite role compatibility ({role_fit:.1f}%)",
            )
        )

    elif role_fit >= 82:
        reasons.append(
            (
                88,
                f"Very strong role fit ({role_fit:.1f}%)",
            )
        )

    elif role_fit >= 72:
        reasons.append(
            (
                76,
                f"Strong tactical fit ({role_fit:.1f}%)",
            )
        )

    if same_archetype:
        reasons.append(
            (
                91,
                "Matches the target statistical archetype",
            )
        )

    if (
        same_lateral_profile
        and same_vertical_profile
    ):
        reasons.append(
            (
                90,
                "Occupies the same lateral and vertical zones",
            )
        )

    elif same_spatial_role:
        reasons.append(
            (
                87,
                "Shares the same tournament spatial role",
            )
        )

    elif spatial_similarity >= 75:
        reasons.append(
            (
                84,
                (
                    "Excellent positional alignment "
                    f"({spatial_similarity:.1f}%)"
                ),
            )
        )

    elif spatial_similarity >= 60:
        reasons.append(
            (
                72,
                (
                    "Strong spatial alignment "
                    f"({spatial_similarity:.1f}%)"
                ),
            )
        )

    if same_mobility_profile:
        reasons.append(
            (
                66,
                "Shows a comparable mobility profile",
            )
        )

    # ----------------------------------------------------------
    # Category-specific explanations
    # ----------------------------------------------------------

    if category == "BEST OVERALL":
        if decision_score >= 80:
            reasons.append(
                (
                    98,
                    (
                        "Highest balanced decision score "
                        f"({decision_score:.1f})"
                    ),
                )
            )

        if quality >= 85:
            reasons.append(
                (
                    89,
                    (
                        "High tournament quality "
                        f"({quality:.1f})"
                    ),
                )
            )

        if (
            rating > target_rating
            and rating >= 7.0
        ):
            reasons.append(
                (
                    86,
                    (
                        "Higher tournament rating "
                        f"({rating:.2f} vs "
                        f"{target_rating:.2f})"
                    ),
                )
            )

        cheaper_text = (
            market_value_difference_text(
                market_value,
                target_market_value,
            )
        )

        if cheaper_text:
            reasons.append(
                (
                    83,
                    cheaper_text,
                )
            )

    elif category == "BEST VALUE":
        cheaper_text = (
            market_value_difference_text(
                market_value,
                target_market_value,
            )
        )

        if cheaper_text:
            reasons.append(
                (
                    100,
                    cheaper_text,
                )
            )

        if market_advantage >= 80:
            reasons.append(
                (
                    96,
                    (
                        "Exceptional market-value advantage "
                        f"({market_advantage:.1f}%)"
                    ),
                )
            )

        elif market_advantage >= 55:
            reasons.append(
                (
                    88,
                    (
                        "Strong market-value advantage "
                        f"({market_advantage:.1f}%)"
                    ),
                )
            )

        if (
            role_fit >= 80
            and market_advantage >= 50
        ):
            reasons.append(
                (
                    92,
                    "Combines strong role fit with low acquisition cost",
                )
            )

        if reliability >= 80:
            reasons.append(
                (
                    71,
                    "Value case supported by reliable tournament evidence",
                )
            )

    elif category == "PREMIUM OPTION":
        if quality >= 90:
            reasons.append(
                (
                    100,
                    (
                        "Elite tournament quality "
                        f"({quality:.1f})"
                    ),
                )
            )

        elif quality >= 82:
            reasons.append(
                (
                    92,
                    (
                        "High-level tournament quality "
                        f"({quality:.1f})"
                    ),
                )
            )

        if rating >= 7.50:
            reasons.append(
                (
                    95,
                    (
                        "Outstanding tournament rating "
                        f"({rating:.2f})"
                    ),
                )
            )

        elif rating >= 7.10:
            reasons.append(
                (
                    84,
                    (
                        "Strong tournament rating "
                        f"({rating:.2f})"
                    ),
                )
            )

        if (
            age > 0
            and age <= 24
        ):
            reasons.append(
                (
                    88,
                    (
                        "Premium long-term asset "
                        f"at age {age:.1f}"
                    ),
                )
            )

        elif (
            target_age > 0
            and age > 0
            and age < target_age
        ):
            reasons.append(
                (
                    80,
                    (
                        f"{target_age - age:.1f} years younger "
                        "than the target"
                    ),
                )
            )

        if market_value >= target_market_value:
            reasons.append(
                (
                    67,
                    "Premium acquisition justified by profile quality",
                )
            )

    elif category == "CLOSEST ROLE PROFILE":
        if statistical_similarity >= 75:
            reasons.append(
                (
                    98,
                    (
                        "Excellent statistical similarity "
                        f"({statistical_similarity:.1f}%)"
                    ),
                )
            )

        elif statistical_similarity >= 55:
            reasons.append(
                (
                    84,
                    (
                        "Strong statistical similarity "
                        f"({statistical_similarity:.1f}%)"
                    ),
                )
            )

        if spatial_similarity >= 75:
            reasons.append(
                (
                    96,
                    (
                        "Excellent spatial similarity "
                        f"({spatial_similarity:.1f}%)"
                    ),
                )
            )

        elif spatial_similarity >= 55:
            reasons.append(
                (
                    82,
                    (
                        "Strong spatial similarity "
                        f"({spatial_similarity:.1f}%)"
                    ),
                )
            )

        if (
            same_final_role
            and same_archetype
        ):
            reasons.append(
                (
                    99,
                    "Matches both role identity and archetype",
                )
            )

        if (
            same_lateral_profile
            and same_vertical_profile
        ):
            reasons.append(
                (
                    94,
                    "Replicates the target pitch occupation",
                )
            )

    # ----------------------------------------------------------
    # Remaining useful observations
    # ----------------------------------------------------------

    if statistical_similarity >= 70:
        reasons.append(
            (
                78,
                (
                    "Close production profile "
                    f"({statistical_similarity:.1f}%)"
                ),
            )
        )

    if reliability >= 85:
        reasons.append(
            (
                64,
                (
                    "High evidence reliability "
                    f"({reliability:.1f})"
                ),
            )
        )

    if (
        target_age > 0
        and age > 0
        and age <= target_age - 3
    ):
        reasons.append(
            (
                73,
                (
                    f"{target_age - age:.1f} years younger "
                    "than the target"
                ),
            )
        )

    # ----------------------------------------------------------
    # Deduplicate and select the strongest statements
    # ----------------------------------------------------------

    reasons.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    selected: list[str] = []
    normalized_selected: set[str] = set()

    for _, reason in reasons:
        normalized = (
            reason.casefold()
            .replace("%", "")
            .replace("(", "")
            .replace(")", "")
        )

        # Avoid multiple reasons explaining nearly the same thing.
        reason_group = None

        if "role" in normalized:
            reason_group = "role"

        elif (
            "spatial" in normalized
            or "position" in normalized
            or "zone" in normalized
            or "pitch occupation" in normalized
        ):
            reason_group = "spatial"

        elif (
            "market" in normalized
            or "cheaper" in normalized
            or "cost" in normalized
        ):
            reason_group = "market"

        elif (
            "quality" in normalized
            or "rating" in normalized
        ):
            reason_group = "quality"

        elif (
            "statistical" in normalized
            or "production profile" in normalized
            or "archetype" in normalized
        ):
            reason_group = "statistical"

        elif (
            "younger" in normalized
            or "long-term" in normalized
        ):
            reason_group = "age"

        if (
            reason_group is not None
            and reason_group
            in normalized_selected
        ):
            continue

        selected.append(
            reason
        )

        if reason_group is not None:
            normalized_selected.add(
                reason_group
            )

        if len(selected) >= max_reasons:
            break

    fallback_reasons = [
        "Reliable tournament evidence",
        "Balanced recruitment profile",
        "Suitable tactical alternative",
        "Data-supported transfer target",
    ]

    for fallback in fallback_reasons:
        if len(selected) >= max_reasons:
            break

        selected.append(
            fallback
        )

    return selected[:max_reasons]



def draw_check_bullet(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    max_width: int,
) -> None:
    """Draw a green circular check and one compact reason line."""
    green = "#52D77D"

    draw.ellipse(
        (x, y + 2, x + 17, y + 19),
        outline=green,
        width=2,
    )

    draw.line(
        (x + 4, y + 10, x + 8, y + 14),
        fill=green,
        width=2,
    )

    draw.line(
        (x + 8, y + 14, x + 14, y + 6),
        fill=green,
        width=2,
    )

    selected_font = font(12)
    safe = truncate_text(
        draw,
        clean_text(text),
        selected_font,
        max_width,
    )

    draw.text(
        (x + 26, y),
        safe,
        font=selected_font,
        fill=TEXT_SOFT,
    )


# ---------------------------------------------------------------------------
# Scatter chart
# ---------------------------------------------------------------------------

def market_tick(value: float, _: Any) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.0f}M"

    if value >= 1_000:
        return f"{value / 1_000:.0f}K"

    return f"{value:.0f}"


def build_scatter_chart(
    dataframe: pd.DataFrame,
    mode: str,
    numbered_players: pd.DataFrame,
    width: int,
    height: int,
) -> Image.Image:
    """Create the analytical chart with local player-photo markers."""
    config = MODE_CONFIG[mode]
    score_column = config["score_column"]
    accent = config["accent"]

    figure = plt.figure(
        figsize=(width / 170, height / 170),
        dpi=170,
        facecolor=PANEL,
    )

    axis = figure.add_axes([0.085, 0.14, 0.88, 0.77])
    axis.set_facecolor(PANEL)

    median_value = float(dataframe["market_value"].median())
    score_threshold = float(
        dataframe[score_column].quantile(0.68)
    )

    axis.add_patch(
        Rectangle(
            (0, score_threshold),
            median_value,
            100 - score_threshold,
            facecolor=accent,
            edgecolor=accent,
            linewidth=1,
            linestyle=(0, (4, 5)),
            alpha=0.07,
            zorder=0,
        )
    )

    axis.axvline(
        median_value,
        color="#3A5C4B",
        linewidth=0.8,
        linestyle=(0, (3, 5)),
        zorder=1,
    )

    axis.axhline(
        score_threshold,
        color="#43D477",
        linewidth=0.9,
        linestyle=(0, (5, 5)),
        alpha=0.85,
        zorder=1,
    )

    same_role = dataframe.get(
        "same_final_role",
        pd.Series(False, index=dataframe.index),
    ).fillna(False)

    same_archetype = dataframe.get(
        "same_archetype",
        pd.Series(False, index=dataframe.index),
    ).fillna(False)

    quality = dataframe["player_quality_score"].fillna(50)
    reliability = dataframe["data_reliability_score"].fillna(50)
    sizes = 42 + quality * 0.68 + reliability * 0.38

    numbered_ids = set(
        numbered_players["player_id"].dropna().astype(int).tolist()
    )

    background = dataframe[
        ~dataframe["player_id"].astype(int).isin(numbered_ids)
    ]

    bg_same_role = same_role.loc[background.index]
    bg_same_archetype = same_archetype.loc[background.index]
    bg_sizes = sizes.loc[background.index]

    groups = [
        (
            background[bg_same_role],
            bg_sizes[bg_same_role],
            "D",
        ),
        (
            background[~bg_same_role & bg_same_archetype],
            bg_sizes[~bg_same_role & bg_same_archetype],
            "s",
        ),
        (
            background[~bg_same_role & ~bg_same_archetype],
            bg_sizes[~bg_same_role & ~bg_same_archetype],
            "o",
        ),
    ]

    for group, group_sizes, marker in groups:
        if group.empty:
            continue

        axis.scatter(
            group["market_value"],
            group[score_column],
            s=group_sizes,
            marker=marker,
            c=group["role_fit_pct"],
            cmap="viridis",
            vmin=0,
            vmax=100,
            edgecolors="#DDEFE6",
            linewidths=0.55,
            alpha=0.82,
            zorder=3,
        )

    # Premium area label.
    x_max_data = max(float(dataframe["market_value"].max()), 1)

    axis.text(
        x_max_data * 0.79,
        min(float(dataframe[score_column].max()) + 1.8, 98),
        "PREMIUM TARGETS",
        color="#C876FF",
        fontsize=7.2,
        fontweight="bold",
        ha="center",
        zorder=4,
    )

    axis.text(
        median_value * 0.05,
        min(score_threshold + 1.2, 98),
        config["zone"],
        color=accent,
        fontsize=7.1,
        fontweight="bold",
        zorder=4,
    )

    for number, (_, row) in enumerate(
        numbered_players.iterrows(),
        start=1,
    ):
        player_image = load_player_image(
            player_id=row.get("player_id"),
            player_name=clean_text(row.get("player_name")),
            size=(84, 84),
            font_path=system_font_path(True),
        )

        player_image = circle_crop(
            player_image,
            84,
            accent,
            border_width=4,
        )

        image_array = np.asarray(player_image.convert("RGBA"))

        annotation = AnnotationBbox(
            OffsetImage(image_array, zoom=0.34),
            (
                row["market_value"],
                row[score_column],
            ),
            frameon=False,
            box_alignment=(0.5, 0.5),
            zorder=9,
        )

        axis.add_artist(annotation)

        # Number badge.
        axis.annotate(
            str(number),
            (
                row["market_value"],
                row[score_column],
            ),
            xytext=(14, 15),
            textcoords="offset points",
            ha="center",
            va="center",
            fontsize=6.2,
            fontweight="bold",
            color=BACKGROUND,
            bbox={
                "boxstyle": "circle,pad=0.27",
                "facecolor": accent,
                "edgecolor": WHITE,
                "linewidth": 0.8,
            },
            zorder=12,
        )


    axis.set_xlim(0, x_max_data * 1.08)

    y_min = max(0, float(dataframe[score_column].min()) - 6)
    y_max = min(100, float(dataframe[score_column].max()) + 8)

    if y_max - y_min < 24:
        y_min = max(0, y_min - 6)
        y_max = min(100, y_max + 6)

    axis.set_ylim(y_min, y_max)

    axis.xaxis.set_major_formatter(
        FuncFormatter(market_tick)
    )

    axis.set_xlabel(
        "MARKET VALUE (EUR)",
        color=TEXT_SOFT,
        fontsize=7,
        fontweight="bold",
        labelpad=9,
    )

    axis.set_ylabel(
        "ROLE FIT SCORE (%)",
        color=TEXT_SOFT,
        fontsize=7,
        fontweight="bold",
        labelpad=9,
    )

    axis.tick_params(
        colors=TEXT_SOFT,
        labelsize=6.4,
    )

    axis.grid(
        color=GRID,
        linewidth=0.62,
        alpha=0.72,
        zorder=0,
    )

    for spine in axis.spines.values():
        spine.set_color(BORDER)
        spine.set_linewidth(0.8)

    buffer = io.BytesIO()

    figure.savefig(
        buffer,
        format="png",
        dpi=170,
        facecolor=figure.get_facecolor(),
    )

    plt.close(figure)
    buffer.seek(0)

    return Image.open(buffer).convert("RGBA")


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

def draw_header(
    canvas: Image.Image,
    target: pd.Series,
    mode: str,
    role_fit_benchmark: float,
) -> None:
    """Draw the report title and an expanded benchmark target card."""
    config = MODE_CONFIG[mode]
    accent = config["accent"]
    draw = ImageDraw.Draw(canvas)

    draw.text(
        (45, 32),
        "WC2026 | TRANSFER INTELLIGENCE",
        font=font(22, bold=True),
        fill=accent,
    )

    title = clean_text(target["player_name"]).upper()

    title_font = fit_font(
        draw,
        title,
        max_width=1030,
        start_size=59,
        minimum_size=42,
        bold=True,
    )

    draw.text(
        (45, 72),
        title,
        font=title_font,
        fill=TEXT,
    )

    draw.text(
        (45, 148),
        config["title"],
        font=font(27, bold=True),
        fill=accent,
    )

    draw.text(
        (45, 187),
        config["subtitle"],
        font=font(17),
        fill=TEXT_SOFT,
    )

    profile_box = (1240, 24, 2350, 225)

    draw_panel(
        canvas,
        profile_box,
        fill=PANEL,
        radius=24,
        shadow=False,
    )

    image_size = 160

    player_image = load_player_image(
        player_id=target.get("player_id"),
        player_name=clean_text(target.get("player_name")),
        size=(image_size, image_size),
        font_path=system_font_path(True),
    )

    player_image = circle_crop(
        player_image,
        image_size,
        accent,
        border_width=5,
    )

    canvas.alpha_composite(
        player_image,
        (1275, 43),
    )

    text_x = 1460

    draw.text(
        (text_x, 42),
        "TARGET PROFILE",
        font=font(15, bold=True),
        fill="#65D590",
    )

    role = clean_text(target.get("final_role"))
    role_font = fit_font(
        draw,
        role,
        max_width=385,
        start_size=20,
        minimum_size=14,
        bold=True,
    )

    draw.text(
        (text_x, 72),
        role,
        font=role_font,
        fill=TEXT,
    )

    draw.text(
        (text_x, 108),
        clean_text(target.get("archetype")),
        font=font(16),
        fill=accent,
    )

    flag = load_country_flag(
        country_name=clean_text(
            target.get("national_team_name")
        ),
        size=(42, 31),
        ratio="4x3",
    )

    paste_contained(
        canvas,
        flag,
        (text_x, 139, text_x + 42, 170),
    )

    draw.text(
        (text_x + 54, 143),
        clean_text(target.get("national_team_name")),
        font=font(15),
        fill=TEXT_SOFT,
    )

    draw.text(
        (text_x, 181),
        (
            f"Age {format_age(target.get('age'))}  |  "
            f"{format_market_value(target.get('market_value'))}"
        ),
        font=font(15, bold=True),
        fill=TEXT_SOFT,
    )

    role_benchmark = float(role_fit_benchmark)

    if role_benchmark <= 1:
        role_benchmark *= 100

    quality_benchmark = float(
        target.get("player_quality_score", 0)
        if pd.notna(target.get("player_quality_score", np.nan))
        else 0
    )

    if quality_benchmark <= 0:
        rating = float(
            target.get("weighted_rating", 0)
            if pd.notna(target.get("weighted_rating", np.nan))
            else 0
        )
        quality_benchmark = rating * 10

    metric_boxes = [
        (
            1880,
            60,
            2070,
            176,
            "ROLE FIT BENCHMARK",
            f"{role_benchmark:.1f}%" if role_benchmark > 0 else "-",
        ),
        (
            2100,
            60,
            2310,
            176,
            "QUALITY BENCHMARK",
            f"{quality_benchmark:.1f}" if quality_benchmark > 0 else "-",
        ),
    ]

    for x1, y1, x2, y2, label, value in metric_boxes:
        draw.rounded_rectangle(
            (x1, y1, x2, y2),
            radius=18,
            fill=PANEL_ALT,
            outline=BORDER,
            width=2,
        )

        draw.text(
            (x1 + 16, y1 + 18),
            label,
            font=font(11, bold=True),
            fill=TEXT_MUTED,
        )

        draw.text(
            (x1 + 16, y1 + 55),
            value,
            font=font(27, bold=True),
            fill="#52D77D",
        )


# ---------------------------------------------------------------------------
# Decision cards
# ---------------------------------------------------------------------------

def draw_decision_card(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    category: str,
    row: pd.Series,
    target: pd.Series,
    mode: str,
    accent: str,
    highlighted: bool,
) -> None:
    """Draw a product-style recruitment card with explanation bullets."""
    score_column = MODE_CONFIG[mode]["score_column"]
    x1, y1, x2, y2 = box
    draw = ImageDraw.Draw(canvas)

    draw_panel(
        canvas,
        box,
        fill=PANEL_ALT,
        outline=accent if highlighted else BORDER,
        width=3 if highlighted else 2,
        radius=21,
        shadow=True,
    )

    image_size = 105

    player_image = load_player_image(
        player_id=row.get("player_id"),
        player_name=clean_text(row.get("player_name")),
        size=(image_size, image_size),
        font_path=system_font_path(True),
    )

    player_image = circle_crop(
        player_image,
        image_size,
        accent,
        border_width=4,
    )

    canvas.alpha_composite(
        player_image,
        (x1 + 18, y1 + 53),
    )

    flag = load_country_flag(
        country_name=clean_text(
            row.get("national_team_name")
        ),
        size=(44, 33),
        ratio="4x3",
    )

    paste_contained(
        canvas,
        flag,
        (x2 - 64, y1 + 16, x2 - 20, y1 + 49),
    )

    draw.text(
        (x1 + 18, y1 + 17),
        category,
        font=font(13, bold=True),
        fill=accent,
    )

    text_x = x1 + 144
    text_width = x2 - text_x - 25

    name = clean_text(row.get("player_name"))

    name_font = fit_font(
        draw,
        name,
        max_width=text_width,
        start_size=24,
        minimum_size=16,
        bold=True,
    )

    name_lines = wrap_text(
        draw,
        name,
        name_font,
        text_width,
        max_lines=2,
    )

    for index, line in enumerate(name_lines):
        draw.text(
            (text_x, y1 + 55 + index * 27),
            line,
            font=name_font,
            fill=TEXT,
        )

    role_lines = wrap_text(
        draw,
        clean_text(row.get("final_role")),
        font(13),
        text_width,
        max_lines=2,
    )

    role_y = y1 + 112

    for index, line in enumerate(role_lines):
        draw.text(
            (text_x, role_y + index * 16),
            line,
            font=font(13),
            fill=TEXT_SOFT,
        )

    draw.text(
        (text_x, y1 + 151),
        (
            f"{format_score(row.get(score_column))} | "
            f"{format_market_value(row.get('market_value'))}"
        ),
        font=font(15, bold=True),
        fill=accent,
    )

    reasons = build_recommendation_reasons(
        row=row,
        target=target,
        category=category,
        mode=mode,
        max_reasons=4,
    )

    reason_y = y1 + 194

    for index, reason in enumerate(reasons):
        draw_check_bullet(
            draw,
            x1 + 18,
            reason_y + index * 29,
            reason,
            max_width=(x2 - x1 - 65),
        )


# ---------------------------------------------------------------------------
# Ranked list
# ---------------------------------------------------------------------------

def draw_ranked_candidates(
    canvas: Image.Image,
    dataframe: pd.DataFrame,
    mode: str,
    start_x: int,
    start_y: int,
    total_width: int,
    card_height: int,
    count: int = 6,
) -> None:
    """Draw six detailed recruitment targets in one horizontal row."""
    config = MODE_CONFIG[mode]
    score_column = config["score_column"]
    accent = config["accent"]
    draw = ImageDraw.Draw(canvas)

    draw.text(
        (start_x, start_y - 38),
        "TOP RECRUITMENT TARGETS",
        font=font(19, bold=True),
        fill=TEXT,
    )

    candidates = dataframe.head(count)

    gap = 14
    card_width = int(
        (total_width - gap * (count - 1)) / count
    )

    for index, (_, row) in enumerate(
        candidates.iterrows(),
        start=1,
    ):
        x1 = start_x + (index - 1) * (
            card_width + gap
        )
        y1 = start_y
        x2 = x1 + card_width
        y2 = y1 + card_height

        draw_panel(
            canvas,
            (x1, y1, x2, y2),
            fill=PANEL,
            radius=18,
            shadow=False,
        )

        flag = load_country_flag(
            country_name=clean_text(
                row.get("national_team_name")
            ),
            size=(38, 28),
            ratio="4x3",
        )

        paste_contained(
            canvas,
            flag,
            (x2 - 54, y1 + 16, x2 - 16, y1 + 44),
        )

        image_size = 88

        player_image = load_player_image(
            player_id=row.get("player_id"),
            player_name=clean_text(row.get("player_name")),
            size=(image_size, image_size),
            font_path=system_font_path(True),
        )

        player_image = circle_crop(
            player_image,
            image_size,
            accent,
            border_width=3,
        )

        canvas.alpha_composite(
            player_image,
            (x1 + 18, y1 + 35),
        )

        badge_x = x1 + 28
        badge_y = y1 + 22

        draw.ellipse(
            (
                badge_x - 15,
                badge_y - 15,
                badge_x + 15,
                badge_y + 15,
            ),
            fill=accent,
        )

        badge_font = font(14, bold=True)
        badge_text = str(index)
        badge_box = draw.textbbox(
            (0, 0),
            badge_text,
            font=badge_font,
        )

        draw.text(
            (
                badge_x - (badge_box[2] - badge_box[0]) / 2,
                badge_y - (badge_box[3] - badge_box[1]) / 2 - 1,
            ),
            badge_text,
            font=badge_font,
            fill=BACKGROUND,
        )

        text_x = x1 + 124
        text_width = card_width - 142

        name = clean_text(row.get("player_name"))
        name_font = fit_font(
            draw,
            name,
            max_width=text_width,
            start_size=18,
            minimum_size=13,
            bold=True,
        )

        name_lines = wrap_text(
            draw,
            name,
            name_font,
            text_width,
            max_lines=2,
        )

        for line_index, line in enumerate(name_lines):
            draw.text(
                (text_x, y1 + 22 + line_index * 22),
                line,
                font=name_font,
                fill=TEXT,
            )

        role_lines = wrap_text(
            draw,
            clean_text(row.get("final_role")),
            font(11),
            text_width,
            max_lines=2,
        )

        for line_index, line in enumerate(role_lines):
            draw.text(
                (text_x, y1 + 71 + line_index * 14),
                line,
                font=font(11),
                fill=TEXT_SOFT,
            )

        draw.text(
            (text_x, y1 + 109),
            (
                f"{format_score(row.get(score_column))} | "
                f"{format_market_value(row.get('market_value'))}"
            ),
            font=font(14, bold=True),
            fill=accent,
        )

        divider_y = y1 + 145

        draw.line(
            (x1 + 16, divider_y, x2 - 16, divider_y),
            fill=GRID,
            width=2,
        )

        draw.text(
            (x1 + 16, y1 + 160),
            (
                f"Fit {format_score(row.get('role_fit_pct'))}%  |  "
                f"Sim {format_score(row.get('statistical_similarity_pct'))}%"
            ),
            font=font(11),
            fill=TEXT_SOFT,
        )

        draw.text(
            (x1 + 16, y1 + 184),
            (
                f"Spatial {format_score(row.get('spatial_similarity_pct'))}%  |  "
                f"Quality {format_score(row.get('player_quality_score'))}"
            ),
            font=font(11),
            fill=TEXT_MUTED,
        )

def create_role_radar(
    target: pd.Series,
    candidate: pd.Series,
    width: int,
    height: int,
    target_color: str,
    candidate_color: str,
) -> Image.Image:
    labels, target_values, target_missing = (
        extract_radar_profile(target)
    )

    _, candidate_values, candidate_missing = (
        extract_radar_profile(candidate)
    )

    # Uzun etiketleri iki satıra böl.
    label_map = {
        "Creativity": "Creativity",
        "Progression": "Progression",
        "Passing Volume": "Passing\nVolume",
        "Ball Security": "Ball\nSecurity",
        "Dribbling": "Dribbling",
        "Scoring Threat": "Scoring\nThreat",
        "Defensive Work": "Defensive\nWork",
        "Wide Creation": "Wide\nCreation",
    }

    display_labels = [
        label_map.get(label, label)
        for label in labels
    ]

    angles = np.linspace(
        0,
        2 * np.pi,
        len(labels),
        endpoint=False,
    ).tolist()

    closed_angles = angles + angles[:1]
    target_plot = target_values + target_values[:1]
    candidate_plot = candidate_values + candidate_values[:1]

    # DPI değeri hem oluştururken hem kaydederken aynı olsun.
    dpi = 180

    figure = plt.figure(
        figsize=(
            width / dpi,
            height / dpi,
        ),
        dpi=dpi,
        facecolor=PANEL,
    )

    # Radar biraz küçültülüyor.
    # Böylece dış etiketler için yeterli boşluk kalıyor.
    axis = figure.add_axes(
        [
            0.19,  # left
            0.15,  # bottom
            0.63,  # width
            0.70,  # height
        ],
        projection="polar",
    )

    axis.set_facecolor(PANEL)

    axis.set_theta_offset(
        np.pi / 2
    )

    axis.set_theta_direction(
        -1
    )

    axis.set_ylim(
        0,
        100,
    )

    axis.set_yticks(
        [
            20,
            40,
            60,
            80,
            100,
        ]
    )

    axis.set_yticklabels(
        [
            "20",
            "40",
            "60",
            "80",
            "100",
        ],
        color=TEXT_MUTED,
        fontsize=5,
    )

    # Radial değerleri sağ üst tarafa taşı.
    axis.set_rlabel_position(
        18
    )

    axis.set_xticks(
        angles
    )

    axis.set_xticklabels(
        display_labels,
        color=TEXT_SOFT,
        fontsize=5,
        fontweight="bold",
        linespacing=1.05,
    )

    # Etiketleri radar çemberinden uzaklaştır.
    axis.tick_params(
        axis="x",
        pad=5,
    )

    axis.tick_params(
        axis="y",
        pad=2,
    )

    axis.grid(
        color=GRID,
        linewidth=0.8,
        alpha=0.85,
    )

    axis.spines[
        "polar"
    ].set_color(
        BORDER
    )

    axis.spines[
        "polar"
    ].set_linewidth(
        1.0
    )

    axis.plot(
        closed_angles,
        target_plot,
        color=target_color,
        linewidth=2.4,
        solid_capstyle="round",
        solid_joinstyle="round",
        zorder=5,
    )

    axis.fill(
        closed_angles,
        target_plot,
        color=target_color,
        alpha=0.12,
        zorder=3,
    )

    axis.plot(
        closed_angles,
        candidate_plot,
        color=candidate_color,
        linewidth=2.4,
        solid_capstyle="round",
        solid_joinstyle="round",
        zorder=6,
    )

    axis.fill(
        closed_angles,
        candidate_plot,
        color=candidate_color,
        alpha=0.10,
        zorder=2,
    )

    # Köşe noktaları görünürlüğü artırır.
    axis.scatter(
        angles,
        target_values,
        s=14,
        color=target_color,
        edgecolors=PANEL,
        linewidths=0.6,
        zorder=8,
    )

    axis.scatter(
        angles,
        candidate_values,
        s=14,
        color=candidate_color,
        edgecolors=PANEL,
        linewidths=0.6,
        zorder=9,
    )

    buffer = io.BytesIO()

    figure.savefig(
        buffer,
        format="png",
        dpi=dpi,
        facecolor=figure.get_facecolor(),
        transparent=False,
        bbox_inches=None,
        pad_inches=0,
    )

    plt.close(
        figure
    )

    buffer.seek(
        0
    )

    scale = 1.25

    render_width = int(width * scale)
    render_height = int(height * scale)

    figure = plt.figure(
        figsize=(
            render_width / dpi,
            render_height / dpi,
        ),
        dpi=dpi,
        facecolor=PANEL,
    )

    image = Image.open(
        buffer
    ).convert(
        "RGBA"
    )

    # Tam istenen ölçüye sabitle.
    return ImageOps.contain(
        image,
        (
            width,
            height,
        ),
        method=Image.Resampling.LANCZOS,
    )


def draw_mini_pitch(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    target: pd.Series,
    candidate: pd.Series,
    target_color: str,
    candidate_color: str,
) -> None:
    x1, y1, x2, y2 = box
    draw = ImageDraw.Draw(canvas)

    draw.rounded_rectangle(box, radius=18, fill="#0E6A35", outline=BORDER, width=2)

    margin = 15
    px1, py1, px2, py2 = x1 + margin, y1 + margin, x2 - margin, y2 - margin
    line = "#E8F5ED"

    draw.rectangle((px1, py1, px2, py2), outline=line, width=2)
    middle_x = (px1 + px2) // 2
    draw.line((middle_x, py1, middle_x, py2), fill=line, width=2)

    center_y = (py1 + py2) // 2
    radius = int(min(px2 - px1, py2 - py1) * 0.12)
    draw.ellipse((middle_x - radius, center_y - radius, middle_x + radius, center_y + radius), outline=line, width=2)
    draw.ellipse((middle_x - 3, center_y - 3, middle_x + 3, center_y + 3), fill=line)

    penalty_w = int((px2 - px1) * 0.17)
    penalty_h = int((py2 - py1) * 0.45)
    draw.rectangle((px1, center_y - penalty_h // 2, px1 + penalty_w, center_y + penalty_h // 2), outline=line, width=2)
    draw.rectangle((px2 - penalty_w, center_y - penalty_h // 2, px2, center_y + penalty_h // 2), outline=line, width=2)

    # Tactical grid: vertical thirds and five horizontal lanes.
    for fraction in (1 / 3, 2 / 3):
        grid_x = px1 + int((px2 - px1) * fraction)
        draw.line((grid_x, py1, grid_x, py2), fill="#79A88C", width=1)

    for fraction in (0.2, 0.4, 0.6, 0.8):
        grid_y = py1 + int((py2 - py1) * fraction)
        draw.line((px1, grid_y, px2, grid_y), fill="#79A88C", width=1)

    def coordinate(row: pd.Series) -> tuple[float, float]:
        mean_x = canonical_spatial_value(row, "mean_x")
        mean_y = canonical_spatial_value(row, "mean_y")

        if pd.isna(mean_x):
            mean_x = 55.0
        if pd.isna(mean_y):
            mean_y = 50.0

        return float(np.clip(mean_x, 0, 100)), float(np.clip(mean_y, 0, 100))

    def plot_player(row: pd.Series, color: str, letter: str) -> None:
        mean_x, mean_y = coordinate(row)
        plot_x = px1 + int((px2 - px1) * mean_x / 100)
        plot_y = py1 + int((py2 - py1) * mean_y / 100)

        spread = canonical_spatial_value(row, "spatial_spread")
        if pd.notna(spread):
            spread_radius = int(np.clip(float(spread) * 2.0, 12, 38))
            draw.ellipse(
                (plot_x - spread_radius, plot_y - spread_radius, plot_x + spread_radius, plot_y + spread_radius),
                fill=color + "28",
                outline=color,
                width=2,
            )

        draw.ellipse((plot_x - 13, plot_y - 13, plot_x + 13, plot_y + 13), fill=color, outline=WHITE, width=2)
        selected_font = font(12, bold=True)
        bbox = draw.textbbox((0, 0), letter, font=selected_font)
        draw.text(
            (plot_x - (bbox[2] - bbox[0]) / 2, plot_y - (bbox[3] - bbox[1]) / 2 - 1),
            letter,
            font=selected_font,
            fill=BACKGROUND,
        )

    plot_player(target, target_color, "T")
    plot_player(candidate, candidate_color, "A")


def draw_role_intelligence_panel(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    target: pd.Series,
    candidate: pd.Series,
    mode: str,
    heatmap_archive: np.lib.npyio.NpzFile | None,
) -> None:
    """
    Draw the final role comparison section.

    Layout:
        Radar comparison | Natural 105:68 tactical pitch | Role intelligence

    Role intelligence:
        Primary Function
        Typical Pitch Behaviour | Target Spatial Behaviour
        Key Requirements under Typical Pitch Behaviour
    """
    x1, y1, x2, y2 = box
    draw = ImageDraw.Draw(canvas)

    accent = MODE_CONFIG[mode]["accent"]
    candidate_color = "#55D991"

    draw_panel(
        canvas,
        box,
        fill=PANEL,
        radius=24,
        shadow=False,
    )

    # --------------------------------------------------------------
    # Main section heading
    # --------------------------------------------------------------
    draw.text(
        (x1 + 20, y1 + 14),
        "ROLE PROFILE COMPARISON",
        font=font(17, bold=True),
        fill=TEXT,
    )

    draw.text(
        (x1 + 20, y1 + 42),
        (
            f"{clean_text(target.get('player_name'))} vs "
            f"{clean_text(candidate.get('player_name'))}"
        ),
        font=font(12),
        fill=TEXT_MUTED,
    )

    content_top = y1 + 64
    content_bottom = y2 - 16
    content_height = content_bottom - content_top

    # Balanced final widths.
    radar_col = (
        x1 + 18,
        content_top,
        x1 + 745,
        content_bottom,
    )

    pitch_col = (
        x1 + 765,
        content_top,
        x1 + 1515,
        content_bottom,
    )

    role_col = (
        x1 + 1535,
        content_top,
        x2 - 18,
        content_bottom,
    )

    draw.line(
        (
            radar_col[2] + 9,
            content_top + 10,
            radar_col[2] + 9,
            content_bottom - 10,
        ),
        fill=BORDER,
        width=2,
    )

    draw.line(
        (
            pitch_col[2] + 9,
            content_top + 10,
            pitch_col[2] + 9,
            content_bottom - 10,
        ),
        fill=BORDER,
        width=2,
    )

    # --------------------------------------------------------------
    # 1. Radar comparison
    # --------------------------------------------------------------
    radar_col_width = (
            radar_col[2] - radar_col[0]
    )

    radar_col_height = (
            radar_col[3] - radar_col[1]
    )

    # Radarın mevcut kullanılabilir alana göre temel boyutu.
    base_radar_size = min(
        radar_col_width - 20,
        radar_col_height - 2,
    )

    # %15–20 büyütmek için.
    radar_scale = 1.22

    radar_size = int(
        base_radar_size * radar_scale
    )

    # Radar sütunun dışına taşmasın.
    maximum_radar_size = min(
        radar_col_width,
        radar_col_height,
    )

    radar_size = min(
        radar_size,
        maximum_radar_size,
    )

    # Gerçek sütunun ortasına yerleştir.
    radar_x = (
            radar_col[0]
            + (
                    radar_col_width
                    - radar_size
            ) // 2
    )

    radar_y = (
            radar_col[1]
            + (
                    radar_col_height
                    - radar_size
            ) // 2
    )

    radar = create_role_radar(
        target,
        candidate,
        width=radar_size,
        height=radar_size,
        target_color=accent,
        candidate_color=candidate_color,
    )

    # Burada radar_size - 10 kullanma.
    # Bu tekrar küçülmesine neden oluyordu.
    radar = ImageOps.contain(
        radar,
        (
            radar_size,
            radar_size,
        ),
        method=Image.Resampling.LANCZOS,
    )

    canvas.alpha_composite(
        radar,
        (
            radar_x,
            radar_y,
        ),
    )

    # --------------------------------------------------------------
    # 2. Tactical map — natural football-pitch proportion
    # --------------------------------------------------------------
    draw.text(
        (pitch_col[0] + 10, pitch_col[1] + 5),
        "HEATMAP OCCUPATION MAP",
        font=font(14, bold=True),
        fill="#65D590",
    )

    pitch_area_width = pitch_col[2] - pitch_col[0] - 36
    pitch_area_height = pitch_col[3] - pitch_col[1]

    # Reserve space before calculating the pitch size. The pitch is limited
    # by both available width and available height, so it can never overflow
    # into the player cards or outside the parent panel.
    title_height = 28
    legend_height = 76
    gap_after_pitch = 13
    vertical_safety_margin = 18

    maximum_pitch_height = max(
        120,
        pitch_area_height
        - title_height
        - legend_height
        - gap_after_pitch
        - vertical_safety_margin,
    )

    maximum_width_from_height = int(
        maximum_pitch_height * 105 / 68
    )

    # Natural 105:68 landscape ratio, constrained on both axes.
    desired_pitch_width = min(
        pitch_area_width,
        maximum_width_from_height,
        520,
    )

    desired_pitch_height = int(
        desired_pitch_width * 68 / 105
    )

    tactical_total_height = (
        title_height
        + desired_pitch_height
        + gap_after_pitch
        + legend_height
    )

    tactical_start_y = max(
        pitch_col[1],
        pitch_col[1]
        + (pitch_area_height - tactical_total_height) // 2,
    )

    pitch_x = (
        pitch_col[0]
        + (
            (pitch_col[2] - pitch_col[0])
            - desired_pitch_width
        ) // 2
    )

    pitch_box = (
        pitch_x,
        tactical_start_y + title_height,
        pitch_x + desired_pitch_width,
        tactical_start_y + title_height + desired_pitch_height,
    )

    draw_heatmap_mini_pitch(
        canvas=canvas,
        box=pitch_box,
        target=target,
        candidate=candidate,
        target_color=accent,
        candidate_color=candidate_color,
        heatmap_archive=heatmap_archive,
        font_path=system_font_path(True),
    )

    legend_y = pitch_box[3] + gap_after_pitch
    legend_gap = 12
    legend_width = (
        (desired_pitch_width - legend_gap) // 2
    )

    legend_players = [
        (
            target,
            accent,
            "TARGET",
            pitch_x,
        ),
        (
            candidate,
            candidate_color,
            "BEST OVERALL",
            pitch_x + legend_width + legend_gap,
        ),
    ]

    for row, color, label, legend_x in legend_players:
        draw.rounded_rectangle(
            (
                legend_x,
                legend_y,
                legend_x + legend_width,
                legend_y + legend_height,
            ),
            radius=15,
            fill=PANEL_ALT,
            outline=BORDER,
            width=2,
        )

        portrait = load_player_image(
            player_id=row.get("player_id"),
            player_name=clean_text(
                row.get("player_name")
            ),
            size=(52, 52),
            font_path=system_font_path(True),
        )

        portrait = circle_crop(
            portrait,
            52,
            color,
            border_width=3,
        )

        canvas.alpha_composite(
            portrait,
            (legend_x + 10, legend_y + 12),
        )

        text_x = legend_x + 73
        text_width = legend_width - 84

        draw.text(
            (text_x, legend_y + 9),
            label,
            font=font(9, bold=True),
            fill=color,
        )

        player_name = truncate_text(
            draw,
            clean_text(row.get("player_name")),
            font(12, bold=True),
            text_width,
        )

        draw.text(
            (text_x, legend_y + 28),
            player_name,
            font=font(12, bold=True),
            fill=TEXT,
        )

        lateral = clean_text(
            canonical_spatial_value(
                row,
                "lateral_profile",
            )
        )

        vertical = clean_text(
            canonical_spatial_value(
                row,
                "vertical_profile",
            )
        )

        summary = truncate_text(
            draw,
            f"{lateral} · {vertical}",
            font(9),
            text_width,
        )

        draw.text(
            (text_x, legend_y + 49),
            summary,
            font=font(9),
            fill=TEXT_MUTED,
        )

    # --------------------------------------------------------------
    # 3. Target role intelligence
    # --------------------------------------------------------------
    draw.rounded_rectangle(
        role_col,
        radius=18,
        fill=PANEL_ALT,
        outline=BORDER,
        width=2,
    )

    padding = 18
    inner_x1 = role_col[0] + padding
    inner_x2 = role_col[2] - padding
    inner_width = inner_x2 - inner_x1

    cursor_y = role_col[1] + 14

    draw.text(
        (inner_x1, cursor_y),
        "TARGET ROLE INTELLIGENCE",
        font=font(13, bold=True),
        fill="#65D590",
    )

    cursor_y += 31

    role_name = clean_text(
        target.get("final_role")
    )

    role_name_font = fit_font(
        draw,
        role_name,
        inner_width,
        22,
        15,
        bold=True,
    )

    role_name_lines = wrap_text(
        draw,
        role_name,
        role_name_font,
        inner_width,
        max_lines=2,
    )

    for line in role_name_lines:
        draw.text(
            (inner_x1, cursor_y),
            line,
            font=role_name_font,
            fill=TEXT,
        )

        cursor_y += role_name_font.size + 2

    cursor_y += 6

    intelligence = role_intelligence_for(
        role_name
    )

    draw.text(
        (inner_x1, cursor_y),
        "PRIMARY FUNCTION",
        font=font(10, bold=True),
        fill=TEXT_MUTED,
    )

    cursor_y += 20

    function_lines = wrap_text(
        draw,
        intelligence["function"],
        font(10),
        inner_width,
        max_lines=3,
    )

    for line in function_lines:
        draw.text(
            (inner_x1, cursor_y),
            line,
            font=font(10),
            fill=TEXT_SOFT,
        )

        cursor_y += 14

    cursor_y += 12

    # ----------------------------------------------------------
    # Two-column information area.
    # ----------------------------------------------------------
    column_gap = 24
    left_width = int(
        (inner_width - column_gap) * 0.54
    )
    right_width = (
        inner_width - column_gap - left_width
    )

    left_x = inner_x1
    right_x = (
        inner_x1 + left_width + column_gap
    )

    columns_top = cursor_y
    column_bottom = role_col[3] - 16

    divider_x = inner_x1 + left_width + column_gap // 2

    draw.line(
        (
            divider_x,
            columns_top,
            divider_x,
            column_bottom,
        ),
        fill=BORDER,
        width=2,
    )

    # ----------------------------------------------------------
    # Left: Typical Pitch Behaviour + Key Requirements
    # ----------------------------------------------------------
    left_cursor = columns_top

    draw.text(
        (left_x, left_cursor),
        "TYPICAL PITCH BEHAVIOUR",
        font=font(10, bold=True),
        fill=TEXT_MUTED,
    )

    left_cursor += 22

    for behaviour in intelligence[
        "behaviours"
    ][:4]:
        lines = wrap_text(
            draw,
            behaviour,
            font(9),
            left_width - 21,
            max_lines=2,
        )

        draw.ellipse(
            (
                left_x + 1,
                left_cursor + 4,
                left_x + 8,
                left_cursor + 11,
            ),
            fill=candidate_color,
        )

        for line_index, line in enumerate(lines):
            draw.text(
                (
                    left_x + 17,
                    left_cursor
                    + line_index * 13,
                ),
                line,
                font=font(9),
                fill=TEXT_SOFT,
            )

        left_cursor += max(
            17,
            len(lines) * 13 + 5,
        )

    left_cursor += 9

    # Key Requirements must remain under Typical Pitch Behaviour.
    draw.line(
        (
            left_x,
            left_cursor,
            left_x + left_width,
            left_cursor,
        ),
        fill=BORDER,
        width=2,
    )

    left_cursor += 10

    draw.text(
        (left_x, left_cursor),
        "KEY REQUIREMENTS",
        font=font(10, bold=True),
        fill=TEXT_MUTED,
    )

    left_cursor += 21

    requirement_text = " · ".join(
        intelligence["requirements"]
    )

    requirement_lines = wrap_text(
        draw,
        requirement_text,
        font(9),
        left_width,
        max_lines=2,
    )

    for line in requirement_lines:
        if left_cursor + 13 > column_bottom:
            break

        draw.text(
            (left_x, left_cursor),
            line,
            font=font(9, bold=True),
            fill=accent,
        )

        left_cursor += 13

    # ----------------------------------------------------------
    # Right: Target Spatial Behaviour
    # ----------------------------------------------------------
    right_cursor = columns_top

    draw.text(
        (right_x, right_cursor),
        "TARGET SPATIAL BEHAVIOUR",
        font=font(10, bold=True),
        fill=TEXT_MUTED,
    )

    right_cursor += 24

    target_lateral = clean_text(
        canonical_spatial_value(
            target,
            "lateral_profile",
        )
    )

    target_vertical = clean_text(
        canonical_spatial_value(
            target,
            "vertical_profile",
        )
    )

    target_mobility = clean_text(
        canonical_spatial_value(
            target,
            "mobility_profile",
        )
    )

    target_spatial_role = clean_text(
        canonical_spatial_value(
            target,
            "spatial_role",
        )
    )

    candidate_lateral = clean_text(
        canonical_spatial_value(
            candidate,
            "lateral_profile",
        )
    )

    candidate_vertical = clean_text(
        canonical_spatial_value(
            candidate,
            "vertical_profile",
        )
    )

    candidate_mobility = clean_text(
        canonical_spatial_value(
            candidate,
            "mobility_profile",
        )
    )

    target_rows = [
        (
            "LATERAL PROFILE",
            target_lateral,
        ),
        (
            "VERTICAL PROFILE",
            target_vertical,
        ),
        (
            "SPATIAL ROLE",
            target_spatial_role,
        ),
        (
            "MOBILITY",
            target_mobility,
        ),
    ]

    for label, value in target_rows:
        if right_cursor + 33 > column_bottom:
            break

        draw.text(
            (right_x, right_cursor),
            label,
            font=font(8, bold=True),
            fill="#65D590",
        )

        right_cursor += 13

        value_lines = wrap_text(
            draw,
            value,
            font(9),
            right_width,
            max_lines=2,
        )

        for line in value_lines:
            draw.text(
                (right_x, right_cursor),
                line,
                font=font(9),
                fill=TEXT_SOFT,
            )

            right_cursor += 13

        right_cursor += 7

    # Candidate comparison at the bottom of the spatial column.
    if right_cursor + 48 <= column_bottom:
        draw.line(
            (
                right_x,
                right_cursor,
                right_x + right_width,
                right_cursor,
            ),
            fill=BORDER,
            width=2,
        )

        right_cursor += 10

        draw.text(
            (right_x, right_cursor),
            "BEST OVERALL ALTERNATIVE",
            font=font(8, bold=True),
            fill=candidate_color,
        )

        right_cursor += 15

        alternative_text = (
            f"{candidate_lateral} · "
            f"{candidate_vertical} · "
            f"{candidate_mobility}"
        )

        alternative_lines = wrap_text(
            draw,
            alternative_text,
            font(9),
            right_width,
            max_lines=2,
        )

        for line in alternative_lines:
            if right_cursor + 13 > column_bottom:
                break

            draw.text(
                (right_x, right_cursor),
                line,
                font=font(9),
                fill=TEXT_SOFT,
            )

            right_cursor += 13


# ---------------------------------------------------------------------------
# Dashboard builder
# ---------------------------------------------------------------------------

def create_dashboard(
    recommendations: pd.DataFrame,
    target: pd.Series,
    mode: str,
    output_path: Path,
    top_n: int,
    heatmap_archive: np.lib.npyio.NpzFile | None,
) -> None:
    config = MODE_CONFIG[mode]
    accent = config["accent"]

    candidates = recommendations.head(top_n).copy()

    if candidates.empty:
        raise ValueError(
            "No eligible candidates were found."
        )

    decisions = choose_decision_candidates(
        candidates,
        mode,
    )

    numbered = candidates.head(6)

    canvas = Image.new(
        "RGBA",
        (CANVAS_WIDTH, CANVAS_HEIGHT),
        BACKGROUND,
    )

    best_overall = decisions["BEST OVERALL"]

    role_fit_benchmark = float(
        best_overall.get("role_fit_pct", 0)
        if pd.notna(best_overall.get("role_fit_pct", np.nan))
        else 0
    )

    draw_header(
        canvas,
        target,
        mode,
        role_fit_benchmark,
    )

    chart_panel = (
        40,
        250,
        1445,
        1015,
    )

    draw_panel(
        canvas,
        chart_panel,
        fill=PANEL,
        radius=26,
        shadow=True,
    )

    draw = ImageDraw.Draw(canvas)

    draw.text(
        (75, 278),
        "ROLE FIT vs MARKET VALUE",
        font=font(18, bold=True),
        fill=TEXT,
    )

    chart = build_scatter_chart(
        candidates,
        mode,
        numbered,
        width=1350,
        height=665,
    )

    chart = ImageOps.fit(
        chart,
        (1350, 665),
        method=Image.Resampling.LANCZOS,
    )

    canvas.alpha_composite(
        chart,
        (68, 320),
    )

    decision_panel = (
        1470,
        250,
        2355,
        1015,
    )

    draw_panel(
        canvas,
        decision_panel,
        fill=PANEL,
        radius=26,
        shadow=True,
    )

    draw.text(
        (1500, 278),
        "RECRUITMENT DECISION",
        font=font(18, bold=True),
        fill=TEXT_MUTED,
    )

    category_colors = {
        "BEST OVERALL": accent,
        "BEST VALUE": "#73D989",
        "PREMIUM OPTION": "#78B4FF",
        "CLOSEST ROLE PROFILE": "#BF82FF",
    }

    card_gap_x = 16
    card_gap_y = 16
    card_width = 414
    card_height = 330
    card_start_x = 1498
    card_start_y = 322

    for index, (category, row) in enumerate(
        decisions.items()
    ):
        column = index % 2
        row_index = index // 2

        x1 = card_start_x + column * (
            card_width + card_gap_x
        )

        y1 = card_start_y + row_index * (
            card_height + card_gap_y
        )

        draw_decision_card(
            canvas,
            (
                x1,
                y1,
                x1 + card_width,
                y1 + card_height,
            ),
            category,
            row,
            target,
            mode,
            category_colors[category],
            highlighted=(
                    category == "BEST OVERALL"
            ),
        )

    draw_role_intelligence_panel(
        canvas,
        (
            40,
            1038,
            2355,
            1510,
        ),
        target,
        best_overall,
        mode,
        heatmap_archive,
    )

    draw_ranked_candidates(
        canvas,
        candidates,
        mode,
        start_x=40,
        start_y=1555,
        total_width=2315,
        card_height=235,
        count=6,
    )

    draw.text(
        (40, 1810),
        (
            "Tournament-only model | Scores are mode-specific | "
            "Player images, team logos and flags are loaded from local assets."
        ),
        font=font(12),
        fill=TEXT_MUTED,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    canvas.convert("RGB").save(
        output_path,
        quality=96,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a premium local-asset transfer dashboard."
        )
    )

    parser.add_argument(
        "--player",
        required=True,
    )

    parser.add_argument(
        "--mode",
        choices=list(MODE_CONFIG),
        default="value",
    )

    parser.add_argument(
        "--heatmap-grids",
        type=Path,
        default=DEFAULT_HEATMAP_GRIDS,
    )

    parser.add_argument(
        "--features",
        type=Path,
        default=DEFAULT_FEATURES,
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--results-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )

    parser.add_argument(
        "--spatial-profiles",
        type=Path,
        default=DEFAULT_SPATIAL_PROFILES,
    )

    parser.add_argument(
        "--archetype-profiles",
        type=Path,
        default=DEFAULT_ARCHETYPE_PROFILES,
    )

    parser.add_argument(
        "--top-n",
        type=int,
        default=24,
    )

    return parser.parse_args()
def safe_float(
    value,
    default: float = 0.0,
) -> float:
    try:
        if value is None or pd.isna(value):
            return default

        return float(value)

    except (
        TypeError,
        ValueError,
    ):
        return default


def normalize_profile_text(
    value,
) -> str:
    if value is None or pd.isna(value):
        return ""

    return str(value).strip().casefold()


def market_value_difference_text(
    candidate_value,
    target_value,
) -> str | None:
    candidate_value = safe_float(
        candidate_value
    )

    target_value = safe_float(
        target_value
    )

    if (
        candidate_value <= 0
        or target_value <= 0
    ):
        return None

    difference = (
        target_value
        - candidate_value
    )

    if difference <= 0:
        return None

    return (
        f"{format_market_value(difference)} "
        "cheaper than target"
    )


def same_profile(
    candidate: pd.Series,
    target: pd.Series,
    column: str,
) -> bool:
    candidate_value = normalize_profile_text(
        candidate.get(column)
    )

    target_value = normalize_profile_text(
        target.get(column)
    )

    return (
        bool(candidate_value)
        and bool(target_value)
        and candidate_value == target_value
    )

def main() -> None:
    args = parse_args()

    features = load_feature_table(
        args.features
    )

    features = enrich_with_optional_profiles(
        features,
        args.spatial_profiles,
        prefix="spatial",
    )

    features = enrich_with_optional_profiles(
        features,
        args.archetype_profiles,
        prefix="archetype_profile",
    )

    target = resolve_target(
        features,
        args.player,
    )

    input_path = resolve_result_path(
        player_name=args.player,
        mode=args.mode,
        results_dir=args.results_dir,
        explicit_input=args.input,
    )

    raw_recommendations = pd.read_csv(
        input_path,
        low_memory=False,
    )

    # Fill target profile from recommendation CSV when the feature table
    # does not contain every target field.
    target_fallback_columns = {
        "player_id": [
            "target_player_id",
        ],
        "player_name": [
            "target_player_name",
        ],
        "national_team_id": [
            "target_team_id",
            "target_national_team_id",
        ],
        "national_team_name": [
            "target_team",
            "target_team_name",
            "target_national_team_name",
        ],
        "final_role": [
            "target_final_role",
            "target_role",
        ],
        "archetype": [
            "target_archetype",
        ],
        "age": [
            "target_age",
        ],
        "market_value": [
            "target_market_value",
        ],
        "weighted_rating": [
            "target_weighted_rating",
            "target_rating",
        ],
        "role_confidence": [
            "target_role_confidence",
            "target_confidence",
        ],
        "player_quality_score": [
            "target_player_quality_score",
            "target_quality_score",
        ],
    }

    if not raw_recommendations.empty:
        recommendation_row = raw_recommendations.iloc[0]

        for canonical, candidates in target_fallback_columns.items():
            current_value = target.get(canonical, np.nan)

            if pd.notna(current_value) and str(current_value).strip() not in {
                "",
                "-",
                "nan",
                "None",
            }:
                continue

            fallback_value = first_existing_value(
                recommendation_row,
                candidates,
            )

            if pd.notna(fallback_value):
                target[canonical] = fallback_value

    recommendations = prepare_candidates(
        raw_recommendations,
        features,
        args.mode,
    )

    heatmap_archive = load_heatmap_grid_archive(
        args.heatmap_grids
    )

    output_path = (
        args.output_dir
        / (
            f"{slugify(args.player)}_"
            f"{args.mode}_transfer_dashboard.png"
        )
    )

    create_dashboard(
        recommendations=recommendations,
        target=target,
        mode=args.mode,
        output_path=output_path,
        top_n=args.top_n,
        heatmap_archive=heatmap_archive,
    )

    print(
        "Premium transfer dashboard created:"
    )
    print(output_path)


if __name__ == "__main__":
    main()
