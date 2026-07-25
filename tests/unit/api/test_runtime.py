"""Tests for the typed WC26 API runtime state."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pandas as pd
import pytest

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


def test_runtime_state_calculates_uptime() -> None:
    runtime = ApiRuntimeState(
        settings=ApiSettings(
            environment="test",
        )
    )

    started_at = datetime(
        2026,
        7,
        25,
        9,
        0,
        tzinfo=UTC,
    )

    runtime.mark_started(
        timestamp=started_at,
    )

    current_time = started_at + timedelta(
        minutes=2,
        seconds=5.4321,
    )

    assert (
        runtime.uptime_seconds(
            timestamp=current_time,
        )
        == 125.432
    )


def test_runtime_state_does_not_return_negative_uptime() -> None:
    runtime = ApiRuntimeState(
        settings=ApiSettings(
            environment="test",
        )
    )

    started_at = datetime(
        2026,
        7,
        25,
        9,
        0,
        tzinfo=UTC,
    )

    runtime.mark_started(
        timestamp=started_at,
    )

    assert (
        runtime.uptime_seconds(
            timestamp=(started_at - timedelta(seconds=10)),
        )
        == 0.0
    )


def test_runtime_state_rejects_uptime_before_startup() -> None:
    runtime = ApiRuntimeState(
        settings=ApiSettings(
            environment="test",
        )
    )

    with pytest.raises(
        RuntimeError,
        match="runtime has not started",
    ):
        runtime.uptime_seconds()


@pytest.mark.parametrize(
    "operation",
    [
        "startup",
        "catalog",
        "uptime",
    ],
)
def test_runtime_state_rejects_naive_timestamps(
    operation: str,
) -> None:
    runtime = ApiRuntimeState(
        settings=ApiSettings(
            environment="test",
        )
    )
    catalog = _catalog()

    naive_timestamp = datetime(
        2026,
        7,
        25,
        9,
        0,
    )

    if operation == "startup":
        with pytest.raises(
            ValueError,
            match="timezone-aware",
        ):
            runtime.mark_started(
                timestamp=naive_timestamp,
            )

        return

    runtime.mark_started(
        timestamp=datetime(
            2026,
            7,
            25,
            9,
            0,
            tzinfo=UTC,
        )
    )

    if operation == "catalog":
        with pytest.raises(
            ValueError,
            match="timezone-aware",
        ):
            runtime.attach_catalog(
                catalog,
                timestamp=naive_timestamp,
            )

        return

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        runtime.uptime_seconds(
            timestamp=naive_timestamp,
        )
