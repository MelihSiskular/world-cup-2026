"""Console entrypoint for transfer intelligence."""

from __future__ import annotations

from pathlib import Path

from wc26.analytics.transfer_intelligence.cli import parse_args
from wc26.analytics.transfer_intelligence.exporting import (
    export_transfer_csv,
)
from wc26.analytics.transfer_intelligence.reporting import (
    print_transfer_report,
)
from wc26.analytics.transfer_intelligence.service import (
    TransferAnalysisRequest,
    run_transfer_analysis,
)


def main() -> None:
    """Run transfer intelligence from command-line arguments."""

    args = parse_args()

    request = TransferAnalysisRequest(
        player=args.player,
        features=Path(args.features),
        similarity=Path(args.similarity),
        heatmap_similarity=Path(args.heatmap_similarity),
        heatmap_profiles=Path(args.heatmap_profiles),
        minimum_minutes=args.minimum_minutes,
        minimum_role_confidence=args.minimum_role_confidence,
        maximum_market_value=args.maximum_market_value,
        neutral_heatmap_score=args.neutral_heatmap_score,
    )

    result = run_transfer_analysis(request)

    print_transfer_report(
        result,
        args.top_n,
    )

    output_dir = Path(args.output_dir)

    export_transfer_csv(
        result,
        output_dir,
    )

    print()
    print(f"Output directory: {output_dir}")


__all__ = [
    "main",
]
