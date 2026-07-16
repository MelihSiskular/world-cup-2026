# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

"""
RUN

python -m src.player_roles.show_role \
  --role "Advanced Central Playmaker"
  
python -m src.player_roles.show_role \
  --role "Advanced Central Playmaker" \
  --ranking rating
  
python -m src.player_roles.show_role \
  --role "Advanced Central Playmaker" \
  --ranking market_value
"""



DEFAULT_ROLES = Path(
    "data/processed/player_roles/player_roles.csv"
)


def resolve_role_name(values: pd.Series, query: str) -> str:
    roles = values.dropna().astype(str).drop_duplicates()

    exact = roles[
        roles.str.casefold().eq(query.casefold())
    ]
    if len(exact) == 1:
        return str(exact.iloc[0])

    partial = roles[
        roles.str.contains(
            query,
            case=False,
            regex=False,
        )
    ]
    if len(partial) == 1:
        return str(partial.iloc[0])

    if partial.empty:
        raise ValueError(f"Rol bulunamadı: {query}")

    raise ValueError(
        "Birden fazla rol eşleşti: "
        + ", ".join(partial.head(20).tolist())
    )


def format_market_value(value) -> str:
    if pd.isna(value):
        return "-"

    value = float(value)

    if value >= 1_000_000:
        return f"€{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"€{value / 1_000:.0f}K"
    return f"€{value:.0f}"


def weighted_average(
    dataframe: pd.DataFrame,
    value_column: str,
    weight_column: str,
) -> float:
    values = pd.to_numeric(
        dataframe[value_column],
        errors="coerce",
    )
    weights = pd.to_numeric(
        dataframe[weight_column],
        errors="coerce",
    )

    valid = values.notna() & weights.notna() & weights.gt(0)
    if not valid.any():
        return float("nan")

    return float(
        (values[valid] * weights[valid]).sum()
        / weights[valid].sum()
    )


def role_representativeness_score(
    dataframe: pd.DataFrame,
) -> pd.Series:
    confidence = pd.to_numeric(
        dataframe["role_confidence_pct"],
        errors="coerce",
    ).fillna(0)

    rating = pd.to_numeric(
        dataframe["weighted_rating"],
        errors="coerce",
    )
    rating = rating.fillna(rating.median())

    minutes = pd.to_numeric(
        dataframe["minutes"],
        errors="coerce",
    ).fillna(0)

    rating_score = rating.div(10).clip(0, 1) * 100
    minutes_score = minutes.div(600).clip(0, 1) * 100

    return (
        confidence * 0.50
        + rating_score * 0.30
        + minutes_score * 0.20
    ).round(2)


def rank_players(
    members: pd.DataFrame,
    ranking: str,
) -> pd.DataFrame:
    members = members.copy()
    members["representativeness_score"] = (
        role_representativeness_score(members)
    )

    if ranking == "representative":
        return members.sort_values(
            [
                "representativeness_score",
                "role_confidence_pct",
                "minutes",
            ],
            ascending=[False, False, False],
        )

    if ranking == "rating":
        return members.sort_values(
            ["weighted_rating", "minutes"],
            ascending=[False, False],
        )

    if ranking == "market_value":
        return members.sort_values(
            ["market_value", "weighted_rating"],
            ascending=[False, False],
        )

    if ranking == "minutes":
        return members.sort_values(
            ["minutes", "weighted_rating"],
            ascending=[False, False],
        )

    if ranking == "confidence":
        return members.sort_values(
            ["role_confidence_pct", "minutes"],
            ascending=[False, False],
        )

    raise ValueError(
        f"Desteklenmeyen ranking: {ranking}"
    )


def most_common_value(series: pd.Series) -> str:
    cleaned = series.dropna().astype(str)
    if cleaned.empty:
        return "-"
    return str(cleaned.value_counts().index[0])


