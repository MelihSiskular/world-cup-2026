"""Runtime in-memory dataset catalog for transfer intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from wc26.analytics.transfer_intelligence.datasets import (
    load_heatmap_profiles,
    load_heatmap_similarity,
    load_player_features,
    load_player_tournament_summary,
    load_similarity,
)


@dataclass(frozen=True, slots=True)
class TransferDataCatalog:
    """Loaded datasets shared by transfer intelligence services."""

    players: pd.DataFrame
    similarity: pd.DataFrame
    heatmap_similarity: pd.DataFrame
    heatmap_profiles: pd.DataFrame
    player_tournament_summary: pd.DataFrame = field(default_factory=pd.DataFrame)


def load_transfer_data_catalog(
    *,
    features: Path,
    similarity: Path,
    heatmap_similarity: Path,
    heatmap_profiles: Path,
    player_tournament_summary: Path | None = None,
) -> TransferDataCatalog:
    """Load all transfer intelligence datasets into one catalog."""

    tournament_summary = (
        load_player_tournament_summary(player_tournament_summary)
        if player_tournament_summary is not None
        else pd.DataFrame()
    )

    return TransferDataCatalog(
        players=load_player_features(features),
        similarity=load_similarity(similarity),
        heatmap_similarity=load_heatmap_similarity(heatmap_similarity),
        heatmap_profiles=load_heatmap_profiles(heatmap_profiles),
        player_tournament_summary=tournament_summary,
    )


__all__ = [
    "TransferDataCatalog",
    "load_transfer_data_catalog",
]
