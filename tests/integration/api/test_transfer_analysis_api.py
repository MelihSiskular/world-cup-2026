"""Real-data smoke tests for the Transfer Intelligence API."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wc26.api import create_app

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("WC26_RUN_INTEGRATION") != "1",
        reason=("Set WC26_RUN_INTEGRATION=1 to run real-data integration tests."),
    ),
]


def test_transfer_analysis_api_uses_real_datasets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(project_root)

    application = create_app()

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/transfer-intelligence/analyze",
            json={
                "player": "Michael Olise",
                "minimum_minutes": 150,
                "minimum_role_confidence": 50,
                "maximum_market_value": None,
                "neutral_heatmap_score": 70,
            },
        )

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/json")

    payload = response.json()

    assert payload["target"]["player_name"] == "Michael Olise"

    expected_modes = {
        "immediate",
        "development",
        "value",
        "short_term",
    }

    assert set(payload["modes"]) == expected_modes

    for mode_name, mode_result in payload["modes"].items():
        assert mode_result["mode"] == mode_name
        assert isinstance(
            mode_result["recommendations"],
            list,
        )

    recommendation_counts = [
        len(mode_result["recommendations"]) for mode_result in payload["modes"].values()
    ]

    assert any(count > 0 for count in recommendation_counts)

    assert (
        json.loads(
            json.dumps(
                payload,
                allow_nan=False,
            )
        )
        == payload
    )
