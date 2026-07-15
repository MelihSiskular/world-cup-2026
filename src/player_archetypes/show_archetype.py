# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_ARCHETYPES = Path(
    "data/processed/player_archetypes/player_archetypes.csv"
)

DEFAULT_SUMMARY = Path(
    "data/processed/player_archetypes/archetype_summary.csv"
)


def resolve_archetype_name(
    values: pd.Series,
    query: str,
) -> str:
    names = (
        values.dropna()
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
            f"Archetype bulunamadı: {query}"
        )

    raise ValueError(
        "Birden fazla archetype eşleşti: "
        + ", ".join(partial.head(15).tolist())
    )


def pretty_category_name(
    column: str,
) -> str:
    return (
        column.removeprefix("centroid_")
        .removeprefix("archetype_score_")
        .replace("_", " ")
        .title()
    )


def get_centroid_columns(
    summary: pd.DataFrame,
) -> list[str]:
    return [
        column
        for column in summary.columns
        if column.startswith("centroid_")
    ]


def get_score_columns(
    players: pd.DataFrame,
) -> list[str]:
    return [
        column
        for column in players.columns
        if column.startswith("archetype_score_")
    ]


def calculate_distance_to_centroid(
    members: pd.DataFrame,
    centroid_row: pd.Series,
    score_columns: list[str],
) -> pd.DataFrame:
    members = members.copy()

    usable_columns = []

    for score_column in score_columns:
        category = score_column.removeprefix(
            "archetype_score_"
        )
        centroid_column = f"centroid_{category}"

        if (
                centroid_column in centroid_row.index
                and pd.notna(centroid_row[centroid_column])
        ):
            usable_columns.append(
                (score_column, centroid_column)
            )

    if not usable_columns:
        members["distance_to_centroid"] = np.nan
        return members

    member_matrix = (
        members[
            [score for score, _ in usable_columns]
        ]
        .apply(pd.to_numeric, errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
        .to_numpy(dtype=float)
    )

    centroid_vector = np.array(
        [
            float(centroid_row[centroid])
            for _, centroid in usable_columns
        ],
        dtype=float,
    )

    members["distance_to_centroid"] = np.linalg.norm(
        member_matrix - centroid_vector,
        axis=1,
    )

    return members


def category_profile_text(
    centroid_row: pd.Series,
    centroid_columns: list[str],
    descending: bool,
    count: int,
) -> str:
    values = []

    for column in centroid_columns:
        value = centroid_row.get(column)

        if pd.isna(value):
            continue

        values.append(
            (
                pretty_category_name(column),
                float(value),
            )
        )

    values.sort(
        key=lambda item: item[1],
        reverse=descending,
    )

    selected = values[:count]

    if not selected:
        return "-"

    return "\n".join(
        f"{name:<30} {value:>7.3f}"
        for name, value in selected
    )


def rank_members(
    members: pd.DataFrame,
    ranking: str,
) -> pd.DataFrame:
    members = members.copy()

    if ranking == "representative":
        return members.sort_values(
            [
                "distance_to_centroid",
                "minutes",
            ],
            ascending=[True, False],
        )

    if ranking == "rating":
        return members.sort_values(
            [
                "weighted_rating",
                "minutes",
            ],
            ascending=[False, False],
        )

    if ranking == "minutes":
        return members.sort_values(
            [
                "minutes",
                "weighted_rating",
            ],
            ascending=[False, False],
        )

    if ranking == "market_value":
        return members.sort_values(
            [
                "market_value",
                "weighted_rating",
            ],
            ascending=[False, False],
        )

    raise ValueError(
        f"Desteklenmeyen ranking: {ranking}"
    )


def print_archetype_report(
    players: pd.DataFrame,
    summary: pd.DataFrame,
    role_query: str,
    position: str | None,
    top_n: int,
    ranking: str,
) -> None:
    role_name = resolve_archetype_name(
        players["archetype"],
        role_query,
    )

    members = players[
        players["archetype"].eq(role_name)
    ].copy()

    if position:
        members = members[
            members["position"].eq(position)
        ].copy()

    if members.empty:
        raise ValueError(
            "Seçilen archetype ve pozisyon için oyuncu yok."
        )

    position_values = (
        members["position"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    if len(position_values) > 1:
        raise ValueError(
            "Bu archetype birden fazla pozisyonda bulunuyor. "
            "--position G/D/M/F parametresi kullan."
        )

    selected_position = position_values[0]

    summary_rows = summary[
        summary["archetype"].eq(role_name)
        & summary["position"].eq(selected_position)
    ]

    if summary_rows.empty:
        raise ValueError(
            "Archetype summary kaydı bulunamadı."
        )

    summary_row = summary_rows.iloc[0]

    score_columns = get_score_columns(players)
    centroid_columns = get_centroid_columns(summary)

    members = calculate_distance_to_centroid(
        members,
        summary_row,
        score_columns,
    )

    ranked = rank_members(
        members,
        ranking,
    ).head(top_n)

    print("=" * 72)
    print("ARCHETYPE EXPLORER REPORT")
    print("=" * 72)
    print()
    print(f"Archetype:              {role_name}")
    print(f"Position Group:         {selected_position}")
    print(f"Cluster ID:             {int(summary_row['archetype_cluster'])}")
    print(f"Player Count:           {len(members)}")
    print(
        f"Representative Player:  "
        f"{summary_row.get('representative_player', '-')}"
    )
    print(f"Ranking Method:         {ranking}")

    print()
    print("ARCHETYPE STRENGTH PROFILE")
    print("-" * 72)
    print(
        category_profile_text(
            summary_row,
            centroid_columns,
            descending=True,
            count=5,
        )
    )

    print()
    print("ARCHETYPE LOWEST CATEGORIES")
    print("-" * 72)
    print(
        category_profile_text(
            summary_row,
            centroid_columns,
            descending=False,
            count=3,
        )
    )

    print()
    print("PLAYERS")
    print("-" * 72)

    display_columns = [
        "player_name",
        "national_team_name",
        "age",
        "minutes",
        "weighted_rating",
        "market_value",
        "distance_to_centroid",
    ]

    display_columns = [
        column
        for column in display_columns
        if column in ranked.columns
    ]

    display = ranked[
        display_columns
    ].rename(
        columns={
            "national_team_name": "team",
            "weighted_rating": "rating",
        }
    )

    print(
        display.to_string(
            index=False,
            formatters={
                "age": lambda value: (
                    f"{value:.1f}"
                    if pd.notna(value)
                    else "-"
                ),
                "minutes": lambda value: (
                    f"{value:.0f}"
                    if pd.notna(value)
                    else "-"
                ),
                "rating": lambda value: (
                    f"{value:.2f}"
                    if pd.notna(value)
                    else "-"
                ),
                "market_value": lambda value: (
                    f"{value:,.0f}"
                    if pd.notna(value)
                    else "-"
                ),
                "distance_to_centroid": lambda value: (
                    f"{value:.3f}"
                    if pd.notna(value)
                    else "-"
                ),
            },
        )
    )

    print()
    print("INTERPRETATION")
    print("-" * 72)
    print(
        "Centroid skorları pozisyon grubuna göre standardize edilmiştir. "
        "Pozitif değerler grup ortalamasının üzerinde, negatif değerler "
        "altında üretimi ifade eder."
    )
    print(
        "Distance to centroid değeri küçüldükçe oyuncu archetype'ın "
        "ortalama profilini daha iyi temsil eder."
    )


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--role",
        required=True,
    )

    parser.add_argument(
        "--position",
        choices=["G", "D", "M", "F"],
        default=None,
    )

    parser.add_argument(
        "--top-n",
        type=int,
        default=20,
    )

    parser.add_argument(
        "--ranking",
        choices=[
            "representative",
            "rating",
            "minutes",
            "market_value",
        ],
        default="representative",
    )

    parser.add_argument(
        "--archetypes",
        type=Path,
        default=DEFAULT_ARCHETYPES,
    )

    parser.add_argument(
        "--summary",
        type=Path,
        default=DEFAULT_SUMMARY,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    players = pd.read_csv(
        args.archetypes,
        low_memory=False,
    )

    summary = pd.read_csv(
        args.summary,
        low_memory=False,
    )

    print_archetype_report(
        players=players,
        summary=summary,
        role_query=args.role,
        position=args.position,
        top_n=args.top_n,
        ranking=args.ranking,
    )


if __name__ == "__main__":
    main()
