# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch


DEFAULT_PROFILES = Path(
    "data/processed/player_similarity/player_profiles.csv"
)

DEFAULT_TRANSFER_DIR = Path(
    "data/processed/player_similarity/transfer_recommendations"
)

DEFAULT_OUTPUT_DIR = Path(
    "docs/images/player_similarity/transfer_reports"
)


def slugify(text: str) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        str(text),
    )
    ascii_text = normalized.encode(
        "ascii",
        "ignore",
    ).decode("ascii")

    return (
        re.sub(r"[^a-zA-Z0-9]+", "_", ascii_text)
        .strip("_")
        .lower()
    )


def resolve_player_name(
    profiles: pd.DataFrame,
    query: str,
) -> str:
    names = (
        profiles["player_name"]
        .dropna()
        .astype(str)
        .drop_duplicates()
    )

    exact = names[
        names.str.casefold().eq(query.casefold())
    ]

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
        raise ValueError(
            f"Oyuncu bulunamadÄ±: {query}"
        )

    raise ValueError(
        "Birden fazla oyuncu eÅleÅti: "
        + ", ".join(partial.head(10).tolist())
    )


def get_player_profile(
    profiles: pd.DataFrame,
    player_name: str,
) -> pd.Series:
    row = profiles[
        profiles["player_name"].eq(player_name)
    ]

    if row.empty:
        raise ValueError(
            f"Profil bulunamadÄ±: {player_name}"
        )

    return row.iloc[0]


def format_market_value(
    value,
    currency="EUR",
) -> str:
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


def safe_float(
    value,
    default=0.0,
) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def draw_panel(
    axis,
    x,
    y,
    width,
    height,
    facecolor,
    edgecolor,
    radius=0.025,
):
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle=(
            f"round,pad=0.012,"
            f"rounding_size={radius}"
        ),
        transform=axis.transAxes,
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=1.2,
    )
    axis.add_patch(patch)
    return patch


def draw_target_card(
    axis,
    profile: pd.Series,
):
    axis.axis("off")
    axis.set_facecolor("#071710")

    draw_panel(
        axis,
        0.02,
        0.08,
        0.96,
        0.84,
        facecolor="#0d2a1d",
        edgecolor="#2e6f50",
    )

    axis.text(
        0.07,
        0.82,
        "TARGET PLAYER",
        transform=axis.transAxes,
        color="#8be0b5",
        fontsize=11,
        fontweight="bold",
    )

    axis.text(
        0.07,
        0.64,
        str(profile["player_name"]),
        transform=axis.transAxes,
        color="white",
        fontsize=24,
        fontweight="bold",
    )

    meta = (
        f"{profile.get('national_team_name', '-')}"
        f" | {profile.get('position', '-')}"
        f" | Age {safe_float(profile.get('age')):.1f}"
    )

    axis.text(
        0.07,
        0.49,
        meta,
        transform=axis.transAxes,
        color="#bad6c6",
        fontsize=10,
    )

    market = format_market_value(
        profile.get("market_value"),
        profile.get("market_value_currency"),
    )

    axis.text(
        0.07,
        0.29,
        market,
        transform=axis.transAxes,
        color="#48e6a3",
        fontsize=20,
        fontweight="bold",
    )

    axis.text(
        0.07,
        0.18,
        (
            f"{safe_float(profile.get('minutes')):.0f} min"
            f" | Rating {safe_float(profile.get('weighted_rating')):.2f}"
        ),
        transform=axis.transAxes,
        color="#8fb7a2",
        fontsize=9.5,
    )


def draw_highlight_card(
    axis,
    title: str,
    row: pd.Series,
    accent: str,
):
    axis.axis("off")
    axis.set_facecolor("#071710")

    draw_panel(
        axis,
        0.03,
        0.08,
        0.94,
        0.84,
        facecolor="#0c2519",
        edgecolor=accent,
    )

    axis.text(
        0.08,
        0.81,
        title,
        transform=axis.transAxes,
        color=accent,
        fontsize=10.5,
        fontweight="bold",
    )

    axis.text(
        0.08,
        0.62,
        str(row["target_player_name"]),
        transform=axis.transAxes,
        color="white",
        fontsize=18,
        fontweight="bold",
    )

    axis.text(
        0.08,
        0.47,
        (
            f"{row.get('target_team', '-')}"
            f" | Age {safe_float(row.get('age')):.1f}"
        ),
        transform=axis.transAxes,
        color="#bed8c8",
        fontsize=9.5,
    )

    axis.text(
        0.08,
        0.28,
        format_market_value(
            row.get("market_value"),
            row.get("market_value_currency"),
        ),
        transform=axis.transAxes,
        color=accent,
        fontsize=16,
        fontweight="bold",
    )

    axis.text(
        0.92,
        0.57,
        f"{safe_float(row.get('overall_similarity_pct')):.1f}%",
        transform=axis.transAxes,
        color="#ffffff",
        fontsize=17,
        fontweight="bold",
        ha="right",
    )

    axis.text(
        0.92,
        0.42,
        "SIMILARITY",
        transform=axis.transAxes,
        color="#7ea18f",
        fontsize=8,
        fontweight="bold",
        ha="right",
    )

    axis.text(
        0.92,
        0.25,
        f"{safe_float(row.get('transfer_value_score_pct')):.1f}%",
        transform=axis.transAxes,
        color=accent,
        fontsize=17,
        fontweight="bold",
        ha="right",
    )

    axis.text(
        0.92,
        0.12,
        "TRANSFER SCORE",
        transform=axis.transAxes,
        color="#7ea18f",
        fontsize=8,
        fontweight="bold",
        ha="right",
    )


