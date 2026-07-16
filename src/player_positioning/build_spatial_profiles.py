# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_INPUT = Path(
    "data/processed/player_positioning/"
    "player_average_positions.csv"
)

DEFAULT_OUTPUT = Path(
    "data/processed/player_positioning/"
    "player_spatial_profiles.csv"
)


def weighted_mean(
    values: pd.Series,
    weights: pd.Series,
) -> float:
    valid = (
        values.notna()
        & weights.notna()
        & weights.gt(0)
    )

    if not valid.any():
        return np.nan

    return float(
        np.average(
            values[valid].astype(float),
            weights=weights[valid].astype(float),
        )
    )


def weighted_std(
    values: pd.Series,
    weights: pd.Series,
) -> float:
    valid = (
        values.notna()
        & weights.notna()
        & weights.gt(0)
    )

    if not valid.any():
        return np.nan

    numeric_values = values[valid].astype(float)
    numeric_weights = weights[valid].astype(float)

    mean = np.average(
        numeric_values,
        weights=numeric_weights,
    )

    variance = np.average(
        (numeric_values - mean) ** 2,
        weights=numeric_weights,
    )

    return float(np.sqrt(variance))


def weighted_share(
    mask: pd.Series,
    weights: pd.Series,
) -> float:
    valid = weights.notna() & weights.gt(0)

    if not valid.any():
        return np.nan

    return float(
        weights[
            valid & mask.fillna(False)
        ].sum()
        / weights[valid].sum()
    )


def classify_longitudinal_role(
    mean_x: float,
) -> str:
    if pd.isna(mean_x):
        return "unknown"

    if mean_x < 20:
        return "deep_goal_area"
    if mean_x < 35:
        return "deep_build_up"
    if mean_x < 50:
        return "deeper_half"
    if mean_x < 65:
        return "central_advanced"
    if mean_x < 78:
        return "final_third"
    return "high_attacking_zone"


def classify_lateral_role(
    mean_y: float,
) -> str:
    if pd.isna(mean_y):
        return "unknown"

    if mean_y < 20:
        return "right_wide"
    if mean_y < 40:
        return "right_half_space"
    if mean_y < 60:
        return "central_lane"
    if mean_y < 80:
        return "left_half_space"
    return "left_wide"


def spatial_reliability(
    matches: int,
    total_points: float,
    median_points: float,
) -> float:
    """
    0-1 arasında basit güvenilirlik skoru.

    - maç sayısı: 5 maçta doygunluğa yaklaşır
    - toplam nokta: 250 noktada doygunluğa yaklaşır
    - maç başına tipik nokta: 40 noktada doygunluğa yaklaşır
    """
    match_component = min(matches / 5.0, 1.0)
    total_component = min(total_points / 250.0, 1.0)
    median_component = min(median_points / 40.0, 1.0)

    return round(
        (
            match_component * 0.35
            + total_component * 0.40
            + median_component * 0.25
        ),
        4,
    )


