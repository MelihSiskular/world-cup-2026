# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_ARCHETYPES = Path(
    "data/processed/player_archetypes/player_archetypes.csv"
)



DEFAULT_BREAKDOWN_CSV = Path(
    "data/processed/player_similarity/"
    "player_similarity_breakdown_long.csv"
)

DEFAULT_OUTPUT_DIR = Path(
    "data/processed/player_archetypes/"
    "transfer_recommendations"
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


def load_breakdown(

    csv_path: Path,
) -> pd.DataFrame:

    if csv_path.exists():
        return pd.read_csv(
            csv_path,
            low_memory=False,
        )

    raise FileNotFoundError(
        "Similarity breakdown bulunamadı."
    )


def resolve_name(
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
            f"Oyuncu bulunamadı: {query}"
        )

    raise ValueError(
        "Birden fazla oyuncu eşleşti: "
        + ", ".join(partial.head(10).tolist())
    )


def normalize_weights(
    similarity_weight: float,
    affordability_weight: float,
    age_weight: float,
    archetype_weight: float,
    confidence_weight: float,
) -> dict[str, float]:
    weights = {
        "similarity": similarity_weight,
        "affordability": affordability_weight,
        "age": age_weight,
        "archetype": archetype_weight,
        "confidence": confidence_weight,
    }

    if any(value < 0 for value in weights.values()):
        raise ValueError(
            "Ağırlıklar negatif olamaz."
        )

    total = sum(weights.values())

    if total <= 0:
        raise ValueError(
            "Ağırlıkların toplamı sıfırdan büyük olmalı."
        )

    return {
        key: value / total
        for key, value in weights.items()
    }


def affordability_score(
    target_value,
    candidate_value,
) -> float:
    if (
        pd.isna(target_value)
        or pd.isna(candidate_value)
        or float(target_value) <= 0
        or float(candidate_value) < 0
    ):
        return np.nan

    return float(
        target_value
        / (
            float(target_value)
            + float(candidate_value)
        )
    )


def age_score(
    target_age,
    candidate_age,
    penalty_years: float = 10.0,
) -> float:
    if (
        pd.isna(target_age)
        or pd.isna(candidate_age)
    ):
        return np.nan

    difference = (
        float(candidate_age)
        - float(target_age)
    )

    if difference <= 0:
        return 1.0

    return max(
        0.0,
        1.0 - difference / penalty_years,
    )


def archetype_score(
    same_archetype: bool,
    same_cluster: bool,
) -> float:
    """
    Aynı cluster en güçlü eşleşme.
    Aynı isimde archetype ancak farklı cluster teorik olarak mümkün.
    """





    if same_cluster:
        return 1.0

    if same_archetype:
        return 0.85

    return 0.0


def weighted_score(
    row: pd.Series,
    weights: dict[str, float],
) -> float:
    components = {
        "similarity": row["similarity_score"],
        "affordability": row[
            "affordability_score"
        ],
        "age": row["age_score"],
        "archetype": row["archetype_score"],
        "confidence": row[
            "confidence_score"
        ],
    }

    available = {
        key: value
        for key, value in components.items()
        if not pd.isna(value)
    }

    if not available:
        return np.nan

    available_weight = sum(
        weights[key]
        for key in available
    )

    return sum(
        available[key]
        * weights[key]
        / available_weight
        for key in available
    )


def build_recommendations(
    archetypes: pd.DataFrame,
    breakdown: pd.DataFrame,
    player_query: str,
    same_archetype_only: bool,
    minimum_similarity: float,
    maximum_market_value: float | None,
    maximum_age: float | None,
    minimum_minutes: float | None,
    top_n: int,
    weights: dict[str, float],
) -> tuple[pd.Series, pd.DataFrame]:
    player_name = resolve_name(
        archetypes["player_name"],
        player_query,
    )

    target = archetypes[
        archetypes["player_name"].eq(
            player_name
        )
    ].iloc[0]

    source_rows = breakdown[
        breakdown["source_player_id"].eq(
            target["player_id"]
        )
    ].copy()

    if source_rows.empty:
        raise ValueError(
            f"{player_name} için similarity kaydı bulunamadı."
        )

    metadata_columns = [
        "player_id",
        "player_name",
        "national_team_name",
        "position",
        "age",
        "minutes",
        "weighted_rating",
        "market_value",
        "market_value_currency",
        "minutes_reliability",
        "archetype_cluster",
        "archetype",
    ]

    metadata_columns = [
        column
        for column in metadata_columns
        if column in archetypes.columns
    ]

    candidates = source_rows.merge(
        archetypes[metadata_columns],
        left_on="target_player_id",
        right_on="player_id",
        how="left",
    )

    candidates = candidates[
        candidates[
            "overall_similarity_pct"
        ].ge(minimum_similarity)
    ].copy()

    candidates[
        "same_archetype"
    ] = candidates["archetype"].eq(
        target["archetype"]
    )

    candidates[
        "same_archetype_cluster"
    ] = (
        candidates["archetype_cluster"]
        .eq(target["archetype_cluster"])
        & candidates["position"]
        .eq(target["position"])
    )

    if same_archetype_only:
        candidates = candidates[
            candidates[
                "same_archetype_cluster"
            ]
        ].copy()

    if minimum_minutes is not None:
        candidates = candidates[
            candidates["minutes"].ge(
                minimum_minutes
            )
        ]

    if maximum_age is not None:
        candidates = candidates[
            candidates["age"].le(
                maximum_age
            )
        ]

    if maximum_market_value is not None:
        candidates = candidates[
            candidates["market_value"].le(
                maximum_market_value
            )
        ]

    if candidates.empty:
        raise ValueError(
            "Filtrelerden sonra aday kalmadı."
        )

    candidates["similarity_score"] = (
        candidates["overall_similarity_pct"]
        .div(100)
        .clip(0, 1)
    )

    candidates["affordability_score"] = (
        candidates["market_value"]
        .apply(
            lambda value: affordability_score(
                target.get("market_value"),
                value,
            )
        )
    )

    candidates["age_score"] = (
        candidates["age"]
        .apply(
            lambda value: age_score(
                target.get("age"),
                value,
            )
        )
    )

    candidates["archetype_score"] = (
        candidates.apply(
            lambda row: archetype_score(
                bool(row["same_archetype"]),
                bool(
                    row[
                        "same_archetype_cluster"
                    ]
                ),
            ),
            axis=1,
        )
    )

    if (
        "minutes_reliability"
        in candidates.columns
    ):
        candidates["confidence_score"] = (
            pd.to_numeric(
                candidates[
                    "minutes_reliability"
                ],
                errors="coerce",
            )
            .clip(0, 1)
        )
    else:
        candidates["confidence_score"] = np.nan

    candidates[
        "archetype_transfer_score"
    ] = candidates.apply(
        weighted_score,
        axis=1,
        weights=weights,
    )

    for column in [
        "affordability_score",
        "age_score",
        "archetype_score",
        "confidence_score",
        "archetype_transfer_score",
    ]:
        candidates[
            f"{column}_pct"
        ] = (
            candidates[column]
            .mul(100)
            .round(2)
        )

    target_value = target.get(
        "market_value"
    )

    if (
        pd.notna(target_value)
        and float(target_value) > 0
    ):
        candidates[
            "discount_vs_target_pct"
        ] = (
            1
            - candidates["market_value"]
            / float(target_value)
        ).mul(100).round(2)

        candidates[
            "is_cheaper_than_target"
        ] = candidates["market_value"].lt(
            float(target_value)
        )
    else:
        candidates[
            "discount_vs_target_pct"
        ] = np.nan
        candidates[
            "is_cheaper_than_target"
        ] = False

    target_age = target.get("age")

    if pd.notna(target_age):
        candidates[
            "is_younger_than_target"
        ] = candidates["age"].le(
            float(target_age)
        )
    else:
        candidates[
            "is_younger_than_target"
        ] = False

    candidates = (
        candidates.sort_values(
            [
                "archetype_transfer_score",
                "overall_similarity",
                "minutes",
            ],
            ascending=[
                False,
                False,
                False,
            ],
        )
        .head(top_n)
        .reset_index(drop=True)
    )

    candidates.insert(
        0,
        "recommendation_rank",
        range(1, len(candidates) + 1),
    )

    output_columns = [
        "recommendation_rank",
        "target_player_id",
        "target_player_name",
        "target_team",
        "position",
        "archetype",
        "same_archetype",
        "same_archetype_cluster",
        "age",
        "minutes",
        "weighted_rating",
        "market_value",
        "market_value_currency",
        "overall_similarity_pct",
        "affordability_score_pct",
        "age_score_pct",
        "archetype_score_pct",
        "confidence_score_pct",
        "archetype_transfer_score_pct",
        "discount_vs_target_pct",
        "is_cheaper_than_target",
        "is_younger_than_target",
    ]

    output_columns = [
        column
        for column in output_columns
        if column in candidates.columns
    ]

    return (
        target,
        candidates[output_columns].copy(),
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
        default=15,
    )

    parser.add_argument(
        "--minimum-similarity",
        type=float,
        default=20.0,
    )

    parser.add_argument(
        "--maximum-market-value",
        type=float,
        default=None,
    )

    parser.add_argument(
        "--maximum-age",
        type=float,
        default=None,
    )

    parser.add_argument(
        "--minimum-minutes",
        type=float,
        default=180.0,
    )

    parser.add_argument(
        "--include-other-archetypes",
        action="store_true",
        help=(
            "Varsayılan olarak yalnızca aynı archetype cluster'ı "
            "kullanılır. Bu parametre diğer rolleri de dahil eder."
        ),
    )

    parser.add_argument(
        "--similarity-weight",
        type=float,
        default=0.55,
    )

    parser.add_argument(
        "--affordability-weight",
        type=float,
        default=0.20,
    )

    parser.add_argument(
        "--age-weight",
        type=float,
        default=0.08,
    )

    parser.add_argument(
        "--archetype-weight",
        type=float,
        default=0.15,
    )

    parser.add_argument(
        "--confidence-weight",
        type=float,
        default=0.02,
    )

    parser.add_argument(
        "--archetypes",
        type=Path,
        default=DEFAULT_ARCHETYPES,
    )



    parser.add_argument(
        "--breakdown-csv",
        type=Path,
        default=DEFAULT_BREAKDOWN_CSV,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    archetypes = pd.read_csv(
        args.archetypes,
        low_memory=False,
    )

    breakdown = load_breakdown(
        args.breakdown_csv,
    )

    weights = normalize_weights(
        similarity_weight=(
            args.similarity_weight
        ),
        affordability_weight=(
            args.affordability_weight
        ),
        age_weight=args.age_weight,
        archetype_weight=(
            args.archetype_weight
        ),
        confidence_weight=(
            args.confidence_weight
        ),
    )

    target, recommendations = (
        build_recommendations(
            archetypes=archetypes,
            breakdown=breakdown,
            player_query=args.player,
            same_archetype_only=(
                not args.include_other_archetypes
            ),
            minimum_similarity=(
                args.minimum_similarity
            ),
            maximum_market_value=(
                args.maximum_market_value
            ),
            maximum_age=args.maximum_age,
            minimum_minutes=(
                args.minimum_minutes
            ),
            top_n=args.top_n,
            weights=weights,
        )
    )

    output_path = (
        args.output_dir
        / (
            f"{slugify(target['player_name'])}"
            "_archetype_transfer_recommendations.csv"
        )
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    recommendations.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    print("=" * 72)
    print("ARCHETYPE TRANSFER FINDER")
    print("=" * 72)
    print()
    print(
        f"Target Player:  "
        f"{target['player_name']}"
    )
    print(
        f"Archetype:      "
        f"{target['archetype']}"
    )
    print(
        f"Position:       "
        f"{target['position']}"
    )
    print(
        f"Market Value:   "
        f"{target.get('market_value')}"
    )
    print()

    display_columns = [
        "recommendation_rank",
        "target_player_name",
        "target_team",
        "archetype",
        "age",
        "market_value",
        "overall_similarity_pct",
        "archetype_transfer_score_pct",
    ]

    print(
        recommendations[
            display_columns
        ].to_string(index=False)
    )

    print()
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()

# Michael Olise gibi bir Wide Creator arıyorum.
# Aynı rolü oynayan, istatistiksel olarak benzeyen ve daha uygun maliyetli kim var?

"""
Temel Kullanım

python -m src.player_archetypes.archetype_transfer_finder \
  --player "Michael Olise"    
"""

"""
Bütçe Filtresi
c
"""

"""
Genç Oyuncu Arama
python -m src.player_archetypes.archetype_transfer_finder \
  --player "Michael Olise" \
  --maximum-age 24 \
  --minimum-minutes 180
"""