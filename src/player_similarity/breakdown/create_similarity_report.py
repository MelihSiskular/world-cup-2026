# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import math
import re
import unicodedata
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch


DEFAULT_BREAKDOWN_CSV = Path(
    "/Users/melihsiskular/PycharmProjects/wc2026/data/processed/player_similarity/"
    "player_similarity_breakdown_long.csv"
)

DEFAULT_PROFILES = Path(
    "/Users/melihsiskular/PycharmProjects/wc2026/data/processed/player_similarity/"
    "player_profiles.csv"
)

DEFAULT_OUTPUT_DIR = Path(
    "/Users/melihsiskular/PycharmProjects/wc2026/docs/images/player_similarity/scout_reports"
)


CATEGORY_LABELS = {
    "scoring_similarity_pct": "Scoring",
    "creativity_similarity_pct": "Creativity",
    "passing_similarity_pct": "Passing",
    "carrying_dribbling_similarity_pct": "Carrying & Dribbling",
    "dribbling_similarity_pct": "Dribbling",
    "defensive_work_similarity_pct": "Defensive Work",
    "defending_similarity_pct": "Defending",
    "duels_similarity_pct": "Duels",
    "progression_similarity_pct": "Progression",
    "security_similarity_pct": "Security",
    "ball_security_similarity_pct": "Ball Security",
    "involvement_similarity_pct": "Involvement",
    "goalkeeping_similarity_pct": "Goalkeeping",
    "distribution_similarity_pct": "Distribution",
    "sweeping_similarity_pct": "Sweeping",
    "errors_similarity_pct": "Error Profile",
    "overall_quality_similarity_pct": "Overall Quality",
}

CATEGORY_COLORS = {
    "Scoring": "#ff5d73",
    "Creativity": "#ffd166",
    "Passing": "#4dabf7",
    "Carrying & Dribbling": "#b197fc",
    "Dribbling": "#b197fc",
    "Defensive Work": "#51cf66",
    "Defending": "#51cf66",
    "Duels": "#ff922b",
    "Progression": "#20c997",
    "Security": "#22b8cf",
    "Ball Security": "#22b8cf",
    "Involvement": "#f06595",
    "Goalkeeping": "#38d9a9",
    "Distribution": "#74c0fc",
    "Sweeping": "#63e6be",
    "Error Profile": "#ffa94d",
    "Overall Quality": "#e9ecef",
}


STAT_ROWS = [
    ("weighted_rating", "Rating", "{:.2f}"),
    ("goals_per90", "Goals / 90", "{:.2f}"),
    ("goalAssist_per90", "Assists / 90", "{:.2f}"),
    ("expectedGoals_per90", "xG / 90", "{:.2f}"),
    ("expectedAssists_per90", "xA / 90", "{:.2f}"),
    ("keyPass_per90", "Key Passes / 90", "{:.2f}"),
    ("totalShots_per90", "Shots / 90", "{:.2f}"),
    ("pass_accuracy", "Pass Accuracy", "{:.1%}"),
    ("contest_success", "Dribble Success", "{:.1%}"),
    ("minutes", "Minutes", "{:.0f}"),
]


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(text))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "_", ascii_text).strip("_").lower()


def load_breakdown(csv_path: Path) -> pd.DataFrame:

    if csv_path.exists():
        return pd.read_csv(csv_path, low_memory=False)

    raise FileNotFoundError(
        "Similarity breakdown bulunamadÄ±. Ãnce "
        "`python -m src.players.build_similarity_breakdown` Ã§alÄ±ÅtÄ±r."
    )


def resolve_name(values: pd.Series, query: str, label: str) -> str:
    names = values.dropna().astype(str).drop_duplicates()

    exact = names[names.str.casefold().eq(query.casefold())]
    if len(exact) == 1:
        return str(exact.iloc[0])

    partial = names[
        names.str.contains(
            query,
            case=False,
            regex=False,
        )
    ]

    if len(partial) == 1:
        return str(partial.iloc[0])

    if partial.empty:
        raise ValueError(f"{label} bulunamadÄ±: {query}")

    raise ValueError(
        f"{label} birden fazla sonuÃ§la eÅleÅti: "
        + ", ".join(partial.head(10).tolist())
    )


