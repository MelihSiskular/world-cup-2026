# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_ARCHETYPES = Path(
    "data/processed/player_archetypes/player_archetypes.csv"
)



DEFAULT_SIMILARITY_CSV = Path(
    "data/processed/player_similarity/"
    "player_similarity_breakdown_long.csv"
)


def resolve_player_name(
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
            f"Oyuncu bulunamadÄ±: {query}"
        )

    raise ValueError(
        "Birden fazla oyuncu eÅleÅti: "
        + ", ".join(partial.head(10).tolist())
    )


def load_similarity(
    csv_path: Path,
) -> pd.DataFrame | None:
    if csv_path.exists():
        return pd.read_csv(
            csv_path,
            low_memory=False,
        )

    return None


def get_score_columns(
    dataframe: pd.DataFrame,
) -> list[str]:
    return [
        column
        for column in dataframe.columns
        if column.startswith(
            "archetype_score_"
        )
    ]


def pretty_category_name(
    column: str,
) -> str:
    return (
        column.removeprefix(
            "archetype_score_"
        )
        .replace("_", " ")
        .title()
    )


def get_cluster_members(
    archetypes: pd.DataFrame,
    player_row: pd.Series,
) -> pd.DataFrame:
    return archetypes[
        archetypes["position"].eq(
            player_row["position"]
        )
        & archetypes["archetype_cluster"].eq(
            player_row["archetype_cluster"]
        )
    ].copy()


def nearest_members_by_category_profile(
    members: pd.DataFrame,
    player_row: pd.Series,
    score_columns: list[str],
    top_n: int,
) -> pd.DataFrame:
    candidates = members[
        ~members["player_id"].eq(
            player_row["player_id"]
        )
    ].copy()

    if candidates.empty:
        return candidates

    matrix = (
        candidates[score_columns]
        .apply(pd.to_numeric, errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
    )

    player_vector = (
        pd.to_numeric(
            player_row[score_columns],
            errors="coerce",
        )
        .replace([np.inf, -np.inf], np.nan)
        .fillna(0.0)
        .to_numpy(dtype=float)
    )

    distances = np.linalg.norm(
        matrix.to_numpy(dtype=float)
        - player_vector,
        axis=1,
    )

    candidates["archetype_distance"] = distances

    return (
        candidates.sort_values(
            [
                "archetype_distance",
                "minutes",
            ],
            ascending=[True, False],
        )
        .head(top_n)
    )


def nearest_members_by_similarity(
    similarity: pd.DataFrame,
    player_name: str,
    archetype_members: pd.DataFrame,
    top_n: int,
) -> pd.DataFrame:
    member_ids = set(
        archetype_members["player_id"]
        .dropna()
        .tolist()
    )

    results = similarity[
        similarity["source_player_name"].eq(
            player_name
        )
        & similarity["target_player_id"].isin(
            member_ids
        )
    ].copy()

    if results.empty:
        return results

    return (
        results.sort_values(
            [
                "overall_similarity",
                "target_minutes",
            ],
            ascending=[False, False],
        )
        .head(top_n)
    )


def format_score_section(
    player_row: pd.Series,
    score_columns: list[str],
    descending: bool,
    count: int,
) -> str:
    scores = {
        pretty_category_name(column): float(
            player_row[column]
        )
        for column in score_columns
        if pd.notna(player_row[column])
    }

    ordered = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=descending,
    )[:count]

    if not ordered:
        return "-"

    return "\n".join(
        f"{name:<28} {value:>7.3f}"
        for name, value in ordered
    )


def print_report(
    archetypes: pd.DataFrame,
    similarity: pd.DataFrame | None,
    player_query: str,
    top_n: int,
) -> None:
    player_name = resolve_player_name(
        archetypes["player_name"],
        player_query,
    )

    player_row = archetypes[
        archetypes["player_name"].eq(
            player_name
        )
    ].iloc[0]

    score_columns = get_score_columns(
        archetypes
    )

    members = get_cluster_members(
        archetypes,
        player_row,
    )

    print("=" * 62)
    print("PLAYER ARCHETYPE REPORT")
    print("=" * 62)
    print()
    print(f"Player:        {player_row['player_name']}")
    print(
        f"Team:          "
        f"{player_row.get('national_team_name', '-')}"
    )
    print(f"Position:      {player_row['position']}")
    print(f"Archetype:     {player_row['archetype']}")
    print(
        f"Cluster ID:    "
        f"{int(player_row['archetype_cluster'])}"
    )
    print(f"Cluster Size:  {len(members)}")
    print(
        f"Minutes:       "
        f"{float(player_row.get('minutes', 0)):.0f}"
    )
    print(
        f"Rating:        "
        f"{float(player_row.get('weighted_rating', 0)):.2f}"
    )

    if pd.notna(player_row.get("market_value")):
        print(
            f"Market Value:  "
            f"{float(player_row['market_value']):,.0f} "
            f"{player_row.get('market_value_currency', 'EUR')}"
        )

    print()
    print("TOP ARCHETYPE STRENGTHS")
    print("-" * 62)
    print(
        format_score_section(
            player_row,
            score_columns,
            descending=True,
            count=4,
        )
    )

    print()
    print("LOWEST ARCHETYPE SCORES")
    print("-" * 62)
    print(
        format_score_section(
            player_row,
            score_columns,
            descending=False,
            count=3,
        )
    )

    print()
    print("CLOSEST MEMBERS IN THE SAME ARCHETYPE")
    print("-" * 62)

    if similarity is not None:
        nearest = nearest_members_by_similarity(
            similarity,
            player_name,
            members,
            top_n,
        )

        if not nearest.empty:
            display = nearest[
                [
                    "target_player_name",
                    "target_team",
                    "target_minutes",
                    "overall_similarity_pct",
                ]
            ].rename(
                columns={
                    "target_player_name": "player_name",
                    "target_team": "team",
                    "target_minutes": "minutes",
                    "overall_similarity_pct": "similarity_pct",
                }
            )

            print(
                display.to_string(
                    index=False
                )
            )
            return

    nearest = nearest_members_by_category_profile(
        members,
        player_row,
        score_columns,
        top_n,
    )

    if nearest.empty:
        print("AynÄ± archetype iÃ§inde baÅka oyuncu yok.")
        return

    display_columns = [
        "player_name",
        "national_team_name",
        "minutes",
        "weighted_rating",
        "archetype_distance",
    ]

    display_columns = [
        column
        for column in display_columns
        if column in nearest.columns
    ]

    print(
        nearest[
            display_columns
        ].rename(
            columns={
                "national_team_name": "team",
            }
        ).to_string(
            index=False
        )
    )


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--player",
        required=True,
    )

    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--archetypes",
        type=Path,
        default=DEFAULT_ARCHETYPES,
    )



    parser.add_argument(
        "--similarity-csv",
        type=Path,
        default=DEFAULT_SIMILARITY_CSV,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    archetypes = pd.read_csv(
        args.archetypes,
        low_memory=False,
    )

    similarity = load_similarity(
        args.similarity_csv,
    )

    print_report(
        archetypes=archetypes,
        similarity=similarity,
        player_query=args.player,
        top_n=args.top_n,
    )


if __name__ == "__main__":
    main()