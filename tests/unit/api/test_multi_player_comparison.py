"""Tests for the multi-player comparison API route."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from wc26.analytics.transfer_intelligence.errors import (
    InvalidMultiPlayerComparisonRequestError,
)
from wc26.analytics.transfer_intelligence.models import (
    MultiPlayerComparisonCandidateResult,
    MultiPlayerComparisonEvidenceResult,
    MultiPlayerComparisonRequest,
    MultiPlayerComparisonResult,
    PlayerSearchItem,
)
from wc26.api import create_app
from wc26.api.dependencies import (
    MultiPlayerComparisonRunner,
    TransferDatasetPaths,
    get_multi_player_comparison_runner,
    get_transfer_dataset_paths,
)


def _player(
    player_id: int,
    player_name: str,
) -> PlayerSearchItem:
    return PlayerSearchItem(
        player_id=player_id,
        player_name=player_name,
        national_team_name="France",
        country_name="France",
        country_alpha3="FRA",
        position="M",
        final_role="Advanced Playmaker",
        archetype="Creator",
        spatial_role="Right Half-Space",
        age=24.0,
        market_value=80_000_000.0,
        market_value_currency="EUR",
        minutes=540.0,
        role_confidence_pct=82.0,
        data_reliability_score=0.8,
        player_quality_score=84.0,
    )


def _result() -> MultiPlayerComparisonResult:
    return MultiPlayerComparisonResult(
        target=_player(
            978838,
            "Michael Olise",
        ),
        candidates=(
            MultiPlayerComparisonCandidateResult(
                player=_player(
                    789071,
                    "Dani Olmo",
                ),
                evidence=(
                    MultiPlayerComparisonEvidenceResult(
                        statistical_similarity_pct=91.0,
                        spatial_similarity_pct=84.0,
                        heatmap_similarity_score_pct=88.0,
                        role_fit_pct=86.0,
                        market_value_advantage_pct=60.0,
                    )
                ),
            ),
            MultiPlayerComparisonCandidateResult(
                player=_player(
                    805078,
                    "Candidate Without Pair Evidence",
                ),
                evidence=(
                    MultiPlayerComparisonEvidenceResult(
                        statistical_similarity_pct=None,
                        spatial_similarity_pct=72.0,
                        heatmap_similarity_score_pct=None,
                        role_fit_pct=78.0,
                        market_value_advantage_pct=70.0,
                    )
                ),
            ),
        ),
    )


def _dataset_paths() -> TransferDatasetPaths:
    return TransferDatasetPaths(
        features=Path("test-data/features.csv"),
        similarity=Path("test-data/similarity.csv"),
        heatmap_similarity=Path("test-data/heatmap-similarity.csv"),
        heatmap_profiles=Path("test-data/heatmap-profiles.csv"),
    )


def test_multi_player_comparison_route_is_in_openapi_schema() -> None:
    application = create_app()
    schema = application.openapi()

    route = "/api/v1/transfer-intelligence/multi-comparison/{target_player_id}"

    operation = schema["paths"][route]["get"]

    assert "400" in operation["responses"]
    assert "404" in operation["responses"]
    assert "500" in operation["responses"]
    assert "503" in operation["responses"]

    parameters = {parameter["name"]: parameter for parameter in operation["parameters"]}

    candidate_parameter = parameters["candidate_player_ids"]

    assert candidate_parameter["in"] == "query"
    assert candidate_parameter["required"] is True
    assert candidate_parameter["schema"]["type"] == "array"

    response_schema = schema["components"]["schemas"]["MultiPlayerComparisonResponse"]

    assert response_schema["properties"]["target"]["$ref"].endswith(
        "/MultiPlayerComparisonPlayerResponse"
    )


def test_endpoint_preserves_candidate_order_and_null_evidence() -> None:
    application = create_app()

    dataset_paths = _dataset_paths()

    captured: list[MultiPlayerComparisonRequest] = []

    def override_dataset_paths() -> TransferDatasetPaths:
        return dataset_paths

    def fake_runner(
        request: MultiPlayerComparisonRequest,
    ) -> MultiPlayerComparisonResult:
        captured.append(
            request,
        )

        return _result()

    def override_runner() -> MultiPlayerComparisonRunner:
        return fake_runner

    application.dependency_overrides[get_transfer_dataset_paths] = override_dataset_paths

    application.dependency_overrides[get_multi_player_comparison_runner] = override_runner

    with TestClient(application) as client:
        response = client.get(
            ("/api/v1/transfer-intelligence/multi-comparison/978838"),
            params=[
                (
                    "candidate_player_ids",
                    "789071",
                ),
                (
                    "candidate_player_ids",
                    "805078",
                ),
            ],
        )

    assert response.status_code == 200

    assert captured == [
        MultiPlayerComparisonRequest(
            target_player_id=978838,
            candidate_player_ids=(
                789071,
                805078,
            ),
            features=dataset_paths.features,
            similarity=dataset_paths.similarity,
            heatmap_similarity=(dataset_paths.heatmap_similarity),
            heatmap_profiles=(dataset_paths.heatmap_profiles),
        )
    ]

    payload = response.json()

    assert [candidate["player"]["player_id"] for candidate in payload["candidates"]] == [
        789071,
        805078,
    ]

    assert payload["candidates"][1]["evidence"]["statistical_similarity_pct"] is None

    assert payload["candidates"][1]["evidence"]["heatmap_similarity_score_pct"] is None


def test_endpoint_requires_between_one_and_three_candidates() -> None:
    application = create_app()

    runner_called = False

    def fake_runner(
        request: MultiPlayerComparisonRequest,
    ) -> MultiPlayerComparisonResult:
        nonlocal runner_called

        runner_called = True

        return _result()

    def override_runner() -> MultiPlayerComparisonRunner:
        return fake_runner

    application.dependency_overrides[get_multi_player_comparison_runner] = override_runner

    with TestClient(application) as client:
        missing_response = client.get("/api/v1/transfer-intelligence/multi-comparison/978838")

        too_many_response = client.get(
            ("/api/v1/transfer-intelligence/multi-comparison/978838"),
            params=[
                (
                    "candidate_player_ids",
                    str(player_id),
                )
                for player_id in (
                    1,
                    2,
                    3,
                    4,
                )
            ],
        )

    assert missing_response.status_code == 422
    assert too_many_response.status_code == 422
    assert runner_called is False


def test_endpoint_maps_domain_validation_to_bad_request() -> None:
    application = create_app()

    def failing_runner(
        request: MultiPlayerComparisonRequest,
    ) -> MultiPlayerComparisonResult:
        del request

        raise InvalidMultiPlayerComparisonRequestError(
            "Target and candidate player IDs must be unique."
        )

    def override_runner() -> MultiPlayerComparisonRunner:
        return failing_runner

    application.dependency_overrides[get_multi_player_comparison_runner] = override_runner

    with TestClient(application) as client:
        response = client.get(
            ("/api/v1/transfer-intelligence/multi-comparison/978838"),
            params={
                "candidate_player_ids": "978838",
            },
        )

    assert response.status_code == 400

    assert response.json() == {
        "error": {
            "code": ("invalid_transfer_analysis_request"),
            "message": ("Target and candidate player IDs must be unique."),
        }
    }
