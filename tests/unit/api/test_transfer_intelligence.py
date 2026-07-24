"""Tests for Transfer Intelligence API routes."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wc26.analytics.transfer_intelligence.errors import (
    InvalidTransferAnalysisRequestError,
)
from wc26.analytics.transfer_intelligence.models import (
    TransferAnalysisRequest,
    TransferAnalysisResult,
    TransferModeResult,
    TransferRecommendation,
)
from wc26.api import create_app
from wc26.api.dependencies import (
    TransferAnalysisRunner,
    TransferDatasetPaths,
    get_transfer_analysis_runner,
    get_transfer_dataset_paths,
)


def _build_analysis_result() -> TransferAnalysisResult:
    """Return a deterministic transfer-analysis result."""

    return TransferAnalysisResult(
        target={
            "player_id": 10,
            "player_name": "Michael Olise",
        },
        modes=(
            TransferModeResult(
                mode="immediate",
                recommendations=(
                    TransferRecommendation(
                        data={
                            "player_id": 20,
                            "player_name": "Dani Olmo",
                            "transfer_score": 88.5,
                        }
                    ),
                ),
            ),
        ),
    )


def test_transfer_analysis_route_is_in_openapi_schema() -> None:
    application = create_app()

    operation = application.openapi()["paths"]["/api/v1/transfer-intelligence/analyze"]["post"]

    assert "400" in operation["responses"]
    assert "404" in operation["responses"]
    assert "409" in operation["responses"]
    assert "500" in operation["responses"]
    assert "503" in operation["responses"]


def test_transfer_analysis_endpoint_delegates_name_to_application_service() -> None:
    application = create_app()

    dataset_paths = TransferDatasetPaths(
        features=Path("test-data/features.csv"),
        similarity=Path("test-data/similarity.csv"),
        heatmap_similarity=Path("test-data/heatmap-similarity.csv"),
        heatmap_profiles=Path("test-data/heatmap-profiles.csv"),
    )

    captured_requests: list[TransferAnalysisRequest] = []

    def override_dataset_paths() -> TransferDatasetPaths:
        return dataset_paths

    def fake_analysis_runner(
        request: TransferAnalysisRequest,
    ) -> TransferAnalysisResult:
        captured_requests.append(request)

        return _build_analysis_result()

    def override_analysis_runner() -> TransferAnalysisRunner:
        return fake_analysis_runner

    application.dependency_overrides[get_transfer_dataset_paths] = override_dataset_paths
    application.dependency_overrides[get_transfer_analysis_runner] = override_analysis_runner

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/transfer-intelligence/analyze",
            json={
                "player": "Michael Olise",
                "minimum_minutes": 250,
                "minimum_role_confidence": 65,
                "maximum_market_value": 100_000_000,
                "neutral_heatmap_score": 72,
            },
        )

    assert response.status_code == 200

    assert captured_requests == [
        TransferAnalysisRequest(
            player="Michael Olise",
            player_id=None,
            features=dataset_paths.features,
            similarity=dataset_paths.similarity,
            heatmap_similarity=(dataset_paths.heatmap_similarity),
            heatmap_profiles=(dataset_paths.heatmap_profiles),
            minimum_minutes=250.0,
            minimum_role_confidence=65.0,
            maximum_market_value=100_000_000.0,
            neutral_heatmap_score=72.0,
        )
    ]

    assert response.json() == {
        "target": {
            "player_id": 10,
            "player_name": "Michael Olise",
        },
        "modes": {
            "immediate": {
                "mode": "immediate",
                "recommendations": [
                    {
                        "player_id": 20,
                        "player_name": "Dani Olmo",
                        "transfer_score": 88.5,
                    }
                ],
            }
        },
    }


def test_transfer_analysis_endpoint_accepts_player_id() -> None:
    application = create_app()

    dataset_paths = TransferDatasetPaths(
        features=Path("test-data/features.csv"),
        similarity=Path("test-data/similarity.csv"),
        heatmap_similarity=Path("test-data/heatmap-similarity.csv"),
        heatmap_profiles=Path("test-data/heatmap-profiles.csv"),
    )

    captured_requests: list[TransferAnalysisRequest] = []

    def override_dataset_paths() -> TransferDatasetPaths:
        return dataset_paths

    def fake_analysis_runner(
        request: TransferAnalysisRequest,
    ) -> TransferAnalysisResult:
        captured_requests.append(request)

        return _build_analysis_result()

    def override_analysis_runner() -> TransferAnalysisRunner:
        return fake_analysis_runner

    application.dependency_overrides[get_transfer_dataset_paths] = override_dataset_paths
    application.dependency_overrides[get_transfer_analysis_runner] = override_analysis_runner

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/transfer-intelligence/analyze",
            json={
                "player_id": 978838,
                "minimum_minutes": 250,
                "minimum_role_confidence": 65,
                "maximum_market_value": 100_000_000,
                "neutral_heatmap_score": 72,
            },
        )

    assert response.status_code == 200

    assert captured_requests == [
        TransferAnalysisRequest(
            player=None,
            player_id=978838,
            features=dataset_paths.features,
            similarity=dataset_paths.similarity,
            heatmap_similarity=(dataset_paths.heatmap_similarity),
            heatmap_profiles=(dataset_paths.heatmap_profiles),
            minimum_minutes=250.0,
            minimum_role_confidence=65.0,
            maximum_market_value=100_000_000.0,
            neutral_heatmap_score=72.0,
        )
    ]

    assert response.json()["target"] == {
        "player_id": 10,
        "player_name": "Michael Olise",
    }


def test_transfer_analysis_endpoint_uses_filter_defaults() -> None:
    application = create_app()

    captured_requests: list[TransferAnalysisRequest] = []

    def fake_analysis_runner(
        request: TransferAnalysisRequest,
    ) -> TransferAnalysisResult:
        captured_requests.append(request)

        return _build_analysis_result()

    def override_analysis_runner() -> TransferAnalysisRunner:
        return fake_analysis_runner

    application.dependency_overrides[get_transfer_analysis_runner] = override_analysis_runner

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/transfer-intelligence/analyze",
            json={
                "player": "Michael Olise",
            },
        )

    assert response.status_code == 200
    assert len(captured_requests) == 1

    request = captured_requests[0]

    assert request.player == "Michael Olise"
    assert request.player_id is None
    assert request.minimum_minutes == 150.0
    assert request.minimum_role_confidence == 50.0
    assert request.maximum_market_value is None
    assert request.neutral_heatmap_score == 70.0


def test_transfer_analysis_endpoint_rejects_invalid_filters() -> None:
    application = create_app()

    runner_called = False

    def fake_analysis_runner(
        request: TransferAnalysisRequest,
    ) -> TransferAnalysisResult:
        nonlocal runner_called

        del request

        runner_called = True

        return _build_analysis_result()

    def override_analysis_runner() -> TransferAnalysisRunner:
        return fake_analysis_runner

    application.dependency_overrides[get_transfer_analysis_runner] = override_analysis_runner

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/transfer-intelligence/analyze",
            json={
                "player": "Michael Olise",
                "minimum_role_confidence": 101,
            },
        )

    assert response.status_code == 422
    assert runner_called is False


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {
            "player": "Michael Olise",
            "player_id": 978838,
        },
        {
            "player_id": 0,
        },
        {
            "player_id": -1,
        },
        {
            "player": "   ",
        },
    ],
)
def test_transfer_analysis_endpoint_rejects_invalid_target_payload(
    payload: dict[str, object],
) -> None:
    application = create_app()

    runner_called = False

    def fake_analysis_runner(
        request: TransferAnalysisRequest,
    ) -> TransferAnalysisResult:
        nonlocal runner_called

        del request

        runner_called = True

        return _build_analysis_result()

    def override_analysis_runner() -> TransferAnalysisRunner:
        return fake_analysis_runner

    application.dependency_overrides[get_transfer_analysis_runner] = override_analysis_runner

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/transfer-intelligence/analyze",
            json=payload,
        )

    assert response.status_code == 422
    assert runner_called is False


def test_transfer_analysis_endpoint_maps_domain_request_error() -> None:
    application = create_app()

    def failing_analysis_runner(
        request: TransferAnalysisRequest,
    ) -> TransferAnalysisResult:
        del request

        raise InvalidTransferAnalysisRequestError("Provide exactly one of player or player_id.")

    def override_analysis_runner() -> TransferAnalysisRunner:
        return failing_analysis_runner

    application.dependency_overrides[get_transfer_analysis_runner] = override_analysis_runner

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/transfer-intelligence/analyze",
            json={
                "player": "Michael Olise",
            },
        )

    assert response.status_code == 400

    assert response.json() == {
        "error": {
            "code": ("invalid_transfer_analysis_request"),
            "message": ("Provide exactly one of player or player_id."),
        }
    }


def test_transfer_analysis_endpoint_rejects_dataset_paths() -> None:
    application = create_app()

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/transfer-intelligence/analyze",
            json={
                "player": "Michael Olise",
                "features": "/private/server/features.csv",
            },
        )

    assert response.status_code == 422
