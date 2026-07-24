"""Tests for the Player Search API route."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from wc26.analytics.transfer_intelligence.errors import (
    InvalidPlayerSearchError,
)
from wc26.analytics.transfer_intelligence.models import (
    PlayerSearchItem,
    PlayerSearchRequest,
    PlayerSearchResult,
)
from wc26.api import create_app
from wc26.api.dependencies import (
    PlayerSearchRunner,
    TransferDatasetPaths,
    get_player_search_runner,
    get_transfer_dataset_paths,
)


def _build_search_result() -> PlayerSearchResult:
    return PlayerSearchResult(
        query="olise",
        players=(
            PlayerSearchItem(
                player_id=934235,
                player_name="Michael Olise",
                national_team_name="France",
                position="F",
                final_role="Right Elite Inside Forward",
                archetype="Creative Wide Forward",
                age=24.6,
                market_value=65_000_000.0,
                market_value_currency="EUR",
            ),
        ),
    )


def test_player_search_route_is_in_openapi_schema() -> None:
    application = create_app()

    operation = application.openapi()["paths"]["/api/v1/players/search"]

    assert "get" in operation


def test_player_search_endpoint_delegates_to_application_service() -> None:
    application = create_app()

    dataset_paths = TransferDatasetPaths(
        features=Path("test-data/features.csv"),
        similarity=Path("test-data/similarity.csv"),
        heatmap_similarity=Path("test-data/heatmap-similarity.csv"),
        heatmap_profiles=Path("test-data/heatmap-profiles.csv"),
    )

    captured_requests: list[PlayerSearchRequest] = []

    def override_dataset_paths() -> TransferDatasetPaths:
        return dataset_paths

    def fake_player_search_runner(
        request: PlayerSearchRequest,
    ) -> PlayerSearchResult:
        captured_requests.append(request)
        return _build_search_result()

    def override_player_search_runner() -> PlayerSearchRunner:
        return fake_player_search_runner

    application.dependency_overrides[get_transfer_dataset_paths] = override_dataset_paths
    application.dependency_overrides[get_player_search_runner] = override_player_search_runner

    with TestClient(application) as client:
        response = client.get(
            "/api/v1/players/search",
            params={
                "q": "olise",
                "limit": 7,
            },
        )

    assert response.status_code == 200

    assert captured_requests == [
        PlayerSearchRequest(
            query="olise",
            features=dataset_paths.features,
            limit=7,
        )
    ]

    assert response.json() == {
        "query": "olise",
        "count": 1,
        "players": [
            {
                "player_id": 934235,
                "player_name": "Michael Olise",
                "national_team_name": "France",
                "position": "F",
                "final_role": ("Right Elite Inside Forward"),
                "archetype": "Creative Wide Forward",
                "age": 24.6,
                "market_value": 65_000_000.0,
                "market_value_currency": "EUR",
            }
        ],
    }


def test_player_search_endpoint_uses_default_limit() -> None:
    application = create_app()

    captured_requests: list[PlayerSearchRequest] = []

    def fake_player_search_runner(
        request: PlayerSearchRequest,
    ) -> PlayerSearchResult:
        captured_requests.append(request)

        return PlayerSearchResult(
            query=request.query,
            players=(),
        )

    def override_player_search_runner() -> PlayerSearchRunner:
        return fake_player_search_runner

    application.dependency_overrides[get_player_search_runner] = override_player_search_runner

    with TestClient(application) as client:
        response = client.get(
            "/api/v1/players/search",
            params={
                "q": "unknown",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "query": "unknown",
        "count": 0,
        "players": [],
    }
    assert captured_requests[0].limit == 10


def test_player_search_endpoint_rejects_short_query() -> None:
    application = create_app()

    runner_called = False

    def fake_player_search_runner(
        request: PlayerSearchRequest,
    ) -> PlayerSearchResult:
        del request

        nonlocal runner_called
        runner_called = True

        return _build_search_result()

    def override_player_search_runner() -> PlayerSearchRunner:
        return fake_player_search_runner

    application.dependency_overrides[get_player_search_runner] = override_player_search_runner

    with TestClient(application) as client:
        response = client.get(
            "/api/v1/players/search",
            params={
                "q": "a",
            },
        )

    assert response.status_code == 422
    assert runner_called is False


def test_player_search_endpoint_rejects_invalid_limit() -> None:
    application = create_app()

    runner_called = False

    def fake_player_search_runner(
        request: PlayerSearchRequest,
    ) -> PlayerSearchResult:
        del request

        nonlocal runner_called
        runner_called = True

        return _build_search_result()

    def override_player_search_runner() -> PlayerSearchRunner:
        return fake_player_search_runner

    application.dependency_overrides[get_player_search_runner] = override_player_search_runner

    with TestClient(application) as client:
        response = client.get(
            "/api/v1/players/search",
            params={
                "q": "olise",
                "limit": 26,
            },
        )

    assert response.status_code == 422
    assert runner_called is False


def test_player_search_endpoint_returns_domain_validation_error() -> None:
    application = create_app()

    def failing_player_search_runner(
        request: PlayerSearchRequest,
    ) -> PlayerSearchResult:
        del request

        raise InvalidPlayerSearchError("Player search query must contain at least 2 characters.")

    def override_player_search_runner() -> PlayerSearchRunner:
        return failing_player_search_runner

    application.dependency_overrides[get_player_search_runner] = override_player_search_runner

    with TestClient(application) as client:
        response = client.get(
            "/api/v1/players/search",
            params={
                "q": "  ",
            },
        )

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "invalid_player_search",
            "message": ("Player search query must contain at least 2 characters."),
        }
    }


def test_player_search_endpoint_hides_unexpected_errors() -> None:
    application = create_app()

    def failing_player_search_runner(
        request: PlayerSearchRequest,
    ) -> PlayerSearchResult:
        del request

        raise RuntimeError("sensitive internal player-search detail")

    def override_player_search_runner() -> PlayerSearchRunner:
        return failing_player_search_runner

    application.dependency_overrides[get_player_search_runner] = override_player_search_runner

    with TestClient(application) as client:
        response = client.get(
            "/api/v1/players/search",
            params={
                "q": "olise",
            },
        )

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "player_search_failed",
            "message": ("Player search could not be completed."),
        }
    }

    assert "sensitive internal player-search detail" not in response.text


def test_player_search_openapi_documents_error_responses() -> None:
    application = create_app()

    operation = application.openapi()["paths"]["/api/v1/players/search"]["get"]

    assert "400" in operation["responses"]
    assert "500" in operation["responses"]
    assert "503" in operation["responses"]
