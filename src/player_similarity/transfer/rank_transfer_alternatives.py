# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd



DEFAULT_BREAKDOWN_CSV = Path(
    "data/processed/player_similarity/player_similarity_breakdown_long.csv"
)
DEFAULT_PROFILES = Path(
    "data/processed/player_similarity/player_profiles.csv"
)
DEFAULT_OUTPUT_DIR = Path(
    "data/processed/player_similarity/transfer_recommendations"
)


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(text))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-zA-Z0-9]+", "_", ascii_text).strip("_").lower()


def load_breakdown(csv_path: Path) -> pd.DataFrame:
    if csv_path.exists():
        return pd.read_csv(csv_path, low_memory=False)

    raise FileNotFoundError(
        "Similarity breakdown bulunamadÄ±. Ãnce breakdown dosyasÄ±nÄ± Ã¼ret."
    )


def resolve_player_name(values: pd.Series, query: str) -> str:
    names = values.dropna().astype(str).drop_duplicates()

    exact = names[names.str.casefold().eq(query.casefold())]
    if len(exact) == 1:
        return str(exact.iloc[0])

    partial = names[
        names.str.contains(query, case=False, regex=False)
    ]

    if len(partial) == 1:
        return str(partial.iloc[0])

    if partial.empty:
        raise ValueError(f"Oyuncu bulunamadÄ±: {query}")

    raise ValueError(
        "Birden fazla oyuncu eÅleÅti: "
        + ", ".join(partial.head(10).tolist())
    )


def prepare_profiles(profiles: pd.DataFrame) -> pd.DataFrame:
    profiles = profiles.copy()

    for column in [
        "player_id",
        "age",
        "minutes",
        "weighted_rating",
        "market_value",
        "minutes_reliability",
    ]:
        if column in profiles.columns:
            profiles[column] = pd.to_numeric(
                profiles[column],
                errors="coerce",
            )

    return profiles


def calculate_affordability(
    target_value: float | None,
    candidate_value: float | None,
) -> float:
    if (
        pd.isna(target_value)
        or pd.isna(candidate_value)
        or target_value <= 0
        or candidate_value < 0
    ):
        return np.nan

    return float(
        target_value / (target_value + candidate_value)
    )


def calculate_age_score(
    target_age: float | None,
    candidate_age: float | None,
    penalty_years: float = 10.0,
) -> float:
    if pd.isna(target_age) or pd.isna(candidate_age):
        return np.nan

    age_difference = float(candidate_age) - float(target_age)

    if age_difference <= 0:
        return 1.0

    return max(0.0, 1.0 - age_difference / penalty_years)


def normalize_weights(
    similarity_weight: float,
    affordability_weight: float,
    age_weight: float,
    confidence_weight: float,
) -> dict[str, float]:
    weights = {
        "similarity": similarity_weight,
        "affordability": affordability_weight,
        "age": age_weight,
        "confidence": confidence_weight,
    }

    if any(value < 0 for value in weights.values()):
        raise ValueError("AÄÄ±rlÄ±klar negatif olamaz.")

    total = sum(weights.values())

    if total <= 0:
        raise ValueError("AÄÄ±rlÄ±klarÄ±n toplamÄ± sÄ±fÄ±rdan bÃ¼yÃ¼k olmalÄ±.")

    return {key: value / total for key, value in weights.items()}


def calculate_transfer_score(
    row: pd.Series,
    weights: dict[str, float],
) -> float:
    components = {
        "similarity": row["similarity_score"],
        "affordability": row["affordability_score"],
        "age": row["age_score"],
        "confidence": row["confidence_score"],
    }

    available = {
        key: value
        for key, value in components.items()
        if not pd.isna(value)
    }

    if not available:
        return np.nan

    weight_total = sum(weights[key] for key in available)

    return sum(
        available[key] * weights[key] / weight_total
        for key in available
    )


