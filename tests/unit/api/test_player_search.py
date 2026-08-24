"""Tests for the Player Discovery API route."""

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


def _build_search_result(
    *,
    query: str | None = "olise",
    total: int = 1,
    offset: int = 0,
    limit: int = 10,
    sort_by: str = "relevance",
    sort_direction: str = "asc",
) -> PlayerSearchResult:
    return PlayerSearchResult(
        query=query,
        total=total,
        offset=offset,
        limit=limit,
        sort_by=sort_by,
        sort_direction=sort_direction,
        players=(
            PlayerSearchItem(
                player_id=934235,
                player_name="Michael Olise",
                national_team_name="France",
                country_name="France",
                country_alpha3="FRA",
                position="M",
                final_role=("Central Half-Space Creator"),
                archetype="Wide Creator",
                spatial_role=("Advanced Central Zone"),
                age=24.6,
                market_value=65_000_000.0,
                market_value_currency="EUR",
                minutes=650.0,
                role_confidence_pct=87.2,
                data_reliability_score=82.9,
                player_quality_score=85.5,
            ),
        ),
    )


def test_player_search_route_is_in_openapi_schema() -> None:
    application = create_app()

    operation = application.openapi()["paths"]["/api/v1/players/search"]

    assert "get" in operation


def test_player_search_endpoint_delegates_all_filters() -> None:
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
        search_request: PlayerSearchRequest,
    ) -> PlayerSearchResult:
        captured_requests.append(search_request)

        return _build_search_result(
            query=search_request.query,
            offset=search_request.offset,
            limit=search_request.limit,
            sort_by=(search_request.sort_by or "market_value"),
            sort_direction=(search_request.sort_direction or "asc"),
        )

    def override_player_search_runner() -> PlayerSearchRunner:
        return fake_player_search_runner

    application.dependency_overrides[get_transfer_dataset_paths] = override_dataset_paths

    application.dependency_overrides[get_player_search_runner] = override_player_search_runner

    with TestClient(application) as client:
        response = client.get(
            "/api/v1/players/search",
            params=[
                ("q", "olise"),
                ("position", "M"),
                ("position", "F"),
                (
                    "final_role",
                    "Central Half-Space Creator",
                ),
                (
                    "archetype",
                    "Wide Creator",
                ),
                ("country", "France"),
                ("min_age", "20"),
                ("max_age", "27"),
                (
                    "min_market_value",
                    "1000000",
                ),
                (
                    "max_market_value",
                    "70000000",
                ),
                ("min_minutes", "300"),
                (
                    "min_role_confidence",
                    "70",
                ),
                (
                    "min_data_reliability",
                    "60",
                ),
                (
                    "sort_by",
                    "market_value",
                ),
                (
                    "sort_direction",
                    "asc",
                ),
                ("offset", "5"),
                ("limit", "7"),
            ],
        )

    assert response.status_code == 200

    assert captured_requests == [
        PlayerSearchRequest(
            query="olise",
            features=dataset_paths.features,
            limit=7,
            offset=5,
            positions=(
                "M",
                "F",
            ),
            final_roles=("Central Half-Space Creator",),
            archetypes=("Wide Creator",),
            countries=("France",),
            minimum_age=20.0,
            maximum_age=27.0,
            minimum_market_value=1_000_000.0,
            maximum_market_value=70_000_000.0,
            minimum_minutes=300.0,
            minimum_role_confidence=70.0,
            minimum_data_reliability=60.0,
            sort_by="market_value",
            sort_direction="asc",
        )
    ]

    assert response.json() == {
        "query": "olise",
        "count": 1,
        "total": 1,
        "offset": 5,
        "limit": 7,
        "has_more": False,
        "sort_by": "market_value",
        "sort_direction": "asc",
        "players": [
            {
                "player_id": 934235,
                "player_name": "Michael Olise",
                "national_team_name": "France",
                "country_name": "France",
                "country_alpha3": "FRA",
                "position": "M",
                "final_role": ("Central Half-Space Creator"),
                "archetype": "Wide Creator",
                "spatial_role": ("Advanced Central Zone"),
                "age": 24.6,
                "market_value": 65_000_000.0,
                "market_value_currency": "EUR",
                "minutes": 650.0,
                "role_confidence_pct": 87.2,
                "data_reliability_score": 82.9,
                "player_quality_score": 85.5,
            }
        ],
    }


