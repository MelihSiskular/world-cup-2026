"""Tests for Transfer Intelligence API error responses."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from wc26.analytics.transfer_intelligence.errors import (
    AmbiguousPlayerError,
    DatasetNotFoundError,
    InvalidDatasetError,
    PlayerNotFoundError,
)
from wc26.analytics.transfer_intelligence.models import (
    TransferAnalysisRequest,
    TransferAnalysisResult,
)
from wc26.api import create_app
from wc26.api.dependencies import (
    TransferAnalysisRunner,
    get_transfer_analysis_runner,
)

type ErrorFactory = Callable[[], Exception]


@pytest.mark.parametrize(
    (
        "error_factory",
        "expected_status",
        "expected_code",
        "expected_message",
    ),
    [
        (
            lambda: PlayerNotFoundError("Player not found: Missing Player"),
            404,
            "player_not_found",
            "Player not found: Missing Player",
        ),
        (
            lambda: AmbiguousPlayerError("Multiple players matched: Alex Smith, Alex Jones"),
            409,
            "ambiguous_player",
            ("Multiple players matched: Alex Smith, Alex Jones"),
        ),
        (
            lambda: DatasetNotFoundError("Similarity file not found: /private/data.csv"),
            503,
            "dataset_unavailable",
            "A required transfer dataset is unavailable.",
        ),
        (
            lambda: InvalidDatasetError("Missing similarity columns: player_id"),
            503,
            "invalid_dataset",
            ("A transfer dataset does not satisfy the required data contract."),
        ),
    ],
)
def test_transfer_analysis_endpoint_returns_domain_errors(
    error_factory: ErrorFactory,
    expected_status: int,
    expected_code: str,
    expected_message: str,
) -> None:
    application = create_app()

    def failing_runner(
        request: TransferAnalysisRequest,
    ) -> TransferAnalysisResult:
        del request
        raise error_factory()

    def override_analysis_runner() -> TransferAnalysisRunner:
        return failing_runner

    application.dependency_overrides[get_transfer_analysis_runner] = override_analysis_runner

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/transfer-intelligence/analyze",
            json={
                "player": "Missing Player",
            },
        )

    assert response.status_code == expected_status
    assert response.json() == {
        "error": {
            "code": expected_code,
            "message": expected_message,
        }
    }


def test_transfer_analysis_endpoint_hides_unexpected_errors() -> None:
    application = create_app()

    def failing_runner(
        request: TransferAnalysisRequest,
    ) -> TransferAnalysisResult:
        del request
        raise RuntimeError("sensitive internal implementation detail")

    def override_analysis_runner() -> TransferAnalysisRunner:
        return failing_runner

    application.dependency_overrides[get_transfer_analysis_runner] = override_analysis_runner

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/transfer-intelligence/analyze",
            json={
                "player": "Michael Olise",
            },
        )

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "analysis_failed",
            "message": ("Transfer analysis could not be completed."),
        }
    }

    assert "sensitive internal implementation detail" not in response.text


def test_transfer_analysis_openapi_documents_error_responses() -> None:
    application = create_app()

    operation = application.openapi()["paths"]["/api/v1/transfer-intelligence/analyze"]["post"]

    assert "404" in operation["responses"]
    assert "409" in operation["responses"]
    assert "500" in operation["responses"]
    assert "503" in operation["responses"]
