# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd



"""
RUN

python -m src.player_roles.build_player_roles
"""


DEFAULT_ARCHETYPES = Path(
    "data/processed/player_archetypes/player_archetypes.csv"
)

DEFAULT_SPATIAL = Path(
    "data/processed/player_positioning/player_spatial_profiles.csv"
)

DEFAULT_OUTPUT = Path(
    "data/processed/player_roles/player_roles.csv"
)


def safe_float(value, default=np.nan) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def lateral_label(row: pd.Series) -> str:
    y = safe_float(row.get("weighted_mean_y"))

    if pd.isna(y):
        return "Unknown Lane"
    if y < 20:
        return "Right Wide"
    if y < 40:
        return "Right Half-Space"
    if y < 60:
        return "Central Lane"
    if y < 80:
        return "Left Half-Space"
    return "Left Wide"


def vertical_label(row: pd.Series) -> str:
    x = safe_float(row.get("weighted_mean_x"))

    if pd.isna(x):
        return "Unknown Height"
    if x < 20:
        return "Goal Area"
    if x < 35:
        return "Deep Build-Up"
    if x < 50:
        return "Deeper Half"
    if x < 65:
        return "Advanced Middle Third"
    if x < 78:
        return "Final Third"
    return "High Attacking Zone"


def mobility_label(row: pd.Series) -> str:
    spread = safe_float(row.get("spatial_spread"))

    if pd.isna(spread):
        return "Unknown Mobility"
    if spread < 4:
        return "Highly Fixed"
    if spread < 7:
        return "Positionally Stable"
    if spread < 11:
        return "Mobile"
    return "Free-Roaming"


def side_from_y(y: float) -> str:
    if pd.isna(y):
        return ""
    if y < 40:
        return "Right"
    if y > 60:
        return "Left"
    return "Central"


def build_spatial_role(row: pd.Series) -> str:
    position = str(row.get("position"))
    x = safe_float(row.get("weighted_mean_x"))
    y = safe_float(row.get("weighted_mean_y"))
    wide_share = safe_float(
        row.get("wide_lane_match_share"),
        0.0,
    )
    half_share = safe_float(
        row.get("half_space_match_share"),
        0.0,
    )
    central_share = safe_float(
        row.get("central_lane_match_share"),
        0.0,
    )
    attacking_share = safe_float(
        row.get("attacking_third_match_share"),
        0.0,
    )
    defensive_share = safe_float(
        row.get("defensive_third_match_share"),
        0.0,
    )
    spread = safe_float(
        row.get("spatial_spread"),
        0.0,
    )
    side = side_from_y(y)

    if position == "G":
        if x >= 18:
            return "Aggressive Sweeper Zone"
        if x >= 14:
            return "Advanced Goalkeeper Zone"
        return "Deep Goalkeeper Zone"

    if position == "D":
        if wide_share >= 0.45 or y < 25 or y > 75:
            if x >= 55 or attacking_share >= 0.35:
                return f"{side} Overlapping Channel"
            if x >= 45:
                return f"{side} Full-Back Channel"
            return f"{side} Defensive Full-Back Zone"

        if half_share >= 0.45:
            if x >= 48:
                return f"{side} Inverted Defensive Lane"
            return f"{side} Wide Centre-Back Lane"

        if central_share >= 0.45:
            if x >= 48:
                return "High Central Defensive Line"
            if defensive_share >= 0.55:
                return "Deep Central Defensive Line"
            return "Central Centre-Back Zone"

        return "Hybrid Defensive Zone"

    if position == "M":
        if wide_share >= 0.45 or y < 22 or y > 78:
            if x >= 62:
                return f"{side} Advanced Wide Zone"
            return f"{side} Wide Midfield Zone"

        if half_share >= 0.45 or 20 <= y < 40 or 60 < y <= 80:
            if x >= 62:
                return f"{side} Advanced Half-Space"
            if x >= 48:
                return f"{side} Half-Space"
            return f"{side} Deep Half-Space"

        if central_share >= 0.45 or 40 <= y <= 60:
            if x < 45:
                return "Deep Central Zone"
            if x < 58:
                if spread >= 10:
                    return "Central Roaming Zone"
                return "Central Build-Up Zone"
            if spread >= 10:
                return "Advanced Roaming Zone"
            return "Advanced Central Zone"

        return "Hybrid Midfield Zone"

    if position == "F":
        if wide_share >= 0.45 or y < 22 or y > 78:
            if x >= 68:
                return f"{side} High Wide Zone"
            return f"{side} Wide Forward Zone"

        if half_share >= 0.45 or 20 <= y < 40 or 60 < y <= 80:
            if x >= 68:
                return f"{side} Inside-Forward Zone"
            return f"{side} Creative Half-Space"

        if central_share >= 0.45 or 40 <= y <= 60:
            if x >= 70:
                return "Penalty-Box Central Zone"
            if x < 57 and spread >= 8:
                return "False-Nine Zone"
            if x < 60:
                return "Deep Central Forward Zone"
            return "Central Striker Zone"

        return "Hybrid Forward Zone"

    return "Unknown Spatial Role"


