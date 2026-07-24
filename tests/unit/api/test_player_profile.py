"""Tests for the Player Profile API route."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from wc26.analytics.transfer_intelligence.errors import (
    InvalidPlayerProfileError,
    PlayerNotFoundError,
)
from wc26.analytics.transfer_intelligence.models import (
    PlayerProfileRequest,
    PlayerProfileResult,
)
from wc26.api import create_app
from wc26.api.dependencies import (
    PlayerProfileRunner,
    TransferDatasetPaths,
    get_player_profile_runner,
    get_transfer_dataset_paths,
)


def _build_profile() -> PlayerProfileResult:
    return PlayerProfileResult(
        player_id=978838,
        player_name="Michael Olise",
        national_team_name="France",
        country_name="France",
        position="M",
        age=24.6,
        height_cm=184.0,
        appearances=6,
        starts=6,
        minutes=488.0,
        weighted_rating=7.570697,
        market_value=144_000_000.0,
        market_value_currency="EUR",
        archetype="Wide Creator",
        spatial_role="Advanced Central Zone",
        final_role="Advanced Central Playmaker",
        lateral_profile="Central Lane",
        vertical_profile="Advanced Middle Third",
        mobility_profile="Positionally Stable",
        role_confidence_pct=87.19,
        spatial_reliability=1.0,
        data_reliability_score=74.52,
        player_quality_score=88.85,
        role_reason="Statistical and spatial profile.",
    )


def test_player_profile_route_is_in_openapi_schema() -> None:
    application = create_app()

    operation = application.openapi()["paths"]["/api/v1/players/{player_id}"]

    assert "get" in operation


def test_player_profile_endpoint_delegates_to_service() -> None:
    application = create_app()

    dataset_paths = TransferDatasetPaths(
        features=Path("test-data/features.csv"),
        similarity=Path("test-data/similarity.csv"),
        heatmap_similarity=Path("test-data/heatmap-similarity.csv"),
        heatmap_profiles=Path("test-data/heatmap-profiles.csv"),
    )

    captured_requests: list[PlayerProfileRequest] = []

    def override_dataset_paths() -> TransferDatasetPaths:
        return dataset_paths

    def fake_profile_runner(
        request: PlayerProfileRequest,
    ) -> PlayerProfileResult:
        captured_requests.append(request)
        return _build_profile()

    def override_profile_runner() -> PlayerProfileRunner:
        return fake_profile_runner

    application.dependency_overrides[get_transfer_dataset_paths] = override_dataset_paths
    application.dependency_overrides[get_player_profile_runner] = override_profile_runner

    with TestClient(application) as client:
        response = client.get("/api/v1/players/978838")

    assert response.status_code == 200

    assert captured_requests == [
        PlayerProfileRequest(
            player_id=978838,
            features=dataset_paths.features,
        )
    ]

    assert response.json()["player_id"] == 978838
    assert response.json()["player_name"] == "Michael Olise"
    assert response.json()["final_role"] == "Advanced Central Playmaker"


def test_player_profile_endpoint_rejects_non_positive_id() -> None:
    application = create_app()

    runner_called = False

    def fake_profile_runner(
        _request: PlayerProfileRequest,
    ) -> PlayerProfileResult:
        nonlocal runner_called

        runner_called = True
        return _build_profile()

    def override_profile_runner() -> PlayerProfileRunner:
        return fake_profile_runner

    application.dependency_overrides[get_player_profile_runner] = override_profile_runner

    with TestClient(application) as client:
        response = client.get("/api/v1/players/0")

    assert response.status_code == 422
    assert runner_called is False


def test_player_profile_endpoint_returns_not_found_error() -> None:
    application = create_app()

    def failing_profile_runner(
        _request: PlayerProfileRequest,
    ) -> PlayerProfileResult:
        raise PlayerNotFoundError("Player not found for ID: 999999")

    def override_profile_runner() -> PlayerProfileRunner:
        return failing_profile_runner

    application.dependency_overrides[get_player_profile_runner] = override_profile_runner

    with TestClient(application) as client:
        response = client.get("/api/v1/players/999999")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "player_not_found",
            "message": "Player not found for ID: 999999",
        }
    }


def test_player_profile_endpoint_returns_domain_validation_error() -> None:
    application = create_app()

    def failing_profile_runner(
        _request: PlayerProfileRequest,
    ) -> PlayerProfileResult:
        raise InvalidPlayerProfileError("Player ID must be a positive integer.")

    def override_profile_runner() -> PlayerProfileRunner:
        return failing_profile_runner

    application.dependency_overrides[get_player_profile_runner] = override_profile_runner

    with TestClient(application) as client:
        response = client.get("/api/v1/players/978838")

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "invalid_player_profile",
            "message": "Player ID must be a positive integer.",
        }
    }


def test_player_profile_endpoint_hides_unexpected_errors() -> None:
    application = create_app()

    def failing_profile_runner(
        _request: PlayerProfileRequest,
    ) -> PlayerProfileResult:
        raise RuntimeError("sensitive player-profile implementation detail")

    def override_profile_runner() -> PlayerProfileRunner:
        return failing_profile_runner

    application.dependency_overrides[get_player_profile_runner] = override_profile_runner

    with TestClient(application) as client:
        response = client.get("/api/v1/players/978838")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "player_profile_failed",
            "message": ("Player profile could not be retrieved."),
        }
    }

    assert "sensitive player-profile implementation detail" not in response.text


def test_player_profile_openapi_documents_error_responses() -> None:
    application = create_app()

    operation = application.openapi()["paths"]["/api/v1/players/{player_id}"]["get"]

    assert "400" in operation["responses"]
    assert "404" in operation["responses"]
    assert "500" in operation["responses"]
    assert "503" in operation["responses"]