def select_comparison(
    breakdown: pd.DataFrame,
    player_query: str,
    candidate_query: str | None,
    rank: int,
) -> pd.Series:
    source_name = resolve_name(
        breakdown["source_player_name"],
        player_query,
        "Hedef oyuncu",
    )

    candidates = (
        breakdown[
            breakdown["source_player_name"].eq(source_name)
        ]
        .sort_values(
            ["overall_similarity", "target_minutes"],
            ascending=[False, False],
        )
        .reset_index(drop=True)
    )

    if candidates.empty:
        raise ValueError(f"{source_name} iÃ§in aday bulunamadÄ±.")

    if candidate_query:
        candidate_name = resolve_name(
            candidates["target_player_name"],
            candidate_query,
            "Aday oyuncu",
        )
        return candidates[
            candidates["target_player_name"].eq(candidate_name)
        ].iloc[0]

    if not 1 <= rank <= len(candidates):
        raise ValueError(f"rank 1 ile {len(candidates)} arasÄ±nda olmalÄ±.")

    return candidates.iloc[rank - 1]


def get_profile(
    profiles: pd.DataFrame,
    player_id,
) -> pd.Series:
    row = profiles[profiles["player_id"].eq(player_id)]

    if row.empty:
        raise ValueError(f"Profil bulunamadÄ±: {player_id}")

    return row.iloc[0]


def format_market_value(value, currency) -> str:
    if pd.isna(value):
        return "Unknown"

    value = float(value)

    if value >= 1_000_000:
        display = f"{value / 1_000_000:.1f}M"
    elif value >= 1_000:
        display = f"{value / 1_000:.0f}K"
    else:
        display = f"{value:.0f}"

    return f"{currency or 'EUR'} {display}"


def get_similarity_items(comparison: pd.Series) -> list[tuple[str, float]]:
    items = []

    for column, label in CATEGORY_LABELS.items():
        if column not in comparison.index:
            continue

        value = comparison[column]

        if pd.isna(value):
            continue

        items.append((label, float(value)))

    return items


def draw_header(
    figure,
    source_profile: pd.Series,
    target_profile: pd.Series,
    comparison: pd.Series,
):
    source_name = comparison["source_player_name"]
    target_name = comparison["target_player_name"]
    overall = float(comparison["overall_similarity_pct"])

    figure.text(
        0.05,
        0.955,
        "PLAYER SIMILARITY SCOUT REPORT",
        color="#8bdcb4",
        fontsize=13,
        fontweight="bold",
        va="top",
    )

    figure.text(
        0.05,
        0.915,
        f"{source_name}  vs  {target_name}",
        color="white",
        fontsize=27,
        fontweight="bold",
        va="top",
    )

    figure.text(
        0.95,
        0.917,
        f"{overall:.1f}%",
        color="#4be3a1",
        fontsize=30,
        fontweight="bold",
        ha="right",
        va="top",
    )

    figure.text(
        0.95,
        0.875,
        "OVERALL SIMILARITY",
        color="#90b8a3",
        fontsize=9,
        fontweight="bold",
        ha="right",
    )

    source_meta = (
        f"{source_profile['national_team_name']}  |  "
        f"{source_profile['position']}  |  "
        f"Age {source_profile['age']:.1f}  |  "
        f"{source_profile['minutes']:.0f} min  |  "
        f"{format_market_value(source_profile['market_value'],source_profile['market_value_currency'],)}"

    )

    target_meta = (
    f"{target_profile['national_team_name']}  |  "
    f"{target_profile['position']}  |  "
    f"Age {target_profile['age']:.1f}  |  "
    f"{target_profile['minutes']:.0f} min  |  "
    f"{format_market_value(target_profile['market_value'],target_profile['market_value_currency'],)}"
    )

    figure.text(
        0.05,
        0.865,
        source_meta,
        color="#c7ddcf",
        fontsize=10,
    )

    figure.text(
        0.05,
        0.838,
        target_meta,
        color="#91b5a2",
        fontsize=10,
    )