def build_final_role(row: pd.Series) -> tuple[str, list[str]]:
    position = str(row.get("position"))
    archetype = str(row.get("archetype"))
    spatial = str(row.get("spatial_role"))

    x = safe_float(row.get("weighted_mean_x"))
    y = safe_float(row.get("weighted_mean_y"))
    wide_share = safe_float(
        row.get("wide_lane_match_share"),
        0.0,
    )
    half_share = safe_float(
        row.get("half_space_match_share"),
        0.0,
    )
    central_share = safe_float(
        row.get("central_lane_match_share"),
        0.0,
    )
    spread = safe_float(
        row.get("spatial_spread"),
        0.0,
    )
    side = side_from_y(y)

    reasons = [
        f"Statistical archetype: {archetype}",
        f"Spatial profile: {spatial}",
    ]

    if position == "G":
        if archetype == "Traditional Shot Stopper":
            if x >= 16:
                role = "Proactive Shot-Stopping Goalkeeper"
            else:
                role = "Traditional Shot-Stopping Goalkeeper"

        elif archetype == "Commanding Goalkeeper":
            if x >= 17:
                role = "Commanding Sweeper Keeper"
            else:
                role = "Commanding Goalkeeper"

        elif archetype == "Balanced Goalkeeper":
            if x >= 17:
                role = "Balanced Sweeper Keeper"
            else:
                role = "Balanced Goalkeeper"
        else:
            role = archetype

    elif position == "D":
        is_wide = (
            wide_share >= 0.40
            or "Full-Back" in spatial
            or "Overlapping" in spatial
        )
        is_inverted = (
            "Inverted" in spatial
            or (
                half_share >= 0.45
                and not is_wide
            )
        )

        if archetype == "Attacking Full-Back":
            if is_inverted:
                role = f"{side} Inverted Attacking Full-Back"
            elif x >= 55:
                role = f"{side} Overlapping Full-Back"
            else:
                role = f"{side} Attacking Full-Back"

        elif archetype in {
            "Ball-Carrying Defender",
            "Progressive Defender",
        }:
            if is_wide:
                role = f"{side} Progressive Full-Back"
            elif is_inverted:
                role = f"{side} Wide Centre-Back"
            elif archetype == "Ball-Carrying Defender":
                role = "Ball-Carrying Centre-Back"
            else:
                role = "Progressive Centre-Back"

        elif archetype == "Safe-Possession Defender":
            if is_wide:
                role = f"{side} Possession Full-Back"
            else:
                role = "Safe Ball-Playing Centre-Back"

        elif archetype == "Aerial Enforcer":
            role = (
                f"{side} Aerial Full-Back"
                if is_wide
                else "Aerial-Dominant Centre-Back"
            )

        elif archetype.startswith("Defensive Stopper"):
            role = (
                f"{side} Defensive Full-Back"
                if is_wide
                else "Aggressive Stopper Centre-Back"
            )
        else:
            role = archetype

    elif position == "M":
        is_wide = (
            wide_share >= 0.40
            or "Wide Zone" in spatial
        )
        is_half_space = (
            half_share >= 0.40
            or "Half-Space" in spatial
        )
        is_deep = x < 48
        is_advanced = x >= 58
        is_roaming = spread >= 10

        if archetype == "Wide Creator":
            if is_wide:
                role = f"{side} Touchline Creator"
            elif is_half_space:
                role = f"{side} Half-Space Creator"
            elif is_advanced:
                role = "Advanced Central Playmaker"
            else:
                role = "Creative Central Midfielder"

        elif archetype == "Tempo Controller":
            if is_deep:
                role = "Deep-Lying Playmaker"
            elif is_roaming:
                role = "Roaming Tempo Controller"
            else:
                role = "Central Tempo Controller"

        elif archetype == "Ball-Winning Midfielder":
            if is_deep:
                role = "Holding Ball-Winner"
            elif is_roaming:
                role = "Box-to-Box Ball-Winner"
            else:
                role = "Central Ball-Winning Midfielder"

        elif archetype == "Goal-Threat Midfielder":
            if is_wide:
                role = f"{side} Goal-Threat Wide Midfielder"
            elif is_half_space:
                role = f"{side} Goal-Threat Number 8"
            elif is_roaming:
                role = "Box-to-Box Goal-Threat Midfielder"
            else:
                role = "Advanced Goal-Threat Midfielder"

        elif archetype == "Press-Resistant Carrier":
            if is_half_space:
                role = f"{side} Press-Resistant Number 8"
            elif is_roaming:
                role = "Roaming Ball-Carrying Midfielder"
            else:
                role = "Central Press-Resistant Carrier"

        elif archetype == "Possession-Secure Midfielder":
            if is_deep:
                role = "Possession-Secure Holding Midfielder"
            elif is_half_space:
                role = f"{side} Possession-Secure Number 8"
            else:
                role = "Possession-Secure Central Midfielder"
        else:
            role = archetype

    elif position == "F":
        is_wide = (
            wide_share >= 0.40
            or "Wide Zone" in spatial
        )
        is_half_space = (
            half_share >= 0.40
            or "Inside-Forward" in spatial
            or "Half-Space" in spatial
        )
        is_central = (
            central_share >= 0.40
            or "Central" in spatial
            or "Penalty-Box" in spatial
        )

        if archetype == "Poacher - Shooting Volume":
            if is_wide or is_half_space:
                role = f"{side} Elite Inside Forward"
            elif x < 60 and spread >= 8:
                role = "Complete False Nine"
            else:
                role = "High-Volume Elite Poacher"

        elif archetype == "Poacher - Ball Security":
            if is_wide:
                role = f"{side} Direct Wide Forward"
            elif x < 60:
                role = "Secure Link Striker"
            else:
                role = "Possession-Secure Poacher"

        elif archetype == "Dribbling Forward":
            if is_wide:
                role = f"{side} Touchline Dribbler"
            elif is_half_space:
                role = f"{side} Inside Forward"
            elif x < 60:
                role = "Dribbling False Nine"
            else:
                role = "Mobile Dribbling Striker"

        elif archetype == "Target Forward":
            if is_wide:
                role = f"{side} Wide Target Forward"
            elif x < 60:
                role = "Deep Target Forward"
            else:
                role = "Central Target Forward"
        else:
            role = archetype

    else:
        role = archetype

    reasons.append(
        f"Mean position: X={x:.1f}, Y={y:.1f}"
    )
    reasons.append(
        f"Wide={wide_share:.2f}, "
        f"Half-space={half_share:.2f}, "
        f"Central={central_share:.2f}"
    )
    reasons.append(
        f"Spatial spread={spread:.2f}"
    )

    return role, reasons


