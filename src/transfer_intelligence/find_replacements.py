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
from wc26.analytics.transfer_intelligence.explanations import (
    build_reason as build_reason,
)
from wc26.analytics.transfer_intelligence.explanations import (
    classify_candidate as classify_candidate,
)
from wc26.analytics.transfer_intelligence.explanations import (
    dominant_heatmap_zone as dominant_heatmap_zone,
)
from wc26.analytics.transfer_intelligence.explanations import (
    heatmap_difference_reason as heatmap_difference_reason,
)
from wc26.analytics.transfer_intelligence.explanations import (
    recommendation_strength as recommendation_strength,
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
from wc26.analytics.transfer_intelligence.recommendations import (
    filter_for_mode as filter_for_mode,
)
from wc26.analytics.transfer_intelligence.recommendations import (
    generate_mode_results as generate_mode_results,
)
from wc26.analytics.transfer_intelligence.reporting import (
    print_report as print_report,
)
from wc26.analytics.transfer_intelligence.scoring import (
    calculate_age_suitability as calculate_age_suitability,
)
from wc26.analytics.transfer_intelligence.scoring import (
    calculate_market_value_advantage as calculate_market_value_advantage,
)
from wc26.analytics.transfer_intelligence.scoring import (
    calculate_mode_score as calculate_mode_score,
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
    format_market_value as format_market_value,
)
from wc26.analytics.transfer_intelligence.utils import (
    format_optional_score as format_optional_score,
)
from wc26.analytics.transfer_intelligence.utils import (
    normalize_text as normalize_text,
)
from wc26.analytics.transfer_intelligence.utils import (
    safe_float as safe_float,
)
from wc26.analytics.transfer_intelligence.utils import (
    slugify,
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