def test_player_search_endpoint_accepts_filter_only_discovery() -> None:
    application = create_app()

    captured_requests: list[PlayerSearchRequest] = []

    def fake_player_search_runner(
        search_request: PlayerSearchRequest,
    ) -> PlayerSearchResult:
        captured_requests.append(search_request)

        return PlayerSearchResult(
            query=search_request.query,
            players=(),
            total=0,
            offset=search_request.offset,
            limit=search_request.limit,
            sort_by="player_quality",
            sort_direction="desc",
        )

    def override_player_search_runner() -> PlayerSearchRunner:
        return fake_player_search_runner

    application.dependency_overrides[get_player_search_runner] = override_player_search_runner

    with TestClient(application) as client:
        response = client.get(
            "/api/v1/players/search",
            params=[
                ("position", "D"),
                (
                    "archetype",
                    "Ball-Carrying Defender",
                ),
                ("max_age", "24"),
                (
                    "max_market_value",
                    "30000000",
                ),
                ("min_minutes", "300"),
            ],
        )

    assert response.status_code == 200
    assert response.json() == {
        "query": None,
        "count": 0,
        "total": 0,
        "offset": 0,
        "limit": 10,
        "has_more": False,
        "sort_by": "player_quality",
        "sort_direction": "desc",
        "players": [],
    }

    assert captured_requests == [
        PlayerSearchRequest(
            query=None,
            features=(captured_requests[0].features),
            limit=10,
            positions=("D",),
            archetypes=("Ball-Carrying Defender",),
            maximum_age=24.0,
            maximum_market_value=30_000_000.0,
            minimum_minutes=300.0,
        )
    ]


def test_player_search_endpoint_uses_default_pagination() -> None:
    application = create_app()

    captured_requests: list[PlayerSearchRequest] = []

    def fake_player_search_runner(
        search_request: PlayerSearchRequest,
    ) -> PlayerSearchResult:
        captured_requests.append(search_request)

        return PlayerSearchResult(
            query=search_request.query,
            players=(),
            total=0,
            offset=search_request.offset,
            limit=search_request.limit,
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
    assert response.json()["offset"] == 0
    assert response.json()["limit"] == 10
    assert response.json()["total"] == 0
    assert response.json()["has_more"] is False

    assert captured_requests[0].offset == 0
    assert captured_requests[0].limit == 10


def test_player_search_endpoint_rejects_short_query() -> None:
    application = create_app()

    runner_called = False

    def fake_player_search_runner(
        search_request: PlayerSearchRequest,
    ) -> PlayerSearchResult:
        del search_request

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


def test_player_search_endpoint_rejects_invalid_query_constraints() -> None:
    application = create_app()

    with TestClient(application) as client:
        invalid_limit = client.get(
            "/api/v1/players/search",
            params={
                "q": "olise",
                "limit": 26,
            },
        )

        invalid_confidence = client.get(
            "/api/v1/players/search",
            params={
                "position": "D",
                "min_role_confidence": 101,
            },
        )

        invalid_offset = client.get(
            "/api/v1/players/search",
            params={
                "position": "D",
                "offset": -1,
            },
        )

    assert invalid_limit.status_code == 422
    assert invalid_confidence.status_code == 422
    assert invalid_offset.status_code == 422


def test_player_search_endpoint_returns_domain_validation_error() -> None:
    application = create_app()

    def failing_player_search_runner(
        search_request: PlayerSearchRequest,
    ) -> PlayerSearchResult:
        del search_request

        raise InvalidPlayerSearchError(
            "Player discovery requires a name query or at least one filter."
        )

    def override_player_search_runner() -> PlayerSearchRunner:
        return failing_player_search_runner

    application.dependency_overrides[get_player_search_runner] = override_player_search_runner

    with TestClient(application) as client:
        response = client.get("/api/v1/players/search")

    assert response.status_code == 400
    assert response.json() == {
        "error": {
            "code": "invalid_player_search",
            "message": ("Player discovery requires a name query or at least one filter."),
        }
    }


def test_player_search_endpoint_hides_unexpected_errors() -> None:
    application = create_app()

    def failing_player_search_runner(
        search_request: PlayerSearchRequest,
    ) -> PlayerSearchResult:
        del search_request

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


def test_player_search_openapi_documents_contract() -> None:
    application = create_app()

    operation = application.openapi()["paths"]["/api/v1/players/search"]["get"]

    parameter_names = {parameter["name"] for parameter in operation["parameters"]}

    assert {
        "q",
        "position",
        "final_role",
        "archetype",
        "country",
        "min_age",
        "max_age",
        "min_market_value",
        "max_market_value",
        "min_minutes",
        "min_role_confidence",
        "min_data_reliability",
        "sort_by",
        "sort_direction",
        "offset",
        "limit",
    }.issubset(parameter_names)

    assert "400" in operation["responses"]
    assert "500" in operation["responses"]
    assert "503" in operation["responses"]