def draw_top_alternatives_table(
    axis,
    recommendations: pd.DataFrame,
    top_n: int,
):
    axis.axis("off")
    axis.set_facecolor("#071710")

    axis.text(
        0.02,
        0.97,
        "TOP TRANSFER ALTERNATIVES",
        transform=axis.transAxes,
        color="#bce5cf",
        fontsize=13,
        fontweight="bold",
        va="top",
    )

    rows = []

    for _, row in recommendations.head(
        top_n
    ).iterrows():
        rows.append(
            [
                int(row["recommendation_rank"]),
                str(row["target_player_name"]),
                str(row.get("target_team", "-")),
                f"{safe_float(row.get('age')):.1f}",
                format_market_value(
                    row.get("market_value"),
                    row.get("market_value_currency"),
                ),
                f"{safe_float(row.get('overall_similarity_pct')):.1f}%",
                f"{safe_float(row.get('affordability_score_pct')):.1f}%",
                f"{safe_float(row.get('transfer_value_score_pct')):.1f}%",
            ]
        )

    table = axis.table(
        cellText=rows,
        colLabels=[
            "#",
            "Player",
            "Team",
            "Age",
            "Market Value",
            "Similarity",
            "Affordable",
            "Transfer Score",
        ],
        loc="center",
        cellLoc="center",
        colLoc="center",
        bbox=[0.0, 0.03, 1.0, 0.86],
        colWidths=[
            0.05,
            0.21,
            0.13,
            0.07,
            0.15,
            0.13,
            0.13,
            0.13,
        ],
    )

    table.auto_set_font_size(False)
    table.set_fontsize(9)

    for (row_index, col_index), cell in (
        table.get_celld().items()
    ):
        cell.set_edgecolor("#244b39")
        cell.set_linewidth(0.8)

        if row_index == 0:
            cell.set_facecolor("#153629")
            cell.get_text().set_color("#e7fff2")
            cell.get_text().set_fontweight("bold")
        else:
            cell.set_facecolor(
                "#0d271c"
                if row_index % 2
                else "#102d21"
            )
            cell.get_text().set_color("#eafff2")

            if col_index == 1:
                cell.get_text().set_ha("left")
                cell.get_text().set_fontweight("bold")

            if col_index == 7:
                cell.get_text().set_color("#48e6a3")
                cell.get_text().set_fontweight("bold")


def draw_value_scatter(
    axis,
    recommendations: pd.DataFrame,
):
    axis.set_facecolor("#0a2117")

    x = recommendations[
        "overall_similarity_pct"
    ].astype(float)

    y = (
        recommendations["market_value"]
        .astype(float)
        .div(1_000_000)
    )

    sizes = (
        recommendations[
            "transfer_value_score_pct"
        ]
        .astype(float)
        .clip(lower=1)
        .mul(5)
    )

    axis.scatter(
        x,
        y,
        s=sizes,
        alpha=0.72,
        edgecolor="#d9fff0",
        linewidth=0.7,
    )

    for _, row in recommendations.head(
        8
    ).iterrows():
        axis.annotate(
            # RİSK OLABİLİR BURADA KONTROL YAPMADIM İKİNCİ KELİME YOKSSA PATLAYABİLİR!
            str(row["target_player_name"]).split()[1],
            (
                safe_float(
                    row["overall_similarity_pct"]
                ),
                safe_float(
                    row["market_value"]
                )
                / 1_000_000,
            ),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=5,
            color="#eafff2",
        )

    axis.set_title(
        "SIMILARITY vs MARKET VALUE",
        color="#bce5cf",
        fontsize=11,
        fontweight="bold",
        pad=12,
    )

    axis.set_xlabel(
        "Overall Similarity (%)",
        color="#b8d8c7",
        fontsize=9,
    )
    axis.set_ylabel(
        "Market Value (EUR M)",
        color="#b8d8c7",
        fontsize=9,
    )

    axis.tick_params(
        colors="#88aa98",
        labelsize=8,
    )

    axis.grid(
        linestyle="--",
        alpha=0.22,
    )

    for spine in axis.spines.values():
        spine.set_color("#315343")


