"""Application service for transfer intelligence analysis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from wc26.analytics.transfer_intelligence.candidates import (
    prepare_candidate_base,
)
from wc26.analytics.transfer_intelligence.config import (
    MODE_CONFIG,
)
from wc26.analytics.transfer_intelligence.datasets import (
    load_heatmap_profiles,
    load_heatmap_similarity,
    load_similarity,
)
from wc26.analytics.transfer_intelligence.matching import (
    resolve_player,
)
from wc26.analytics.transfer_intelligence.recommendations import (
    generate_mode_results,
)
from wc26.analytics.transfer_intelligence.reporting import (
    print_report,
)
from wc26.analytics.transfer_intelligence.utils import (
    slugify,
)


@dataclass(frozen=True, slots=True)
class TransferAnalysisRequest:
    """Input parameters required to run transfer analysis."""

    player: str
    features: Path
    similarity: Path
    heatmap_similarity: Path
    heatmap_profiles: Path
    output_dir: Path
    minimum_minutes: float
    minimum_role_confidence: float
    maximum_market_value: float | None
    neutral_heatmap_score: float
    top_n: int


def run_transfer_analysis(
    request: TransferAnalysisRequest,
) -> None:
    players = pd.read_csv(
        request.features,
        low_memory=False,
    )

    players["player_id"] = pd.to_numeric(
        players["player_id"],
        errors="coerce",
    )

    similarity = load_similarity(request.similarity)

    heatmap_similarity = load_heatmap_similarity(request.heatmap_similarity)

    heatmap_profiles = load_heatmap_profiles(request.heatmap_profiles)

    target = resolve_player(
        players,
        request.player,
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
        minimum_minutes=request.minimum_minutes,
        minimum_role_confidence=(request.minimum_role_confidence),
        maximum_market_value=(request.maximum_market_value),
        neutral_heatmap_score=(request.neutral_heatmap_score),
    )

    results = {
        mode: generate_mode_results(
            base_candidates,
            mode,
            target_heatmap_profile,
        )
        for mode in MODE_CONFIG
    }

    request.output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    player_slug = slugify(target["player_name"])

    for mode, result in results.items():
        if result.empty:
            continue

        output_path = request.output_dir / (f"{player_slug}_{mode}_recommendations.csv")

        result.to_csv(
            output_path,
            index=False,
            encoding="utf-8-sig",
        )

    print_report(
        target,
        results,
        request.top_n,
    )

    print()
    print(f"Output directory: {request.output_dir}")


__all__ = [
    "TransferAnalysisRequest",
    "run_transfer_analysis",
]