def build_transfer_recommendations(
    breakdown: pd.DataFrame,
    profiles: pd.DataFrame,
    player_query: str,
    minimum_similarity_pct: float,
    maximum_market_value: float | None,
    maximum_age: float | None,
    minimum_minutes: float | None,
    similarity_weight: float,
    affordability_weight: float,
    age_weight: float,
    confidence_weight: float,
    top_n: int,
) -> tuple[pd.Series, pd.DataFrame]:
    source_name = resolve_player_name(
        breakdown["source_player_name"],
        player_query,
    )

    source_rows = breakdown[
        breakdown["source_player_name"].eq(source_name)
    ].copy()

    if source_rows.empty:
        raise ValueError(f"{source_name} iÃ§in similarity sonucu yok.")

    source_player_id = source_rows.iloc[0]["source_player_id"]

    source_profile_rows = profiles[
        profiles["player_id"].eq(source_player_id)
    ]

    if source_profile_rows.empty:
        raise ValueError(f"{source_name} iÃ§in profile bulunamadÄ±.")

    source_profile = source_profile_rows.iloc[0]

    metadata_columns = [
        "player_id",
        "player_name",
        "national_team_name",
        "position",
        "age",
        "minutes",
        "minutes_reliability",
        "weighted_rating",
        "market_value",
        "market_value_currency",
    ]

    metadata_columns = [
        column for column in metadata_columns
        if column in profiles.columns
    ]

    candidates = source_rows.merge(
        profiles[metadata_columns],
        left_on="target_player_id",
        right_on="player_id",
        how="left",
    )

    candidates = candidates[
        candidates["overall_similarity_pct"].ge(
            minimum_similarity_pct
        )
    ].copy()

    if minimum_minutes is not None:
        candidates = candidates[
            candidates["minutes"].ge(minimum_minutes)
        ]

    if maximum_age is not None:
        candidates = candidates[
            candidates["age"].le(maximum_age)
        ]

    if maximum_market_value is not None:
        candidates = candidates[
            candidates["market_value"].le(maximum_market_value)
        ]

    if candidates.empty:
        raise ValueError("Filtrelerden sonra aday oyuncu kalmadÄ±.")

    target_value = source_profile.get("market_value")
    target_age = source_profile.get("age")

    candidates["similarity_score"] = (
        candidates["overall_similarity_pct"]
        .div(100)
        .clip(0, 1)
    )

    candidates["affordability_score"] = candidates["market_value"].apply(
        lambda value: calculate_affordability(target_value, value)
    )

    candidates["age_score"] = candidates["age"].apply(
        lambda value: calculate_age_score(target_age, value)
    )

    if "minutes_reliability" in candidates.columns:
        candidates["confidence_score"] = (
            candidates["minutes_reliability"]
            .clip(0, 1)
        )
    else:
        candidates["confidence_score"] = np.nan

    weights = normalize_weights(
        similarity_weight,
        affordability_weight,
        age_weight,
        confidence_weight,
    )

    candidates["transfer_value_score"] = candidates.apply(
        calculate_transfer_score,
        axis=1,
        weights=weights,
    )

    candidates["transfer_value_score_pct"] = (
        candidates["transfer_value_score"] * 100
    ).round(2)

    candidates["affordability_score_pct"] = (
        candidates["affordability_score"] * 100
    ).round(2)

    candidates["age_score_pct"] = (
        candidates["age_score"] * 100
    ).round(2)

    candidates["confidence_score_pct"] = (
        candidates["confidence_score"] * 100
    ).round(2)

    if pd.notna(target_value) and target_value > 0:
        candidates["market_value_difference"] = (
            candidates["market_value"] - float(target_value)
        )

        candidates["market_value_ratio"] = (
            candidates["market_value"] / float(target_value)
        ).round(3)

        candidates["discount_vs_target_pct"] = (
            1 - candidates["market_value"] / float(target_value)
        ).mul(100).round(2)

        candidates["is_cheaper_than_target"] = (
            candidates["market_value"].lt(float(target_value))
        )
    else:
        candidates["market_value_difference"] = np.nan
        candidates["market_value_ratio"] = np.nan
        candidates["discount_vs_target_pct"] = np.nan
        candidates["is_cheaper_than_target"] = False

    if pd.notna(target_age):
        candidates["is_younger_than_target"] = (
            candidates["age"].le(float(target_age))
        )
    else:
        candidates["is_younger_than_target"] = False

    candidates = (
        candidates.sort_values(
            [
                "transfer_value_score",
                "overall_similarity",
                "minutes",
            ],
            ascending=[False, False, False],
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
        "target_position",
        "age",
        "minutes",
        "weighted_rating",
        "market_value",
        "market_value_currency",
        "overall_similarity_pct",
        "affordability_score_pct",
        "age_score_pct",
        "confidence_score_pct",
        "transfer_value_score_pct",
        "market_value_difference",
        "market_value_ratio",
        "discount_vs_target_pct",
        "is_cheaper_than_target",
        "is_younger_than_target",
    ]

    output_columns = [
        column for column in output_columns
        if column in candidates.columns
    ]

    return source_profile, candidates[output_columns].copy()


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--player", required=True)
    parser.add_argument("--top-n", type=int, default=15)
    parser.add_argument(
        "--minimum-similarity",
        type=float,
        default=20.0,
    )
    parser.add_argument(
        "--maximum-market-value",
        type=float,
        default=None,
        help="Ãrnek: 40000000",
    )
    parser.add_argument(
        "--maximum-age",
        type=float,
        default=None,
    )
    parser.add_argument(
        "--minimum-minutes",
        type=float,
        default=None,
    )
    parser.add_argument(
        "--similarity-weight",
        type=float,
        default=0.70,
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
        "--confidence-weight",
        type=float,
        default=0.02,
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

    profiles = prepare_profiles(
        pd.read_csv(args.profiles, low_memory=False)
    )

    source_profile, recommendations = build_transfer_recommendations(
        breakdown=breakdown,
        profiles=profiles,
        player_query=args.player,
        minimum_similarity_pct=args.minimum_similarity,
        maximum_market_value=args.maximum_market_value,
        maximum_age=args.maximum_age,
        minimum_minutes=args.minimum_minutes,
        similarity_weight=args.similarity_weight,
        affordability_weight=args.affordability_weight,
        age_weight=args.age_weight,
        confidence_weight=args.confidence_weight,
        top_n=args.top_n,
    )

    player_name = str(source_profile["player_name"])

    output_path = (
        args.output_dir
        / f"{slugify(player_name)}_transfer_alternatives.csv"
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

    print()
    print(f"Target player: {player_name}")
    print(f"Target market value: {source_profile.get('market_value')}")
    print()
    print("Transfer alternatives:")

    display_columns = [
        "recommendation_rank",
        "target_player_name",
        "target_team",
        "age",
        "market_value",
        "overall_similarity_pct",
        "affordability_score_pct",
        "transfer_value_score_pct",
    ]

    display_columns = [
        column for column in display_columns
        if column in recommendations.columns
    ]

    print(recommendations[display_columns].to_string(index=False))
    print()
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
