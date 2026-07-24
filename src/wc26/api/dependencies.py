"""FastAPI dependencies for WC26 application services."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from wc26.analytics.transfer_intelligence.config import (
    DEFAULT_FEATURES,
    DEFAULT_HEATMAP_PROFILES,
    DEFAULT_HEATMAP_SIMILARITY,
    DEFAULT_SIMILARITY,
)
from wc26.analytics.transfer_intelligence.models import (
    TransferAnalysisRequest,
    TransferAnalysisResult,
)
from wc26.analytics.transfer_intelligence.service import (
    run_transfer_analysis,
)


@dataclass(frozen=True, slots=True)
class TransferDatasetPaths:
    """Server-managed dataset paths used by transfer analysis."""

    features: Path = DEFAULT_FEATURES
    similarity: Path = DEFAULT_SIMILARITY
    heatmap_similarity: Path = DEFAULT_HEATMAP_SIMILARITY
    heatmap_profiles: Path = DEFAULT_HEATMAP_PROFILES


type TransferAnalysisRunner = Callable[
    [TransferAnalysisRequest],
    TransferAnalysisResult,
]


def get_transfer_dataset_paths() -> TransferDatasetPaths:
    """Return the configured transfer intelligence dataset paths."""

    return TransferDatasetPaths()


def get_transfer_analysis_runner() -> TransferAnalysisRunner:
    """Return the transfer analysis application service."""

    return run_transfer_analysis


__all__ = [
    "TransferAnalysisRunner",
    "TransferDatasetPaths",
    "get_transfer_analysis_runner",
    "get_transfer_dataset_paths",
]
