"""Human-readable explanations for transfer recommendations."""

from __future__ import annotations

import pandas as pd

from wc26.analytics.transfer_intelligence.utils import (
    safe_float,
)


def classify_candidate(
    row: pd.Series,
    mode: str,
) -> str:
    same_role = bool(row["same_final_role"])

    same_archetype = bool(row["same_archetype"])

    has_heatmap = bool(
        row.get(
            "has_heatmap_similarity",
            False,
        )
    )

    similarity = safe_float(row["statistical_similarity_pct"])

    role_fit = safe_float(row["role_fit_pct"])

    heatmap_fit = safe_float(row["effective_heatmap_score_pct"])

    quality = safe_float(row["player_quality_score"])

    value_advantage = safe_float(row["market_value_advantage_pct"])

    # ----------------------------------------------------------
    # Immediate replacement
    # ----------------------------------------------------------
    if mode == "immediate":
        if (
            same_role
            and role_fit >= 85
            and quality >= 65
            and (not has_heatmap or heatmap_fit >= 75)
        ):
            return "Direct tactical replacement"

        if has_heatmap and similarity >= 75 and heatmap_fit >= 80:
            return "High-continuity playing-profile alternative"

        if role_fit >= 65:
            return "Strong tactical alternative"

        return "Adaptable first-team option"

    # ----------------------------------------------------------
    # Development prospect
    # ----------------------------------------------------------
    if mode == "development":
        if same_role and role_fit >= 75:
            return "Long-term direct replacement"

        if similarity >= 60 and same_archetype:
            return "High-upside statistical prospect"

        if has_heatmap and heatmap_fit >= 85:
            return "Developmental occupation-profile match"

        return "Long-term tactical project"

    # ----------------------------------------------------------
    # Value alternative
    # ----------------------------------------------------------
    if mode == "value":
        if same_role and value_advantage >= 65:
            return "Best-value direct replacement"

        if has_heatmap and heatmap_fit >= 85 and value_advantage >= 60:
            return "High-value occupation-profile match"

        if value_advantage >= 80:
            return "Low-cost adaptable option"

        return "Balanced value alternative"

    # ----------------------------------------------------------
    # Short-term experienced option
    # ----------------------------------------------------------
    if mode == "short_term":
        if same_role and role_fit >= 75:
            return "Experienced direct replacement"

        if same_archetype and similarity >= 55:
            return "Experienced profile match"

        if has_heatmap and heatmap_fit >= 85:
            return "Experienced occupation-profile match"

        return "Short-term tactical alternative"

    raise ValueError(f"Unsupported recommendation mode: {mode}")


def dominant_heatmap_zone(
    profile: dict[str, float],
    prefix: str = "",
) -> tuple[str, str]:
    lateral = {
        "left wide lane": safe_float(profile.get(f"{prefix}left_wide_share")),
        "left half-space": safe_float(profile.get(f"{prefix}left_half_space_share")),
        "central lane": safe_float(profile.get(f"{prefix}central_share")),
        "right half-space": safe_float(profile.get(f"{prefix}right_half_space_share")),
        "right wide lane": safe_float(profile.get(f"{prefix}right_wide_share")),
    }

    vertical = {
        "build-up third": safe_float(profile.get(f"{prefix}build_up_share")),
        "middle third": safe_float(profile.get(f"{prefix}middle_third_share")),
        "advanced middle third": safe_float(profile.get(f"{prefix}advanced_middle_share")),
        "final third": safe_float(profile.get(f"{prefix}final_third_share")),
    }

    lateral_zone = max(
        lateral,
        key=lambda column: safe_float(lateral.get(column)),
    )

    vertical_zone = max(
        vertical,
        key=lambda column: safe_float(vertical.get(column)),
    )

    return lateral_zone, vertical_zone


def heatmap_difference_reason(
    row: pd.Series,
    target_heatmap_profile: dict[str, float],
) -> str | None:
    if not target_heatmap_profile or not bool(
        row.get(
            "has_heatmap_similarity",
            False,
        )
    ):
        return None

    candidate_profile = {
        column.removeprefix("heatmap_"): value
        for column, value in row.items()
        if isinstance(column, str) and column.startswith("heatmap_")
    }

    target_lateral, target_vertical = dominant_heatmap_zone(target_heatmap_profile)

    candidate_lateral, candidate_vertical = dominant_heatmap_zone(candidate_profile)

    if target_lateral == candidate_lateral and target_vertical == candidate_vertical:
        return f"replicates the target's {target_lateral} and {target_vertical} occupation"

    if target_lateral == candidate_lateral:
        return f"uses the same {target_lateral}, but operates more in the {candidate_vertical}"

    if target_vertical == candidate_vertical:
        return (
            f"matches the target's {target_vertical} depth with more {candidate_lateral} occupation"
        )

    return f"operates mainly in the {candidate_lateral} and {candidate_vertical}"


