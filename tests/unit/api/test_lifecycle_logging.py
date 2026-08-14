"""Tests for API and runtime catalog lifecycle logs."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

import wc26.api.app as app_module
from wc26.analytics.transfer_intelligence.catalog import (
    TransferDataCatalog,
)
from wc26.analytics.transfer_intelligence.errors import (
    InvalidDatasetError,
)
from wc26.api.app import create_app
from wc26.api.deployment import (
    DeploymentIdentity,
)
from wc26.api.settings import (
    ApiSettings,
    TransferDatasetPaths,
)


def _catalog() -> TransferDataCatalog:
    """Build a deterministic catalog for lifecycle tests."""

    return TransferDataCatalog(
        players=pd.DataFrame(
            {
                "player_id": [978838],
                "player_name": ["Michael Olise"],
            }
        ),
        similarity=pd.DataFrame(
            {
                "source_player_id": [978838],
            }
        ),
        heatmap_similarity=pd.DataFrame(
            {
                "target_player_id": [978838],
            }
        ),
        heatmap_profiles=pd.DataFrame(
            {
                "player_id": [978838],
            }
        ),
    )


def _dataset_paths() -> TransferDatasetPaths:
    """Return deterministic runtime dataset paths."""

    return TransferDatasetPaths(
        features=Path("runtime/features.csv"),
        similarity=Path("runtime/similarity.csv"),
        heatmap_similarity=Path("runtime/heatmap-similarity.csv"),
        heatmap_profiles=Path("runtime/heatmap-profiles.csv"),
    )


def _identity() -> DeploymentIdentity:
    """Return deterministic deployment identity."""

    return DeploymentIdentity(
        provider="railway",
        commit_sha="a" * 40,
        branch=("feat/docker-deployment-foundation"),
        deployment_id=("deployment-lifecycle-test"),
        dataset_bundle_sha256=("b" * 64),
    )


def _lifecycle_records(
    caplog: pytest.LogCaptureFixture,
) -> list[logging.LogRecord]:
    """Return only lifecycle logger records."""

    return [record for record in caplog.records if record.name == "wc26.api.lifecycle"]


def _event_record(
    records: list[logging.LogRecord],
    event: str,
) -> logging.LogRecord:
    """Return one lifecycle record by event name."""

    return next(
        record
        for record in records
        if getattr(
            record,
            "event",
            None,
        )
        == event
    )


def test_catalog_lifecycle_logs_include_identity_and_counts(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    catalog = _catalog()

    monkeypatch.setattr(
        app_module,
        "resolve_deployment_identity",
        _identity,
    )

    def fake_catalog_loader(
        *,
        features: Path,
        player_tournament_summary: Path,
        similarity: Path,
        heatmap_similarity: Path,
        heatmap_profiles: Path,
    ) -> TransferDataCatalog:
        _ = player_tournament_summary
        del (
            features,
            similarity,
            heatmap_similarity,
            heatmap_profiles,
        )

        return catalog

    application = create_app(
        settings=ApiSettings(
            environment="production",
            service_name=("wc26-lifecycle-test"),
        ),
        dataset_paths=_dataset_paths(),
        catalog_loader=(fake_catalog_loader),
    )

    with caplog.at_level(
        logging.INFO,
        logger="wc26.api.lifecycle",
    ):
        with TestClient(application) as client:
            response = client.get("/ready")

            assert response.status_code == 200

    records = _lifecycle_records(caplog)

    assert [
        getattr(
            record,
            "event",
            None,
        )
        for record in records
    ] == [
        "api.starting",
        "catalog.loading",
        "catalog.loaded",
        "api.ready",
        "api.shutdown.started",
        "api.shutdown.completed",
    ]

    starting = _event_record(
        records,
        "api.starting",
    )

    assert starting.service == "wc26-lifecycle-test"
    assert starting.environment == "production"
    assert starting.provider == "railway"
    assert starting.commit_sha == "a" * 40
    assert starting.deployment_id == "deployment-lifecycle-test"
    assert starting.dataset_bundle_sha256 == "b" * 64

    loading = _event_record(
        records,
        "catalog.loading",
    )

    assert loading.features_path == "runtime/features.csv"
    assert loading.similarity_path == "runtime/similarity.csv"

    loaded = _event_record(
        records,
        "catalog.loaded",
    )

    assert loaded.players_rows == 1
    assert loaded.similarity_rows == 1
    assert loaded.heatmap_similarity_rows == 1
    assert loaded.heatmap_profiles_rows == 1
    assert loaded.duration_ms >= 0

    ready = _event_record(
        records,
        "api.ready",
    )

    assert ready.ready is True
    assert ready.startup_duration_ms >= 0

    shutdown_started = _event_record(
        records,
        "api.shutdown.started",
    )

    assert shutdown_started.ready is True
    assert shutdown_started.uptime_seconds >= 0

    shutdown_completed = _event_record(
        records,
        "api.shutdown.completed",
    )

    assert shutdown_completed.ready is False
    assert shutdown_completed.duration_ms >= 0
    assert shutdown_completed.uptime_seconds >= 0


def test_application_without_catalog_logs_started_not_ready(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(
        app_module,
        "resolve_deployment_identity",
        _identity,
    )

    application = create_app(
        settings=ApiSettings(
            environment="test",
        )
    )

    with caplog.at_level(
        logging.INFO,
        logger="wc26.api.lifecycle",
    ):
        with TestClient(application) as client:
            response = client.get("/health")

            assert response.status_code == 200

    records = _lifecycle_records(caplog)
    events = [
        getattr(
            record,
            "event",
            None,
        )
        for record in records
    ]

    assert "api.started" in events
    assert "api.ready" not in events
    assert "catalog.loading" not in events
    assert "catalog.loaded" not in events

    started = _event_record(
        records,
        "api.started",
    )

    assert started.ready is False
    assert started.startup_duration_ms >= 0


def test_catalog_failure_emits_failure_and_cleanup_logs(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(
        app_module,
        "resolve_deployment_identity",
        _identity,
    )

    def failing_catalog_loader(
        *,
        features: Path,
        player_tournament_summary: Path,
        similarity: Path,
        heatmap_similarity: Path,
        heatmap_profiles: Path,
    ) -> TransferDataCatalog:
        _ = player_tournament_summary
        del (
            features,
            similarity,
            heatmap_similarity,
            heatmap_profiles,
        )

        raise InvalidDatasetError("Catalog lifecycle failure.")

    application = create_app(catalog_loader=(failing_catalog_loader))

    runtime = application.state.api_runtime

    with caplog.at_level(
        logging.INFO,
        logger="wc26.api.lifecycle",
    ):
        with pytest.raises(
            InvalidDatasetError,
            match=("Catalog lifecycle failure"),
        ):
            with TestClient(application):
                pass

    records = _lifecycle_records(caplog)
    events = [
        getattr(
            record,
            "event",
            None,
        )
        for record in records
    ]

    assert events == [
        "api.starting",
        "catalog.loading",
        "catalog.load_failed",
        "api.shutdown.started",
        "api.shutdown.completed",
    ]

    failure = _event_record(
        records,
        "catalog.load_failed",
    )

    assert failure.levelno == logging.ERROR
    assert failure.duration_ms >= 0

    assert runtime.transfer_data_catalog is None
    assert runtime.is_ready is False
