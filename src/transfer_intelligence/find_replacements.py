"""
Football Scouting Decision Engine v4

Scenario-specific player replacement recommendations combining:

- statistical similarity
- role fit
- average-position spatial similarity
- tournament heatmap occupation similarity
- player quality
- data reliability
- market-value advantage
- age suitability
- automatic recommendation labels
- automatic, data-driven explanation text

Run
---
python -m src.transfer_intelligence.find_replacements \
  --player "Michael Olise"
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from wc26.analytics.transfer_intelligence.candidates import (
    prepare_candidate_base as prepare_candidate_base,
)
from wc26.analytics.transfer_intelligence.config import (
    DEFAULT_FEATURES,
    DEFAULT_HEATMAP_PROFILES,
    DEFAULT_HEATMAP_SIMILARITY,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SIMILARITY,
    MODE_CONFIG,
)
from wc26.analytics.transfer_intelligence.config import (
    HEATMAP_METRIC_COLUMNS as HEATMAP_METRIC_COLUMNS,
)
from wc26.analytics.transfer_intelligence.datasets import (
    load_heatmap_profiles,
    load_heatmap_similarity,
    load_similarity,
)
from wc26.analytics.transfer_intelligence.matching import (
    attach_heatmap_profiles as attach_heatmap_profiles,
)
from wc26.analytics.transfer_intelligence.matching import (
    attach_heatmap_similarity as attach_heatmap_similarity,
)
from wc26.analytics.transfer_intelligence.matching import (
    attach_similarity as attach_similarity,
)
from wc26.analytics.transfer_intelligence.matching import (
    resolve_player,
)
from wc26.analytics.transfer_intelligence.scoring import (
    calculate_age_suitability as calculate_age_suitability,
)
from wc26.analytics.transfer_intelligence.scoring import (
    calculate_market_value_advantage as calculate_market_value_advantage,
)
from wc26.analytics.transfer_intelligence.scoring import (
    calculate_mode_score,
)
from wc26.analytics.transfer_intelligence.scoring import (
    calculate_role_fit as calculate_role_fit,
)
from wc26.analytics.transfer_intelligence.scoring import (
    calculate_spatial_similarity as calculate_spatial_similarity,
)
from wc26.analytics.transfer_intelligence.scoring import (
    same_value_score as same_value_score,
)
from wc26.analytics.transfer_intelligence.utils import (
    format_market_value,
    format_optional_score,
    safe_float,
    slugify,
)
from wc26.analytics.transfer_intelligence.utils import (
    normalize_text as normalize_text,
)


def filter_for_mode(
    candidates: pd.DataFrame,
    mode: str,
) -> pd.DataFrame:
    config = MODE_CONFIG[mode]
    result = candidates.copy()

    similarity = pd.to_numeric(
        result["statistical_similarity_pct"],
        errors="coerce",
    )

    role_fit = pd.to_numeric(
        result["role_fit_pct"],
        errors="coerce",
    )

    quality = pd.to_numeric(
        result["player_quality_score"],
        errors="coerce",
    )

    reliability = pd.to_numeric(
        result["data_reliability_score"],
        errors="coerce",
    )

    ages = pd.to_numeric(
        result["age"],
        errors="coerce",
    )

    mask = (
        similarity.ge(config["minimum_similarity"])
        & role_fit.ge(config["minimum_role_fit"])
        & quality.ge(config["minimum_quality"])
        & reliability.ge(config["minimum_reliability"])
    )

    if config["minimum_age"] is not None:
        mask &= ages.ge(config["minimum_age"])

    if config["maximum_age"] is not None:
        mask &= ages.le(config["maximum_age"])

    return result[mask].copy()


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
        key=lateral.get,
    )

    vertical_zone = max(
        vertical,
        key=vertical.get,
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
        column.replace(
            "heatmap_",
            "",
            1,
        ): value
        for column, value in row.items()
        if str(column).startswith("heatmap_")
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


def generate_mode_results(
    base_candidates: pd.DataFrame,
    mode: str,
    target_heatmap_profile: dict[str, float],
) -> pd.DataFrame:
    result = filter_for_mode(
        base_candidates,
        mode,
    )

    if result.empty:
        return result

    result[f"{mode}_score"] = calculate_mode_score(
        result,
        mode,
    )

    result["recommendation_type"] = result.apply(
        lambda row: classify_candidate(
            row,
            mode,
        ),
        axis=1,
    )

    result["recommendation_strength"] = result[f"{mode}_score"].map(recommendation_strength)

    result["why_recommended"] = result.apply(
        lambda row: build_reason(
            row,
            mode,
            target_heatmap_profile,
        ),
        axis=1,
    )

    result = result.sort_values(
        [
            f"{mode}_score",
            "role_fit_pct",
            "effective_heatmap_score_pct",
            "statistical_similarity_pct",
            "player_quality_score",
        ],
        ascending=[
            False,
            False,
            False,
            False,
            False,
        ],
    ).reset_index(drop=True)

    result[f"{mode}_rank"] = np.arange(
        1,
        len(result) + 1,
    )

    return result


def print_report(
    target: pd.Series,
    results: dict[str, pd.DataFrame],
    top_n: int,
) -> None:
    print("=" * 120)
    print("FOOTBALL SCOUTING DECISION ENGINE V4")
    print("=" * 120)
    print()
    print(f"Target Player:  {target['player_name']}")
    print(f"Position:       {target['position']}")
    print(f"Archetype:      {target['archetype']}")
    print(f"Final Role:     {target['final_role']}")
    print(f"Age:            {target['age']}")
    print(f"Market Value:   {format_market_value(target['market_value'])}")

    titles = {
        "immediate": ("IMMEDIATE REPLACEMENTS"),
        "development": ("DEVELOPMENT PROSPECTS"),
        "value": ("BEST VALUE OPTIONS"),
        "short_term": ("SHORT-TERM EXPERIENCED OPTIONS"),
    }

    for mode, title in titles.items():
        print()
        print(title)
        print("-" * 120)

        result = results[mode]

        if result.empty:
            print("No eligible candidates.")
            continue

        columns = [
            f"{mode}_rank",
            "player_name",
            "national_team_name",
            "age",
            "market_value",
            "final_role",
            "statistical_similarity_pct",
            "role_fit_pct",
            "spatial_similarity_pct",
            "heatmap_similarity_score_pct",
            "occupation_overlap_pct",
            f"{mode}_score",
            "recommendation_type",
            "why_recommended",
        ]

        display = result.head(top_n)[columns].rename(
            columns={
                "national_team_name": "team",
                "statistical_similarity_pct": ("stat_sim"),
                "spatial_similarity_pct": ("spatial_sim"),
                "heatmap_similarity_score_pct": "heatmap_sim",
                "occupation_overlap_pct": ("heatmap_overlap"),
                f"{mode}_score": ("decision_score"),
            }
        )

        formatters = {
            "age": lambda value: f"{value:.1f}",
            "market_value": format_market_value,
            "stat_sim": format_optional_score,
            "role_fit_pct": format_optional_score,
            "spatial_sim": format_optional_score,
            "heatmap_sim": format_optional_score,
            "heatmap_overlap": format_optional_score,
            "decision_score": format_optional_score,
        }

        print(
            display.to_string(
                index=False,
                formatters=formatters,
            )
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--player",
        required=True,
    )

    parser.add_argument(
        "--features",
        type=Path,
        default=DEFAULT_FEATURES,
    )

    parser.add_argument(
        "--similarity",
        type=Path,
        default=DEFAULT_SIMILARITY,
    )

    parser.add_argument(
        "--heatmap-similarity",
        type=Path,
        default=DEFAULT_HEATMAP_SIMILARITY,
    )

    parser.add_argument(
        "--heatmap-profiles",
        type=Path,
        default=DEFAULT_HEATMAP_PROFILES,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )

    parser.add_argument(
        "--minimum-minutes",
        type=float,
        default=150,
    )

    parser.add_argument(
        "--minimum-role-confidence",
        type=float,
        default=50,
    )

    parser.add_argument(
        "--maximum-market-value",
        type=float,
        default=None,
    )

    parser.add_argument(
        "--neutral-heatmap-score",
        type=float,
        default=70.0,
        help=("Neutral score assigned when a candidate has no available heatmap comparison."),
    )

    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    players = pd.read_csv(
        args.features,
        low_memory=False,
    )

    players["player_id"] = pd.to_numeric(
        players["player_id"],
        errors="coerce",
    )

    similarity = load_similarity(args.similarity)

    heatmap_similarity = load_heatmap_similarity(args.heatmap_similarity)

    heatmap_profiles = load_heatmap_profiles(args.heatmap_profiles)

    target = resolve_player(
        players,
        args.player,
    )

    (
        base_candidates,
        target_heatmap_profile,
    ) = prepare_candidate_base(
        players=players,
        similarity=similarity,
        heatmap_similarity=heatmap_similarity,
        heatmap_profiles=heatmap_profiles,
        target=target,
        minimum_minutes=args.minimum_minutes,
        minimum_role_confidence=(args.minimum_role_confidence),
        maximum_market_value=(args.maximum_market_value),
        neutral_heatmap_score=(args.neutral_heatmap_score),
    )

    results = {
        mode: generate_mode_results(
            base_candidates,
            mode,
            target_heatmap_profile,
        )
        for mode in MODE_CONFIG
    }

    args.output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    player_slug = slugify(target["player_name"])

    for mode, result in results.items():
        if result.empty:
            continue

        output_path = args.output_dir / (f"{player_slug}_{mode}_recommendations.csv")

        result.to_csv(
            output_path,
            index=False,
            encoding="utf-8-sig",
        )

    print_report(
        target,
        results,
        args.top_n,
    )

    print()
    print(f"Output directory: {args.output_dir}")


if __name__ == "__main__":
    main()