def build_reason(
    row: pd.Series,
    mode: str,
    target_heatmap_profile: dict[str, float],
) -> str:
    reasons: list[tuple[int, str, str]] = []

    if bool(row["same_final_role"]):
        reasons.append(
            (
                100,
                "role",
                "same final role",
            )
        )

    if bool(row["same_archetype"]):
        reasons.append(
            (
                92,
                "archetype",
                "same statistical archetype",
            )
        )

    statistical = safe_float(row["statistical_similarity_pct"])

    role_fit = safe_float(row["role_fit_pct"])

    spatial = safe_float(row["spatial_similarity_pct"])

    heatmap = safe_float(row.get("heatmap_similarity_score_pct"))

    overlap = safe_float(row["occupation_overlap_pct"])

    lateral = safe_float(row["lateral_profile_similarity_pct"])

    vertical = safe_float(row["vertical_profile_similarity_pct"])

    value = safe_float(row["market_value_advantage_pct"])

    if statistical >= 75:
        reasons.append(
            (
                88,
                "statistics",
                (f"very strong statistical similarity ({statistical:.1f}%)"),
            )
        )
    elif statistical >= 55:
        reasons.append(
            (
                74,
                "statistics",
                (f"good statistical similarity ({statistical:.1f}%)"),
            )
        )

    if role_fit >= 85:
        reasons.append(
            (
                96,
                "role",
                (f"elite tactical fit ({role_fit:.1f}%)"),
            )
        )
    elif role_fit >= 65:
        reasons.append(
            (
                82,
                "role",
                (f"strong tactical fit ({role_fit:.1f}%)"),
            )
        )

    if spatial >= 70:
        reasons.append(
            (
                76,
                "average_position",
                (f"similar average-position profile ({spatial:.1f}%)"),
            )
        )

    if bool(
        row.get(
            "has_heatmap_similarity",
            False,
        )
    ):
        if heatmap >= 90:
            reasons.append(
                (
                    94,
                    "heatmap",
                    (f"elite heatmap occupation similarity ({heatmap:.1f}%)"),
                )
            )
        elif heatmap >= 82:
            reasons.append(
                (
                    84,
                    "heatmap",
                    (f"strong heatmap occupation similarity ({heatmap:.1f}%)"),
                )
            )
        elif heatmap >= 72:
            reasons.append(
                (
                    70,
                    "heatmap",
                    (f"useful heatmap occupation similarity ({heatmap:.1f}%)"),
                )
            )

        if overlap >= 80:
            reasons.append(
                (
                    86,
                    "heatmap_overlap",
                    (f"high shared-zone occupation ({overlap:.1f}%)"),
                )
            )

        if lateral >= 90 and vertical >= 90:
            reasons.append(
                (
                    89,
                    "heatmap_structure",
                    "closely matches both lateral and vertical usage",
                )
            )

        zone_reason = heatmap_difference_reason(
            row,
            target_heatmap_profile,
        )

        if zone_reason:
            reasons.append(
                (
                    78,
                    "heatmap_zone",
                    zone_reason,
                )
            )

    if value >= 80:
        reasons.append(
            (
                91 if mode == "value" else 72,
                "market",
                "major price advantage",
            )
        )
    elif value >= 60:
        reasons.append(
            (
                76 if mode == "value" else 64,
                "market",
                "useful price advantage",
            )
        )

    if mode == "development":
        age = safe_float(
            row["age"],
            default=99,
        )

        if age <= 20:
            reasons.append(
                (
                    95,
                    "age",
                    "elite age upside",
                )
            )
        elif age <= 23:
            reasons.append(
                (
                    84,
                    "age",
                    "strong development age",
                )
            )

    if mode == "short_term":
        reliability = safe_float(row["data_reliability_score"])

        if reliability >= 65:
            reasons.append(
                (
                    88,
                    "reliability",
                    "reliable tournament sample",
                )
            )

    reasons.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    selected: list[str] = []
    used_groups: set[str] = set()

    for _, group, text in reasons:
        if group in used_groups:
            continue

        selected.append(text)
        used_groups.add(group)

        if len(selected) >= 4:
            break

    if not selected:
        selected.append("balanced profile across the decision criteria")

    return "; ".join(selected)


def recommendation_strength(
    score: float,
) -> str:
    if score >= 80:
        return "Elite"

    if score >= 72:
        return "Strong"

    if score >= 64:
        return "Good"

    if score >= 56:
        return "Moderate"

    return "Low"


__all__ = [
    "build_reason",
    "classify_candidate",
    "dominant_heatmap_zone",
    "heatmap_difference_reason",
    "recommendation_strength",
]
