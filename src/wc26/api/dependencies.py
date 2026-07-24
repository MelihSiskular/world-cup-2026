"""FastAPI dependencies for WC26 application services."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from fastapi import Request

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


def _get_runtime_catalog(
    request: Request,
) -> TransferDataCatalog | None:
    """Return the startup-loaded catalog when available."""

    catalog = getattr(
        request.app.state,
        "transfer_data_catalog",
        None,
    )

    if isinstance(
        catalog,
        TransferDataCatalog,
    ):
        return catalog

    return None


def get_player_profile_runner(
    request: Request,
) -> PlayerProfileRunner:
    """Return the configured player-profile service."""

    catalog = _get_runtime_catalog(request)

    if catalog is None:
        return get_player_profile

    return create_catalog_player_profile_runner(catalog)


def get_player_search_runner(
    request: Request,
) -> PlayerSearchRunner:
    """Return the configured player-search service."""

    catalog = _get_runtime_catalog(request)

    if catalog is None:
        return search_players

    return create_catalog_player_search_runner(catalog)


def get_transfer_dataset_paths(
    request: Request,
) -> TransferDatasetPaths:
    """Return application-configured dataset paths."""

    dataset_paths = getattr(
        request.app.state,
        "transfer_dataset_paths",
        None,
    )

    if isinstance(
        dataset_paths,
        TransferDatasetPaths,
    ):
        return dataset_paths

    return TransferDatasetPaths()


def get_transfer_analysis_runner(
    request: Request,
) -> TransferAnalysisRunner:
    """Return the configured transfer-analysis service."""

    catalog = _get_runtime_catalog(request)

    if catalog is None:
        return run_transfer_analysis

    return create_catalog_transfer_analysis_runner(catalog)


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