def role_confidence(row: pd.Series) -> float:
    spatial_reliability = safe_float(
        row.get("spatial_reliability"),
        0.0,
    )
    position_consistency = safe_float(
        row.get("position_consistency_score"),
        0.0,
    )
    matches = safe_float(
        row.get("matches_with_position_data"),
        0.0,
    )
    points = safe_float(
        row.get("total_position_points"),
        0.0,
    )

    sample_score = min(matches / 5.0, 1.0)
    point_score = min(points / 250.0, 1.0)

    confidence = (
        spatial_reliability * 0.50
        + position_consistency * 0.15
        + sample_score * 0.20
        + point_score * 0.15
    )

    return round(
        float(np.clip(confidence, 0, 1) * 100),
        2,
    )


def build_player_roles(
    archetypes: pd.DataFrame,
    spatial: pd.DataFrame,
    minimum_spatial_reliability: float,
) -> pd.DataFrame:
    merged = archetypes.merge(
        spatial,
        on=["player_id"],
        how="inner",
        suffixes=("_archetype", "_spatial"),
    )

    if merged.empty:
        raise ValueError(
            "Archetype ve spatial tabloları birleşmedi."
        )

    # Merge sonrası ortak kolonları sadeleştir.
    for column in [
        "player_name",
        "position",
        "national_team_name",
    ]:
        left = f"{column}_archetype"
        right = f"{column}_spatial"

        if left in merged.columns:
            merged[column] = merged[left]
        elif right in merged.columns:
            merged[column] = merged[right]

    merged = merged[
        merged["spatial_reliability"].ge(
            minimum_spatial_reliability
        )
    ].copy()

    merged["spatial_role"] = merged.apply(
        build_spatial_role,
        axis=1,
    )

    role_results = merged.apply(
        build_final_role,
        axis=1,
    )

    merged["final_role"] = [
        result[0]
        for result in role_results
    ]

    merged["role_reason"] = [
        " | ".join(result[1])
        for result in role_results
    ]

    merged["lateral_profile"] = merged.apply(
        lateral_label,
        axis=1,
    )

    merged["vertical_profile"] = merged.apply(
        vertical_label,
        axis=1,
    )

    merged["mobility_profile"] = merged.apply(
        mobility_label,
        axis=1,
    )

    merged["role_confidence_pct"] = merged.apply(
        role_confidence,
        axis=1,
    )

    output_columns = [
        "player_id",
        "player_name",
        "national_team_name",
        "position",
        "age",
        "minutes",
        "weighted_rating",
        "market_value",
        "market_value_currency",
        "archetype_cluster",
        "archetype",
        "spatial_role",
        "final_role",
        "lateral_profile",
        "vertical_profile",
        "mobility_profile",
        "role_confidence_pct",
        "matches_with_position_data",
        "total_position_points",
        "weighted_mean_x",
        "weighted_mean_y",
        "weighted_x_std",
        "weighted_y_std",
        "spatial_spread",
        "defensive_third_match_share",
        "middle_third_match_share",
        "attacking_third_match_share",
        "right_wide_match_share",
        "right_half_space_match_share",
        "central_lane_match_share",
        "left_half_space_match_share",
        "left_wide_match_share",
        "wide_lane_match_share",
        "half_space_match_share",
        "position_consistency_score",
        "spatial_reliability",
        "role_reason",
    ]

    output_columns = [
        column
        for column in output_columns
        if column in merged.columns
    ]

    return (
        merged[output_columns]
        .sort_values(
            [
                "position",
                "final_role",
                "role_confidence_pct",
                "minutes",
            ],
            ascending=[
                True,
                True,
                False,
                False,
            ],
        )
        .reset_index(drop=True)
    )


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--archetypes",
        type=Path,
        default=DEFAULT_ARCHETYPES,
    )

    parser.add_argument(
        "--spatial",
        type=Path,
        default=DEFAULT_SPATIAL,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    parser.add_argument(
        "--minimum-spatial-reliability",
        type=float,
        default=0.35,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    archetypes = pd.read_csv(
        args.archetypes,
        low_memory=False,
    )

    spatial = pd.read_csv(
        args.spatial,
        low_memory=False,
    )

    roles = build_player_roles(
        archetypes=archetypes,
        spatial=spatial,
        minimum_spatial_reliability=(
            args.minimum_spatial_reliability
        ),
    )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    roles.to_csv(
        args.output,
        index=False,
        encoding="utf-8-sig",
    )

    print(
        f"Yazıldı: {args.output} "
        f"({len(roles)} oyuncu)"
    )

    print()
    print("Pozisyon dağılımı:")
    print(
        roles["position"]
        .value_counts()
        .to_string()
    )

    print()
    print("En yaygın roller:")
    print(
        roles["final_role"]
        .value_counts()
        .head(25)
        .to_string()
    )

    print()
    print("Örnek oyuncular:")
    examples = [
        "Michael Olise",
        "Rodri",
        "Jude Bellingham",
        "Bukayo Saka",
        "Erling Haaland",
        "Pedri",
        "Kylian Mbappé",
    ]

    sample = roles[
        roles["player_name"].isin(examples)
    ][
        [
            "player_name",
            "position",
            "archetype",
            "spatial_role",
            "final_role",
            "weighted_mean_x",
            "weighted_mean_y",
            "spatial_spread",
            "role_confidence_pct",
        ]
    ]

    print(
        sample.to_string(index=False)
        if not sample.empty
        else "Örnek oyuncular bulunamadı."
    )


if __name__ == "__main__":
    main()