def draw_radar(
    axis,
    similarity_items: list[tuple[str, float]],
):
    labels = [label for label, _ in similarity_items]
    values = [value for _, value in similarity_items]

    angles = np.linspace(
        0,
        2 * math.pi,
        len(labels),
        endpoint=False,
    ).tolist()

    closed_angles = angles + angles[:1]
    closed_values = values + values[:1]

    axis.set_theta_offset(math.pi / 2)
    axis.set_theta_direction(-1)
    axis.set_facecolor("#0d261b")

    axis.plot(
        closed_angles,
        closed_values,
        color="#48e6a3",
        linewidth=2.8,
        zorder=3,
    )
    axis.fill(
        closed_angles,
        closed_values,
        color="#35d493",
        alpha=0.22,
        zorder=2,
    )
    axis.scatter(
        angles,
        values,
        s=55,
        color="#e6fff3",
        edgecolor="#48e6a3",
        linewidth=1.5,
        zorder=4,
    )

    axis.set_ylim(0, 100)
    axis.set_yticks([20, 40, 60, 80, 100])
    axis.set_yticklabels(
        ["20", "40", "60", "80", "100"],
        color="#709b85",
        fontsize=8,
    )
    axis.set_rlabel_position(6)

    axis.set_xticks(angles)
    axis.set_xticklabels(
        labels,
        color="#f3fff8",
        fontsize=9,
        fontweight="bold",
    )

    axis.yaxis.grid(
        color="#315343",
        linewidth=0.8,
        alpha=0.7,
    )
    axis.xaxis.grid(
        color="#315343",
        linewidth=0.8,
        alpha=0.6,
    )

    axis.spines["polar"].set_color("#4a7561")
    axis.spines["polar"].set_linewidth(1.0)

    axis.set_title(
        "SIMILARITY PROFILE",
        color="#bce5cf",
        fontsize=12,
        fontweight="bold",
        pad=22,
    )


def draw_score_bars(
    axis,
    similarity_items: list[tuple[str, float]],
):
    axis.set_xlim(0, 110)
    axis.set_ylim(-0.7, len(similarity_items) - 0.3)
    axis.axis("off")
    axis.set_facecolor("#0a1e15")

    axis.text(
        0,
        len(similarity_items) - 0.05,
        "CATEGORY BREAKDOWN",
        color="#bce5cf",
        fontsize=12,
        fontweight="bold",
        va="bottom",
    )

    for index, (label, value) in enumerate(reversed(similarity_items)):
        y = index
        color = CATEGORY_COLORS.get(label, "#48e6a3")

        axis.text(
            0,
            y,
            label,
            color="#f1fff7",
            fontsize=9.5,
            fontweight="bold",
            va="center",
        )

        axis.add_patch(
            FancyBboxPatch(
                (33, y - 0.18),
                60,
                0.36,
                boxstyle="round,pad=0.02,rounding_size=0.12",
                facecolor="#183528",
                edgecolor="none",
            )
        )

        axis.add_patch(
            FancyBboxPatch(
                (33, y - 0.18),
                60 * value / 100,
                0.36,
                boxstyle="round,pad=0.02,rounding_size=0.12",
                facecolor=color,
                edgecolor="none",
            )
        )

        axis.text(
            98,
            y,
            f"{value:.1f}%",
            color=color,
            fontsize=10,
            fontweight="bold",
            ha="right",
            va="center",
        )


def format_stat(
    profile: pd.Series,
    column: str,
    formatter: str,
) -> str:
    if column not in profile.index or pd.isna(profile[column]):
        return "-"

    return formatter.format(float(profile[column]))