def print_role_report(
    roles: pd.DataFrame,
    role_query: str,
    top_n: int,
    ranking: str,
    position: str | None,
) -> None:
    role_name = resolve_role_name(
        roles["final_role"],
        role_query,
    )

    members = roles[
        roles["final_role"].eq(role_name)
    ].copy()

    if position:
        members = members[
            members["position"].eq(position)
        ].copy()

    if members.empty:
        raise ValueError(
            "Seçilen rol ve pozisyon için oyuncu yok."
        )

    position_values = (
        members["position"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    ranked = rank_players(
        members,
        ranking,
    ).head(top_n)

    average_age = pd.to_numeric(
        members["age"],
        errors="coerce",
    ).mean()

    average_rating = pd.to_numeric(
        members["weighted_rating"],
        errors="coerce",
    ).mean()

    average_market_value = pd.to_numeric(
        members["market_value"],
        errors="coerce",
    ).mean()

    weighted_x = weighted_average(
        members,
        "weighted_mean_x",
        "total_position_points",
    )

    weighted_y = weighted_average(
        members,
        "weighted_mean_y",
        "total_position_points",
    )

    average_spread = pd.to_numeric(
        members["spatial_spread"],
        errors="coerce",
    ).mean()

    average_confidence = pd.to_numeric(
        members["role_confidence_pct"],
        errors="coerce",
    ).mean()

    print("=" * 78)
    print("ROLE EXPLORER REPORT")
    print("=" * 78)
    print()
    print(f"Role:                    {role_name}")
    print(
        "Position Group:          "
        + ", ".join(position_values)
    )
    print(f"Player Count:            {len(members)}")
    print(f"Ranking Method:          {ranking}")
    print(
        f"Common Archetype:        "
        f"{most_common_value(members['archetype'])}"
    )
    print(
        f"Common Spatial Role:     "
        f"{most_common_value(members['spatial_role'])}"
    )
    print(
        f"Common Lateral Profile:  "
        f"{most_common_value(members['lateral_profile'])}"
    )
    print(
        f"Common Vertical Profile: "
        f"{most_common_value(members['vertical_profile'])}"
    )
    print(
        f"Common Mobility Profile: "
        f"{most_common_value(members['mobility_profile'])}"
    )

    print()
    print("ROLE AVERAGES")
    print("-" * 78)
    print(f"Average Age:             {average_age:.2f}")
    print(f"Average Rating:          {average_rating:.2f}")
    print(
        f"Average Market Value:    "
        f"{format_market_value(average_market_value)}"
    )
    print(f"Average Mean X:          {weighted_x:.2f}")
    print(f"Average Mean Y:          {weighted_y:.2f}")
    print(f"Average Spatial Spread:  {average_spread:.2f}")
    print(f"Average Confidence:      {average_confidence:.2f}%")

    print()
    print("TOP PLAYERS")
    print("-" * 78)

    display_columns = [
        "player_name",
        "national_team_name",
        "age",
        "minutes",
        "weighted_rating",
        "market_value",
        "archetype",
        "spatial_role",
        "role_confidence_pct",
        "representativeness_score",
    ]

    display_columns = [
        column
        for column in display_columns
        if column in ranked.columns
    ]

    display = ranked[display_columns].rename(
        columns={
            "national_team_name": "team",
            "weighted_rating": "rating",
            "role_confidence_pct": "confidence",
            "representativeness_score": "role_score",
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
                "market_value": format_market_value,
                "confidence": lambda value: (
                    f"{value:.2f}%"
                    if pd.notna(value)
                    else "-"
                ),
                "role_score": lambda value: (
                    f"{value:.2f}"
                    if pd.notna(value)
                    else "-"
                ),
            },
        )
    )

    print()
    print("ROLE INTERPRETATION")
    print("-" * 78)
    print(
        "The role combines statistical archetype and spatial behaviour. "
        "Average X/Y values represent the role's weighted tournament-wide "
        "location profile."
    )
    print(
        "Representative ranking combines role confidence, tournament rating "
        "and sample size. It does not mean the player is objectively the best "
        "footballer in the role."
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
            "market_value",
            "minutes",
            "confidence",
        ],
        default="representative",
    )
    parser.add_argument(
        "--roles",
        type=Path,
        default=DEFAULT_ROLES,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    roles = pd.read_csv(
        args.roles,
        low_memory=False,
    )

    print_role_report(
        roles=roles,
        role_query=args.role,
        top_n=args.top_n,
        ranking=args.ranking,
        position=args.position,
    )


if __name__ == "__main__":
    main()