def create_transfer_report(
    target_profile: pd.Series,
    recommendations: pd.DataFrame,
    output_path: Path,
    table_top_n: int = 10,
):
    if recommendations.empty:
        raise ValueError(
            "Transfer Önerisi bulunamadı."
        )

    most_similar = (
        recommendations.sort_values(
            "overall_similarity_pct",
            ascending=False,
        )
        .iloc[0]
    )

    best_value = (
        recommendations.sort_values(
            "transfer_value_score_pct",
            ascending=False,
        )
        .iloc[0]
    )

    cheapest = (
        recommendations.dropna(
            subset=["market_value"]
        )
        .sort_values(
            [
                "market_value",
                "overall_similarity_pct",
            ],
            ascending=[True, False],
        )
        .iloc[0]
    )

    figure = plt.figure(
        figsize=(17, 12),
        facecolor="#06170f",
    )

    grid = GridSpec(
        3,
        3,
        figure=figure,
        height_ratios=[0.75, 0.85, 1.8],
        width_ratios=[1.0, 1.0, 1.0],
        hspace=0.18,
        wspace=0.12,
        top=0.90,
        bottom=0.05,
        left=0.04,
        right=0.96,
    )

    figure.text(
        0.04,
        0.965,
        "TRANSFER RECOMMENDATION REPORT",
        color="#8be0b5",
        fontsize=13,
        fontweight="bold",
        va="top",
    )

    figure.text(
        0.04,
        0.925,
        f"Alternatives for {target_profile['player_name']}",
        color="white",
        fontsize=27,
        fontweight="bold",
        va="top",
    )

    figure.text(
        0.96,
        0.93,
        (
            "Similarity + Affordability + "
            "Age + Sample Confidence"
        ),
        color="#89aa98",
        fontsize=9.5,
        ha="right",
    )

    target_axis = figure.add_subplot(
        grid[0, 0]
    )
    similar_axis = figure.add_subplot(
        grid[0, 1]
    )
    value_axis = figure.add_subplot(
        grid[0, 2]
    )

    draw_target_card(
        target_axis,
        target_profile,
    )

    draw_highlight_card(
        similar_axis,
        "MOST SIMILAR",
        most_similar,
        accent="#4dabf7",
    )

    draw_highlight_card(
        value_axis,
        "BEST TRANSFER VALUE",
        best_value,
        accent="#48e6a3",
    )

    cheapest_axis = figure.add_subplot(
        grid[1, 0]
    )
    scatter_axis = figure.add_subplot(
        grid[1, 1:]
    )

    draw_highlight_card(
        cheapest_axis,
        "CHEAPEST VALID ALTERNATIVE",
        cheapest,
        accent="#ffd166",
    )

    draw_value_scatter(
        scatter_axis,
        recommendations,
    )

    table_axis = figure.add_subplot(
        grid[2, :]
    )

    draw_top_alternatives_table(
        table_axis,
        recommendations,
        top_n=table_top_n,
    )

    figure.text(
        0.5,
        0.017,
        (
            "Market values are used for decision support only. "
            "The model does not yet include wages, contract length, "
            "league strength or tactical fit."
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
        "--profiles",
        type=Path,
        default=DEFAULT_PROFILES,
    )

    parser.add_argument(
        "--transfer-dir",
        type=Path,
        default=DEFAULT_TRANSFER_DIR,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )

    parser.add_argument(
        "--table-top-n",
        type=int,
        default=10,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    profiles = pd.read_csv(
        args.profiles,
        low_memory=False,
    )

    player_name = resolve_player_name(
        profiles,
        args.player,
    )

    target_profile = get_player_profile(
        profiles,
        player_name,
    )

    transfer_csv = (
        args.transfer_dir
        / (
            f"{slugify(player_name)}"
            "_transfer_alternatives.csv"
        )
    )

    if not transfer_csv.exists():
        raise FileNotFoundError(
            f"Transfer CSV bulunamadÄ±: {transfer_csv}\n"
            "Ãnce rank_transfer_alternatives Ã§alÄ±ÅtÄ±r."
        )

    recommendations = pd.read_csv(
        transfer_csv,
        low_memory=False,
    )

    output_path = (
        args.output_dir
        / (
            f"{slugify(player_name)}"
            "_transfer_report.png"
        )
    )

    create_transfer_report(
        target_profile,
        recommendations,
        output_path,
        table_top_n=args.table_top_n,
    )

    print(
        f"Transfer raporu olusturuldu: {output_path}"
    )


if __name__ == "__main__":
    main()
