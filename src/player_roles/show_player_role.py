# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_ROLES = Path(
    "data/processed/player_roles/player_roles.csv"
)

DEFAULT_SIMILARITY_PARQUET = Path(
    "data/processed/player_similarity/"
    "player_similarity_breakdown_long.parquet"
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
        names.str.casefold().eq(
            query.casefold()
        )
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
            f"Oyuncu bulunamadı: {query}"
        )

    raise ValueError(
        "Birden fazla oyuncu eşleşti: "
        + ", ".join(partial.head(15).tolist())
    )


def load_similarity(
    parquet_path: Path,
    csv_path: Path,
) -> pd.DataFrame | None:
    if parquet_path.exists():
        return pd.read_parquet(parquet_path)

    if csv_path.exists():
        return pd.read_csv(
            csv_path,
            low_memory=False,
        )

    return None


def format_market_value(
    value,
    currency="EUR",
) -> str:
    if pd.isna(value):
        return "-"

    value = float(value)

    if value >= 1_000_000:
        display = f"{value / 1_000_000:.1f}M"
    elif value >= 1_000:
        display = f"{value / 1_000:.0f}K"
    else:
        display = f"{value:.0f}"

    return f"{currency or 'EUR'} {display}"


def get_same_role_members(
    roles: pd.DataFrame,
    player_row: pd.Series,
) -> pd.DataFrame:
    return roles[
        roles["final_role"].eq(
            player_row["final_role"]
        )
        & ~roles["player_id"].eq(
            player_row["player_id"]
        )
    ].copy()


