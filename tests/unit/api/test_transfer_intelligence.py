"""Tests for Transfer Intelligence API routes."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wc26.analytics.transfer_intelligence.errors import (
    InvalidTransferAnalysisRequestError,
)
from wc26.analytics.transfer_intelligence.models import (
    HeatmapComparisonRequest,
    HeatmapComparisonResult,
    HeatmapPlayerResult,
    HeatmapSimilarityResult,
    JsonObject,
    RadarComparisonMetadataResult,
    RadarComparisonRequest,
    RadarComparisonResult,
    RadarDimensionResult,
    RadarPlayerResult,
    TransferAnalysisRequest,
    TransferAnalysisResult,
    TransferModeResult,
    TransferRecommendation,
)
from wc26.api import create_app
from wc26.api.dependencies import (
    HeatmapComparisonRunner,
    RadarComparisonRunner,
    TransferAnalysisRunner,
    TransferDatasetPaths,
    get_heatmap_comparison_runner,
    get_radar_comparison_runner,
    get_transfer_analysis_runner,
    get_transfer_dataset_paths,
)


def _build_explainability_payload() -> JsonObject:
    """Return deterministic recommendation explainability."""

    return {
        "mode": "immediate",
        "score": {
            "weighted_signal_total": 80.5,
            "bonus_total": 8.0,
            "pre_clip_score": 88.5,
            "final_score": 88.5,
            "was_clipped": False,
        },
        "signals": [
            {
                "key": "role_fit_pct",
                "label": "Role fit",
                "description": (
                    "Alignment between the candidate and target across the tactical role model."
                ),
                "source_score": 90.0,
                "input_score": 90.0,
                "weight": 0.23,
                "weighted_contribution": 20.7,
                "evidence_status": "available",
                "note": None,
            },
            {
                "key": "effective_heatmap_score_pct",
                "label": "Heatmap evidence",
                "description": (
                    "Heatmap occupation evidence used by the recruitment scoring model."
                ),
                "source_score": None,
                "input_score": 70.0,
                "weight": 0.12,
                "weighted_contribution": 8.4,
                "evidence_status": "fallback",
                "note": (
                    "Direct heatmap evidence is unavailable; "
                    "the configured neutral fallback is used "
                    "for scoring."
                ),
            },
        ],
        "bonuses": [
            {
                "key": "same_final_role",
                "label": "Same final role",
                "configured_points": 6.0,
                "applied": True,
                "applied_points": 6.0,
            },
            {
                "key": "same_archetype",
                "label": "Same statistical archetype",
                "configured_points": 2.0,
                "applied": True,
                "applied_points": 2.0,
            },
        ],
        "reasons": [
            {
                "key": "same_final_role",
                "group": "role",
                "text": "same final role",
            },
            {
                "key": "statistical_similarity",
                "group": "statistics",
                "text": ("very strong statistical similarity (80.0%)"),
            },
        ],
    }


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
                            "recommendation_type": "like_for_like",
                            "recommendation_strength": "strong",
                            "why_recommended": ("Strong immediate replacement profile."),
                            "explainability": _build_explainability_payload(),
                            "immediate_score": 88.5,
                            "immediate_rank": 1,
                        }
                    ),
                ),
            ),
            TransferModeResult(
                mode="development",
                recommendations=(),
            ),
            TransferModeResult(
                mode="value",
                recommendations=(),
            ),
            TransferModeResult(
                mode="short_term",
                recommendations=(),
            ),
        ),
    )


def test_transfer_analysis_route_is_in_openapi_schema() -> None:
    application = create_app()
    schema = application.openapi()

    operation = schema["paths"]["/api/v1/transfer-intelligence/analyze"]["post"]

    assert "400" in operation["responses"]
    assert "404" in operation["responses"]
    assert "409" in operation["responses"]
    assert "500" in operation["responses"]
    assert "503" in operation["responses"]

    schemas = schema["components"]["schemas"]

    analysis_schema = schemas["TransferAnalysisResponse"]

    assert analysis_schema["properties"]["target"]["$ref"].endswith("/TransferTargetResponse")
    assert analysis_schema["properties"]["modes"]["$ref"].endswith("/TransferModesResponse")

    modes_schema = schemas["TransferModesResponse"]

    expected_modes = {
        "immediate": (
            "ImmediateTransferModeResponse",
            "ImmediateTransferRecommendationResponse",
            "immediate_score",
            "immediate_rank",
        ),
        "development": (
            "DevelopmentTransferModeResponse",
            "DevelopmentTransferRecommendationResponse",
            "development_score",
            "development_rank",
        ),
        "value": (
            "ValueTransferModeResponse",
            "ValueTransferRecommendationResponse",
            "value_score",
            "value_rank",
        ),
        "short_term": (
            "ShortTermTransferModeResponse",
            "ShortTermTransferRecommendationResponse",
            "short_term_score",
            "short_term_rank",
        ),
    }

    assert set(modes_schema["required"]) == set(expected_modes)

    for (
        mode_name,
        (
            mode_schema_name,
            recommendation_schema_name,
            score_field,
            rank_field,
        ),
    ) in expected_modes.items():
        mode_reference = modes_schema["properties"][mode_name]["$ref"]

        assert mode_reference.endswith(f"/{mode_schema_name}")

        mode_schema = schemas[mode_schema_name]
        mode_property = mode_schema["properties"]["mode"]

        assert mode_property.get("const") == mode_name or mode_property.get("enum") == [mode_name]

        recommendation_reference = mode_schema["properties"]["recommendations"]["items"]["$ref"]

        assert recommendation_reference.endswith(f"/{recommendation_schema_name}")

        recommendation_properties = schemas[recommendation_schema_name]["properties"]

        assert "player_id" in recommendation_properties
        assert "player_name" in recommendation_properties
        assert "recommendation_strength" in recommendation_properties
        assert "why_recommended" in recommendation_properties
        assert "explainability" in recommendation_properties
        assert score_field in recommendation_properties
        assert rank_field in recommendation_properties

        explainability_reference = recommendation_properties["explainability"]["$ref"]

        assert explainability_reference.endswith("/TransferRecommendationExplainabilityResponse")

    explainability_schema = schemas["TransferRecommendationExplainabilityResponse"]

    assert set(explainability_schema["required"]) == {
        "mode",
        "score",
        "signals",
        "bonuses",
        "reasons",
    }

    assert explainability_schema["properties"]["score"]["$ref"].endswith(
        "/TransferExplainabilityScoreResponse"
    )

    signal_reference = explainability_schema["properties"]["signals"]["items"]["$ref"]

    assert signal_reference.endswith("/TransferExplainabilitySignalResponse")

    bonus_reference = explainability_schema["properties"]["bonuses"]["items"]["$ref"]

    assert bonus_reference.endswith("/TransferExplainabilityBonusResponse")

    reason_reference = explainability_schema["properties"]["reasons"]["items"]["$ref"]

    assert reason_reference.endswith("/TransferExplainabilityReasonResponse")


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
                        "recommendation_type": "like_for_like",
                        "recommendation_strength": "strong",
                        "why_recommended": ("Strong immediate replacement profile."),
                        "explainability": _build_explainability_payload(),
                        "immediate_score": 88.5,
                        "immediate_rank": 1,
                    }
                ],
            },
            "development": {
                "mode": "development",
                "recommendations": [],
            },
            "value": {
                "mode": "value",
                "recommendations": [],
            },
            "short_term": {
                "mode": "short_term",
                "recommendations": [],
            },
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


def _build_heatmap_comparison_result() -> HeatmapComparisonResult:
    """Return deterministic measured heatmap comparison evidence."""

    return HeatmapComparisonResult(
        target=HeatmapPlayerResult(
            player_id=10,
            player_name="Michael Olise",
            available=True,
            grid_width=2,
            grid_height=2,
            grid=(
                (0.10, 0.20),
                (0.30, 0.40),
            ),
            matches_with_heatmap=6,
            heatmap_point_count=509,
            weighted_mean_x=61.3,
            weighted_mean_y=41.2,
            peak_cell_x=62.5,
            peak_cell_y=42.5,
            heatmap_entropy=0.944,
        ),
        candidate=HeatmapPlayerResult(
            player_id=20,
            player_name="Dani Olmo",
            available=True,
            grid_width=2,
            grid_height=2,
            grid=(
                (0.15, 0.15),
                (0.25, 0.45),
            ),
            matches_with_heatmap=6,
            heatmap_point_count=268,
            weighted_mean_x=58.5,
            weighted_mean_y=41.7,
            peak_cell_x=57.5,
            peak_cell_y=42.5,
            heatmap_entropy=0.932,
        ),
        similarity=HeatmapSimilarityResult(
            available=True,
            heatmap_similarity_score_pct=90.9,
            heatmap_cosine_similarity_pct=92.8,
            occupation_overlap_pct=81.4,
            peak_zone_similarity_pct=93.9,
            peak_zone_distance=8.58,
            entropy_similarity_pct=98.8,
            target_matches_with_heatmap=6,
            candidate_matches_with_heatmap=6,
            target_heatmap_points=509,
            candidate_heatmap_points=268,
        ),
    )


def test_heatmap_comparison_route_is_in_openapi_schema() -> None:
    application = create_app()
    schema = application.openapi()

    route = (
        "/api/v1/transfer-intelligence/"
        "heatmap-comparison/"
        "{target_player_id}/{candidate_player_id}"
    )

    operation = schema["paths"][route]["get"]

    assert "400" in operation["responses"]
    assert "404" in operation["responses"]
    assert "500" in operation["responses"]
    assert "503" in operation["responses"]

    schemas = schema["components"]["schemas"]

    response_schema = schemas[
        "HeatmapComparisonResponse"
    ]

    assert response_schema["properties"]["target"]["$ref"].endswith(
        "/HeatmapPlayerResponse"
    )
    assert response_schema["properties"]["candidate"]["$ref"].endswith(
        "/HeatmapPlayerResponse"
    )
    assert response_schema["properties"]["similarity"]["$ref"].endswith(
        "/HeatmapSimilarityResponse"
    )

    similarity_properties = schemas[
        "HeatmapSimilarityResponse"
    ]["properties"]

    assert "heatmap_similarity_score_pct" in similarity_properties
    assert "occupation_overlap_pct" in similarity_properties
    assert "peak_zone_distance" in similarity_properties

    assert (
        "effective_heatmap_score_pct"
        not in similarity_properties
    )


def test_heatmap_comparison_endpoint_delegates_player_ids() -> None:
    application = create_app()

    captured_requests: list[
        HeatmapComparisonRequest
    ] = []

    expected = _build_heatmap_comparison_result()

    def fake_runner(
        request: HeatmapComparisonRequest,
    ) -> HeatmapComparisonResult:
        captured_requests.append(
            request
        )

        return expected

    def override_runner() -> HeatmapComparisonRunner:
        return fake_runner

    application.dependency_overrides[
        get_heatmap_comparison_runner
    ] = override_runner

    with TestClient(application) as client:
        response = client.get(
            "/api/v1/transfer-intelligence/"
            "heatmap-comparison/10/20"
        )

    assert response.status_code == 200

    assert captured_requests == [
        HeatmapComparisonRequest(
            target_player_id=10,
            candidate_player_id=20,
        )
    ]

    payload = response.json()

    assert payload["target"]["player_id"] == 10
    assert payload["target"]["player_name"] == "Michael Olise"
    assert payload["target"]["available"] is True
    assert payload["target"]["grid"] == [
        [0.1, 0.2],
        [0.3, 0.4],
    ]

    assert payload["candidate"]["player_id"] == 20

    assert payload["similarity"]["available"] is True
    assert (
        payload["similarity"][
            "heatmap_similarity_score_pct"
        ]
        == 90.9
    )

    assert (
        "effective_heatmap_score_pct"
        not in payload["similarity"]
    )


def test_heatmap_comparison_endpoint_preserves_invalid_request_error() -> None:
    application = create_app()

    def fake_runner(
        request: HeatmapComparisonRequest,
    ) -> HeatmapComparisonResult:
        del request

        raise InvalidTransferAnalysisRequestError(
            "Heatmap comparison requires two different players."
        )

    def override_runner() -> HeatmapComparisonRunner:
        return fake_runner

    application.dependency_overrides[
        get_heatmap_comparison_runner
    ] = override_runner

    with TestClient(application) as client:
        response = client.get(
            "/api/v1/transfer-intelligence/"
            "heatmap-comparison/10/10"
        )

    assert response.status_code == 400



def _build_radar_comparison_result() -> RadarComparisonResult:
    """Return deterministic position-relative radar comparison evidence."""

    target_dimensions = (
        RadarDimensionResult(
            key="creativity",
            label="Creativity",
            raw_score=4.516,
            percentile=100.0,
            peer_count=216,
        ),
        RadarDimensionResult(
            key="progression",
            label="Progression",
            raw_score=2.870,
            percentile=98.6,
            peer_count=216,
        ),
        RadarDimensionResult(
            key="dribbling",
            label="Dribbling",
            raw_score=1.626,
            percentile=94.0,
            peer_count=216,
        ),
    )

    candidate_dimensions = (
        RadarDimensionResult(
            key="creativity",
            label="Creativity",
            raw_score=1.604,
            percentile=91.7,
            peer_count=216,
        ),
        RadarDimensionResult(
            key="progression",
            label="Progression",
            raw_score=0.115,
            percentile=60.6,
            peer_count=216,
        ),
        RadarDimensionResult(
            key="dribbling",
            label="Dribbling",
            raw_score=0.621,
            percentile=79.2,
            peer_count=216,
        ),
    )

    return RadarComparisonResult(
        target=RadarPlayerResult(
            player_id=10,
            player_name="Michael Olise",
            position="M",
            available=True,
            peer_count=216,
            dimensions=target_dimensions,
        ),
        candidate=RadarPlayerResult(
            player_id=20,
            player_name="Dani Olmo",
            position="M",
            available=True,
            peer_count=216,
            dimensions=candidate_dimensions,
        ),
        comparison=RadarComparisonMetadataResult(
            same_position=True,
            overlay_available=True,
            reason=None,
        ),
    )


def test_radar_comparison_route_is_in_openapi_schema() -> None:
    application = create_app()
    schema = application.openapi()

    route = (
        "/api/v1/transfer-intelligence/"
        "radar-comparison/"
        "{target_player_id}/{candidate_player_id}"
    )

    operation = schema["paths"][route]["get"]

    assert "400" in operation["responses"]
    assert "404" in operation["responses"]
    assert "500" in operation["responses"]
    assert "503" in operation["responses"]

    schemas = schema["components"]["schemas"]

    response_schema = schemas[
        "RadarComparisonResponse"
    ]

    assert response_schema["properties"]["target"]["$ref"].endswith(
        "/RadarPlayerResponse"
    )

    assert response_schema["properties"]["candidate"]["$ref"].endswith(
        "/RadarPlayerResponse"
    )

    assert response_schema["properties"]["comparison"]["$ref"].endswith(
        "/RadarComparisonMetadataResponse"
    )

    player_schema = schemas[
        "RadarPlayerResponse"
    ]

    dimension_reference = (
        player_schema[
            "properties"
        ][
            "dimensions"
        ][
            "items"
        ][
            "$ref"
        ]
    )

    assert dimension_reference.endswith(
        "/RadarDimensionResponse"
    )

    dimension_properties = schemas[
        "RadarDimensionResponse"
    ]["properties"]

    assert "raw_score" in dimension_properties
    assert "percentile" in dimension_properties
    assert "peer_count" in dimension_properties


def test_radar_comparison_endpoint_delegates_player_ids() -> None:
    application = create_app()

    captured_requests: list[
        RadarComparisonRequest
    ] = []

    expected = _build_radar_comparison_result()

    def fake_runner(
        request: RadarComparisonRequest,
    ) -> RadarComparisonResult:
        captured_requests.append(
            request
        )

        return expected

    def override_runner() -> RadarComparisonRunner:
        return fake_runner

    application.dependency_overrides[
        get_radar_comparison_runner
    ] = override_runner

    with TestClient(application) as client:
        response = client.get(
            "/api/v1/transfer-intelligence/"
            "radar-comparison/10/20"
        )

    assert response.status_code == 200

    assert captured_requests == [
        RadarComparisonRequest(
            target_player_id=10,
            candidate_player_id=20,
        )
    ]

    payload = response.json()

    assert payload["target"]["player_id"] == 10
    assert payload["target"]["player_name"] == "Michael Olise"
    assert payload["target"]["position"] == "M"
    assert payload["target"]["available"] is True
    assert payload["target"]["peer_count"] == 216

    assert payload["target"]["dimensions"][0] == {
        "key": "creativity",
        "label": "Creativity",
        "raw_score": 4.516,
        "percentile": 100.0,
        "peer_count": 216,
    }

    assert payload["candidate"]["player_id"] == 20
    assert payload["candidate"]["player_name"] == "Dani Olmo"

    assert payload["comparison"] == {
        "same_position": True,
        "overlay_available": True,
        "reason": None,
    }


def test_radar_comparison_endpoint_preserves_invalid_request_error() -> None:
    application = create_app()

    def fake_runner(
        request: RadarComparisonRequest,
    ) -> RadarComparisonResult:
        del request

        raise InvalidTransferAnalysisRequestError(
            "Radar comparison requires two different players."
        )

    def override_runner() -> RadarComparisonRunner:
        return fake_runner

    application.dependency_overrides[
        get_radar_comparison_runner
    ] = override_runner

    with TestClient(application) as client:
        response = client.get(
            "/api/v1/transfer-intelligence/"
            "radar-comparison/10/10"
        )

    assert response.status_code == 400

    assert response.json() == {
        "error": {
            "code": "invalid_transfer_analysis_request",
            "message": (
                "Radar comparison requires two different players."
            ),
        }
    }
