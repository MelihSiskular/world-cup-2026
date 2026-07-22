"""Command-line argument parsing for transfer intelligence."""

from __future__ import annotations

import argparse
from pathlib import Path

from wc26.analytics.transfer_intelligence.config import (
    DEFAULT_FEATURES,
    DEFAULT_HEATMAP_PROFILES,
    DEFAULT_HEATMAP_SIMILARITY,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SIMILARITY,
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


__all__ = [
    "parse_args",
]