def nearest_by_similarity(
    similarity: pd.DataFrame,
    player_row: pd.Series,
    role_members: pd.DataFrame,
    top_n: int,
) -> pd.DataFrame:
    member_ids = set(
        role_members["player_id"]
        .dropna()
        .tolist()
    )

    results = similarity[
        similarity["source_player_id"].eq(
            player_row["player_id"]
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


def spatial_distance(
    role_members: pd.DataFrame,
    player_row: pd.Series,
) -> pd.DataFrame:
    role_members = role_members.copy()

    features = [
        "weighted_mean_x",
        "weighted_mean_y",
        "spatial_spread",
        "wide_lane_match_share",
        "half_space_match_share",
        "central_lane_match_share",
    ]

    usable = [
        column
        for column in features
        if column in role_members.columns
        and column in player_row.index
    ]

    if not usable:
        role_members["spatial_distance"] = np.nan
        return role_members

    matrix = (
        role_members[usable]
        .apply(pd.to_numeric, errors="coerce")
    )

    player_vector = pd.to_numeric(
        player_row[usable],
        errors="coerce",
    )

    for column in usable:
        median = matrix[column].median()

        matrix[column] = (
            matrix[column].fillna(median)
        )

        if pd.isna(player_vector[column]):
            player_vector[column] = median

    # Kolon ölçeklerini kabaca eşitle.
    normalized_matrix = matrix.copy()
    normalized_player = player_vector.copy()

    for column in usable:
        std = matrix[column].std(ddof=0)

        if pd.isna(std) or std == 0:
            normalized_matrix[column] = 0.0
            normalized_player[column] = 0.0
        else:
            mean = matrix[column].mean()
            normalized_matrix[column] = (
                matrix[column] - mean
            ) / std
            normalized_player[column] = (
                player_vector[column] - mean
            ) / std

    role_members["spatial_distance"] = np.linalg.norm(
        normalized_matrix.to_numpy(dtype=float)
        - normalized_player.to_numpy(dtype=float),
        axis=1,
    )

    return role_members


def combined_role_similarity(
    role_members: pd.DataFrame,
    player_row: pd.Series,
    similarity: pd.DataFrame | None,
) -> pd.DataFrame:
    role_members = spatial_distance(
        role_members,
        player_row,
    )

    if similarity is not None:
        similarity_rows = similarity[
            similarity["source_player_id"].eq(
                player_row["player_id"]
            )
        ][
            [
                "target_player_id",
                "overall_similarity_pct",
            ]
        ].drop_duplicates(
            "target_player_id"
        )

        role_members = role_members.merge(
            similarity_rows,
            left_on="player_id",
            right_on="target_player_id",
            how="left",
        )
    else:
        role_members[
            "overall_similarity_pct"
        ] = np.nan

    max_distance = role_members[
        "spatial_distance"
    ].max()

    if (
        pd.isna(max_distance)
        or max_distance == 0
    ):
        role_members[
            "spatial_similarity_pct"
        ] = 100.0
    else:
        role_members[
            "spatial_similarity_pct"
        ] = (
            1
            - role_members[
                "spatial_distance"
            ]
            / max_distance
        ).clip(0, 1).mul(100)

    football_similarity = pd.to_numeric(
        role_members[
            "overall_similarity_pct"
        ],
        errors="coerce",
    )

    spatial_similarity = pd.to_numeric(
        role_members[
            "spatial_similarity_pct"
        ],
        errors="coerce",
    )

    role_members[
        "role_similarity_score"
    ] = np.where(
        football_similarity.notna(),
        (
            football_similarity * 0.70
            + spatial_similarity * 0.30
        ),
        spatial_similarity,
    )

    return role_members.sort_values(
        [
            "role_similarity_score",
            "role_confidence_pct",
            "minutes",
        ],
        ascending=[False, False, False],
    )


def print_player_report(
    roles: pd.DataFrame,
    similarity: pd.DataFrame | None,
    player_query: str,
    top_n: int,
) -> None:
    player_name = resolve_player_name(
        roles["player_name"],
        player_query,
    )

    player_row = roles[
        roles["player_name"].eq(
            player_name
        )
    ].iloc[0]

    members = get_same_role_members(
        roles,
        player_row,
    )

    ranked_members = combined_role_similarity(
        members,
        player_row,
        similarity,
    ).head(top_n)

    print("=" * 78)
    print("PLAYER ROLE REPORT")
    print("=" * 78)
    print()
    print(f"Player:               {player_row['player_name']}")
    print(
        f"Team:                 "
        f"{player_row.get('national_team_name', '-')}"
    )
    print(f"Position:             {player_row['position']}")
    print(f"Statistical Archetype:{' ' * 2}{player_row['archetype']}")
    print(f"Spatial Role:         {player_row['spatial_role']}")
    print(f"Final Role:           {player_row['final_role']}")
    print(
        f"Role Confidence:      "
        f"{float(player_row['role_confidence_pct']):.2f}%"
    )
    print(
        f"Market Value:         "
        f"{format_market_value(player_row.get('market_value'),player_row.get('market_value_currency'),)}"
    )

    print()
    print("SPATIAL PROFILE")
    print("-" * 78)
    print(
        f"Mean Position:        "
        f"X={float(player_row['weighted_mean_x']):.2f}, "
        f"Y={float(player_row['weighted_mean_y']):.2f}"
    )
    print(
        f"Lateral Profile:      "
        f"{player_row['lateral_profile']}"
    )
    print(
        f"Vertical Profile:     "
        f"{player_row['vertical_profile']}"
    )
    print(
        f"Mobility Profile:     "
        f"{player_row['mobility_profile']}"
    )
    print(
        f"Spatial Spread:       "
        f"{float(player_row['spatial_spread']):.2f}"
    )
    print(
        f"Wide Lane Share:      "
        f"{float(player_row['wide_lane_match_share']):.2%}"
    )
    print(
        f"Half-Space Share:     "
        f"{float(player_row['half_space_match_share']):.2%}"
    )
    print(
        f"Central Lane Share:   "
        f"{float(player_row['central_lane_match_share']):.2%}"
    )

    print()
    print("ROLE DECISION")
    print("-" * 78)
    print(
        str(player_row.get("role_reason", "-"))
        .replace(" | ", "\n")
    )

    print()
    print("CLOSEST PLAYERS IN THE SAME ROLE")
    print("-" * 78)

    if ranked_members.empty:
        print(
            "Aynı final role içinde başka oyuncu bulunamadı."
        )
        return

    display_columns = [
        "player_name",
        "national_team_name",
        "age",
        "minutes",
        "weighted_rating",
        "market_value",
        "overall_similarity_pct",
        "spatial_similarity_pct",
        "role_similarity_score",
        "role_confidence_pct",
    ]

    display_columns = [
        column
        for column in display_columns
        if column in ranked_members.columns
    ]

    display = ranked_members[
        display_columns
    ].rename(
        columns={
            "national_team_name": "team",
            "weighted_rating": "rating",
            "overall_similarity_pct": "stat_similarity",
            "spatial_similarity_pct": "spatial_similarity",
            "role_similarity_score": "role_similarity",
            "role_confidence_pct": "confidence",
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
                    format_market_value(value)
                ),
                "stat_similarity": lambda value: (
                    f"{value:.2f}%"
                    if pd.notna(value)
                    else "-"
                ),
                "spatial_similarity": lambda value: (
                    f"{value:.2f}%"
                    if pd.notna(value)
                    else "-"
                ),
                "role_similarity": lambda value: (
                    f"{value:.2f}%"
                    if pd.notna(value)
                    else "-"
                ),
                "confidence": lambda value: (
                    f"{value:.2f}%"
                    if pd.notna(value)
                    else "-"
                ),
            },
        )
    )

    print()
    print("SIMILARITY INTERPRETATION")
    print("-" * 78)
    print(
        "Role similarity combines statistical similarity (70%) and "
        "spatial similarity (30%) among players already assigned to the "
        "same final role."
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
        "--roles",
        type=Path,
        default=DEFAULT_ROLES,
    )

    parser.add_argument(
        "--similarity-parquet",
        type=Path,
        default=DEFAULT_SIMILARITY_PARQUET,
    )

    parser.add_argument(
        "--similarity-csv",
        type=Path,
        default=DEFAULT_SIMILARITY_CSV,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    roles = pd.read_csv(
        args.roles,
        low_memory=False,
    )

    similarity = load_similarity(
        args.similarity_parquet,
        args.similarity_csv,
    )

    print_player_report(
        roles=roles,
        similarity=similarity,
        player_query=args.player,
        top_n=args.top_n,
    )


if __name__ == "__main__":
    main()