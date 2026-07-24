"""FastAPI dependencies for WC26 application services."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from wc26.analytics.transfer_intelligence.catalog import (
    TransferDataCatalog,
)
from wc26.analytics.transfer_intelligence.config import (
    DEFAULT_FEATURES,
    DEFAULT_HEATMAP_PROFILES,
    DEFAULT_HEATMAP_SIMILARITY,
    DEFAULT_SIMILARITY,
)
from wc26.analytics.transfer_intelligence.models import (
    PlayerProfileRequest,
    PlayerProfileResult,
    PlayerSearchRequest,
    PlayerSearchResult,
    TransferAnalysisRequest,
    TransferAnalysisResult,
)
from wc26.analytics.transfer_intelligence.player_profile import (
    get_player_profile,
    get_player_profile_from_dataframe,
)
from wc26.analytics.transfer_intelligence.player_search import (
    search_players,
    search_players_from_dataframe,
)
from wc26.analytics.transfer_intelligence.service import (
    run_transfer_analysis,
    run_transfer_analysis_from_catalog,
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

type PlayerSearchRunner = Callable[
    [PlayerSearchRequest],
    PlayerSearchResult,
]

type PlayerProfileRunner = Callable[
    [PlayerProfileRequest],
    PlayerProfileResult,
]


def create_catalog_player_search_runner(
    catalog: TransferDataCatalog,
) -> PlayerSearchRunner:
    """Create a player-search runner backed by a loaded catalog."""

    def runner(
        request: PlayerSearchRequest,
    ) -> PlayerSearchResult:
        return search_players_from_dataframe(
            request,
            catalog.players,
        )

    return runner


def create_catalog_player_profile_runner(
    catalog: TransferDataCatalog,
) -> PlayerProfileRunner:
    """Create a player-profile runner backed by a loaded catalog."""

    def runner(
        request: PlayerProfileRequest,
    ) -> PlayerProfileResult:
        return get_player_profile_from_dataframe(
            request,
            catalog.players,
        )

    return runner


def create_catalog_transfer_analysis_runner(
    catalog: TransferDataCatalog,
) -> TransferAnalysisRunner:
    """Create a transfer-analysis runner backed by a loaded catalog."""

    def runner(
        request: TransferAnalysisRequest,
    ) -> TransferAnalysisResult:
        return run_transfer_analysis_from_catalog(
            request,
            catalog,
        )

    return runner


def get_player_profile_runner() -> PlayerProfileRunner:
    """Return the path-based player-profile application service."""

    return get_player_profile


def get_player_search_runner() -> PlayerSearchRunner:
    """Return the path-based player-search application service."""

    return search_players


def get_transfer_dataset_paths() -> TransferDatasetPaths:
    """Return the configured transfer intelligence dataset paths."""

    return TransferDatasetPaths()


def get_transfer_analysis_runner() -> TransferAnalysisRunner:
    """Return the path-based transfer-analysis application service."""

    return run_transfer_analysis


__all__ = [
    "PlayerProfileRunner",
    "PlayerSearchRunner",
    "TransferAnalysisRunner",
    "TransferDatasetPaths",
    "create_catalog_player_profile_runner",
    "create_catalog_player_search_runner",
    "create_catalog_transfer_analysis_runner",
    "get_player_profile_runner",
    "get_player_search_runner",
    "get_transfer_analysis_runner",
    "get_transfer_dataset_paths",
]
