"""Tests for the typed WC26 API runtime state."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from wc26.analytics.transfer_intelligence.catalog import (
    TransferDataCatalog,
)
from wc26.api.runtime import ApiRuntimeState
from wc26.api.settings import ApiSettings


def _catalog() -> TransferDataCatalog:
    """Build a minimal in-memory transfer catalog."""

    return TransferDataCatalog(
        players=pd.DataFrame(
            {
                "player_id": [978838],
                "player_name": ["Michael Olise"],
            }
        ),
        similarity=pd.DataFrame(),
        heatmap_similarity=pd.DataFrame(),
        heatmap_profiles=pd.DataFrame(),
    )


def test_runtime_state_exposes_settings_and_dataset_paths() -> None:
    settings = ApiSettings(
        environment="test",
    )

    runtime = ApiRuntimeState(
        settings=settings,
    )

    assert runtime.settings is settings
    assert runtime.dataset_paths is settings.dataset_paths
    assert runtime.started_at is None
    assert runtime.catalog_loaded_at is None
    assert runtime.transfer_data_catalog is None
    assert runtime.is_ready is False


def test_runtime_state_tracks_catalog_lifecycle() -> None:
    runtime = ApiRuntimeState(
        settings=ApiSettings(
            environment="test",
        )
    )
    catalog = _catalog()

    started_at = datetime(
        2026,
        7,
        25,
        9,
        0,
        tzinfo=UTC,
    )
    catalog_loaded_at = datetime(
        2026,
        7,
        25,
        9,
        1,
        tzinfo=UTC,
    )

    runtime.mark_started(
        timestamp=started_at,
    )
    runtime.attach_catalog(
        catalog,
        timestamp=catalog_loaded_at,
    )

    assert runtime.started_at == started_at
    assert runtime.catalog_loaded_at == catalog_loaded_at
    assert runtime.transfer_data_catalog is catalog
    assert runtime.is_ready is True

    runtime.clear_catalog()

    assert runtime.started_at == started_at
    assert runtime.catalog_loaded_at is None
    assert runtime.transfer_data_catalog is None
    assert runtime.is_ready is False