def build_player_profile(
    group: pd.DataFrame,
) -> dict:
    weights = pd.to_numeric(
        group["points_count"],
        errors="coerce",
    ).fillna(0.0)

    x = pd.to_numeric(
        group["normalized_x"],
        errors="coerce",
    )

    y = pd.to_numeric(
        group["normalized_y"],
        errors="coerce",
    )

    mean_x = weighted_mean(x, weights)
    mean_y = weighted_mean(y, weights)

    x_std = weighted_std(x, weights)
    y_std = weighted_std(y, weights)

    matches = int(group["event_id"].nunique())
    total_points = float(weights.sum())
    median_points = float(weights.median())

    spatial_spread = (
        float(np.sqrt(x_std**2 + y_std**2))
        if pd.notna(x_std) and pd.notna(y_std)
        else np.nan
    )

    return {
        "player_id": group["player_id"].iloc[0],
        "player_name": group["player_name"].iloc[0],
        "position": group["position"].mode().iloc[0],
        "national_team_name": group["team_name"].mode().iloc[0],

        "matches_with_position_data": matches,
        "total_position_points": int(total_points),
        "mean_points_per_match": round(
            float(weights.mean()),
            2,
        ),
        "median_points_per_match": round(
            median_points,
            2,
        ),

        "weighted_mean_x": round(mean_x, 4),
        "weighted_mean_y": round(mean_y, 4),
        "unweighted_mean_x": round(
            float(x.mean()),
            4,
        ),
        "unweighted_mean_y": round(
            float(y.mean()),
            4,
        ),
        "median_x": round(
            float(x.median()),
            4,
        ),
        "median_y": round(
            float(y.median()),
            4,
        ),

        "weighted_x_std": round(x_std, 4),
        "weighted_y_std": round(y_std, 4),
        "spatial_spread": round(
            spatial_spread,
            4,
        ),

        "defensive_third_match_share": round(
            weighted_share(
                x.lt(33.333),
                weights,
            ),
            4,
        ),
        "middle_third_match_share": round(
            weighted_share(
                x.ge(33.333) & x.lt(66.667),
                weights,
            ),
            4,
        ),
        "attacking_third_match_share": round(
            weighted_share(
                x.ge(66.667),
                weights,
            ),
            4,
        ),

        "right_wide_match_share": round(
            weighted_share(
                y.lt(20),
                weights,
            ),
            4,
        ),
        "right_half_space_match_share": round(
            weighted_share(
                y.ge(20) & y.lt(40),
                weights,
            ),
            4,
        ),
        "central_lane_match_share": round(
            weighted_share(
                y.ge(40) & y.lt(60),
                weights,
            ),
            4,
        ),
        "left_half_space_match_share": round(
            weighted_share(
                y.ge(60) & y.lt(80),
                weights,
            ),
            4,
        ),
        "left_wide_match_share": round(
            weighted_share(
                y.ge(80),
                weights,
            ),
            4,
        ),

        "wide_lane_match_share": round(
            weighted_share(
                y.lt(20) | y.ge(80),
                weights,
            ),
            4,
        ),
        "half_space_match_share": round(
            weighted_share(
                (
                    y.ge(20)
                    & y.lt(40)
                )
                | (
                    y.ge(60)
                    & y.lt(80)
                ),
                weights,
            ),
            4,
        ),

        "dominant_longitudinal_zone": (
            classify_longitudinal_role(mean_x)
        ),
        "dominant_lateral_lane": (
            classify_lateral_role(mean_y)
        ),

        "position_consistency_score": round(
            1.0 / (1.0 + spatial_spread)
            if pd.notna(spatial_spread)
            else np.nan,
            4,
        ),
        "spatial_reliability": spatial_reliability(
            matches,
            total_points,
            median_points,
        ),
    }


def build_spatial_profiles(
    dataframe: pd.DataFrame,
    minimum_points_per_match: int,
    minimum_matches: int,
) -> pd.DataFrame:
    required = {
        "event_id",
        "player_id",
        "player_name",
        "position",
        "team_name",
        "normalized_x",
        "normalized_y",
        "points_count",
    }

    missing = required.difference(
        dataframe.columns
    )

    if missing:
        raise ValueError(
            "Eksik kolonlar: "
            + ", ".join(sorted(missing))
        )

    dataframe = dataframe.copy()

    dataframe["points_count"] = pd.to_numeric(
        dataframe["points_count"],
        errors="coerce",
    )

    dataframe = dataframe[
        dataframe["points_count"].ge(
            minimum_points_per_match
        )
    ].copy()

    if dataframe.empty:
        raise ValueError(
            "Minimum points filtresinden sonra "
            "satır kalmadı."
        )

    profiles = []

    for _, group in dataframe.groupby(
        "player_id",
        sort=False,
    ):
        if (
            group["event_id"].nunique()
            < minimum_matches
        ):
            continue

        profiles.append(
            build_player_profile(group)
        )

    result = pd.DataFrame(profiles)

    if result.empty:
        raise ValueError(
            "Oyuncu spatial profile üretilemedi."
        )

    return (
        result.sort_values(
            [
                "position",
                "spatial_reliability",
                "total_position_points",
            ],
            ascending=[True, False, False],
        )
        .reset_index(drop=True)
    )


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    parser.add_argument(
        "--minimum-points-per-match",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--minimum-matches",
        type=int,
        default=1,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    dataframe = pd.read_csv(
        args.input,
        low_memory=False,
    )

    profiles = build_spatial_profiles(
        dataframe=dataframe,
        minimum_points_per_match=(
            args.minimum_points_per_match
        ),
        minimum_matches=args.minimum_matches,
    )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    profiles.to_csv(
        args.output,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        f"Yazıldı: {args.output} "
        f"({len(profiles)} oyuncu)"
    )

    print()
    print("Pozisyon dağılımı:")
    print(
        profiles["position"]
        .value_counts()
        .to_string()
    )

    print()
    print("Spatial reliability özeti:")
    print(
        profiles.groupby("position")[
            "spatial_reliability"
        ]
        .agg(["count", "mean", "median", "min", "max"])
        .round(3)
        .to_string()
    )

    print()
    print("Örnek yüksek güvenilirlikli profiller:")
    print(
        profiles.sort_values(
            "spatial_reliability",
            ascending=False,
        )[
            [
                "player_name",
                "national_team_name",
                "position",
                "matches_with_position_data",
                "weighted_mean_x",
                "weighted_mean_y",
                "dominant_longitudinal_zone",
                "dominant_lateral_lane",
                "spatial_reliability",
            ]
        ]
        .head(15)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()