def draw_stat_table(
    axis,
    source_profile: pd.Series,
    target_profile: pd.Series,
    source_name: str,
    target_name: str,
):
    axis.axis("off")
    axis.set_facecolor("#081b13")

    axis.text(
        0.0,
        1.04,
        "STATISTICAL COMPARISON",
        color="#bce5cf",
        fontsize=12,
        fontweight="bold",
        transform=axis.transAxes,
    )

    visible_rows = [
        row
        for row in STAT_ROWS
        if row[0] in source_profile.index
        and row[0] in target_profile.index
    ]

    cell_text = []

    for column, label, formatter in visible_rows:
        cell_text.append(
            [
                label,
                format_stat(source_profile, column, formatter),
                format_stat(target_profile, column, formatter),
            ]
        )

    table = axis.table(
        cellText=cell_text,
        colLabels=[
            "Metric",
            source_name,
            target_name,
        ],
        loc="center",
        cellLoc="center",
        colLoc="center",
        bbox=[0, 0, 1, 0.95],
    )

    table.auto_set_font_size(False)
    table.set_fontsize(9.5)
    table.scale(1, 1.35)

    for (row, column), cell in table.get_celld().items():
        cell.set_edgecolor("#244b39")
        cell.set_linewidth(0.8)

        if row == 0:
            cell.set_facecolor("#153629")
            cell.get_text().set_color("#dffff0")
            cell.get_text().set_fontweight("bold")
        else:
            cell.set_facecolor(
                "#0d271c"
                if row % 2
                else "#102d21"
            )
            cell.get_text().set_color("#e9fff3")

            if column == 0:
                cell.get_text().set_ha("left")
                cell.get_text().set_fontweight("bold")


def create_scout_report(
    comparison: pd.Series,
    source_profile: pd.Series,
    target_profile: pd.Series,
    output_path: Path,
):
    similarity_items = get_similarity_items(comparison)

    if len(similarity_items) < 3:
        raise ValueError(
            "Rapor iÃ§in yeterli similarity kategorisi yok."
        )

    figure = plt.figure(
        figsize=(16, 11),
        facecolor="#06170f",
    )

    grid = GridSpec(
        2,
        2,
        figure=figure,
        height_ratios=[1.1, 0.9],
        width_ratios=[1.05, 0.95],
        hspace=0.24,
        wspace=0.16,
        top=0.78,
        bottom=0.06,
        left=0.05,
        right=0.95,
    )

    radar_axis = figure.add_subplot(
        grid[0, 0],
        polar=True,
    )

    bars_axis = figure.add_subplot(
        grid[0, 1]
    )

    table_axis = figure.add_subplot(
        grid[1, :]
    )

    draw_header(
        figure,
        source_profile,
        target_profile,
        comparison,
    )

    draw_radar(
        radar_axis,
        similarity_items,
    )

    draw_score_bars(
        bars_axis,
        similarity_items,
    )

    draw_stat_table(
        table_axis,
        source_profile,
        target_profile,
        str(comparison["source_player_name"]),
        str(comparison["target_player_name"]),
    )

    figure.text(
        0.5,
        0.018,
        (
            "Tournament-based comparison using position-specific "
            "per-90 metrics and cosine similarity."
        ),
        ha="center",
        color="#6f9682",
        fontsize=8.5,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
        facecolor=figure.get_facecolor(),
    )

    plt.close(figure)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--player",
        required=True,
    )

    parser.add_argument(
        "--candidate",
        default=None,
    )

    parser.add_argument(
        "--rank",
        type=int,
        default=1,
    )



    parser.add_argument(
        "--breakdown-csv",
        type=Path,
        default=DEFAULT_BREAKDOWN_CSV,
    )

    parser.add_argument(
        "--profiles",
        type=Path,
        default=DEFAULT_PROFILES,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    breakdown = load_breakdown(
        args.breakdown_csv,
    )

    profiles = pd.read_csv(
        args.profiles,
        low_memory=False,
    )

    comparison = select_comparison(
        breakdown,
        player_query=args.player,
        candidate_query=args.candidate,
        rank=args.rank,
    )

    source_profile = get_profile(
        profiles,
        comparison["source_player_id"],
    )

    target_profile = get_profile(
        profiles,
        comparison["target_player_id"],
    )

    filename = (
        f"{slugify(comparison['source_player_name'])}"
        "_vs_"
        f"{slugify(comparison['target_player_name'])}"
        "_scout_report.png"
    )

    output_path = args.output_dir / filename

    create_scout_report(
        comparison,
        source_profile,
        target_profile,
        output_path,
    )

    print(
        f"Rapor oluÅturuldu: {output_path}"
    )


if __name__ == "__main__":
    main()
