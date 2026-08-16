"""Real-data smoke tests for comparison visualization APIs."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wc26.analytics.transfer_intelligence import (
    catalog as catalog_module,
)
from wc26.api import create_app

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("WC26_RUN_INTEGRATION") != "1",
        reason="Set WC26_RUN_INTEGRATION=1 to run real-data integration tests.",
    ),
]


PROJECT_ROOT = Path(__file__).resolve().parents[3]

TARGET_PLAYER_ID = 978838
TARGET_PLAYER_NAME = "Michael Olise"

CANDIDATE_PLAYER_ID = 789071
CANDIDATE_PLAYER_NAME = "Dani Olmo"


def test_heatmap_comparison_api_uses_real_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Build a measured heatmap comparison from the runtime datasets."""

    monkeypatch.chdir(PROJECT_ROOT)

    application = create_app(
        catalog_loader=(catalog_module.load_transfer_data_catalog),
    )

    with TestClient(application) as client:
        response = client.get(
            "/api/v1/transfer-intelligence/"
            f"heatmap-comparison/{TARGET_PLAYER_ID}/{CANDIDATE_PLAYER_ID}"
        )

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/json")

    payload = response.json()

    assert payload["target"]["player_id"] == TARGET_PLAYER_ID
    assert payload["target"]["player_name"] == TARGET_PLAYER_NAME
    assert payload["target"]["available"] is True

    assert payload["candidate"]["player_id"] == CANDIDATE_PLAYER_ID
    assert payload["candidate"]["player_name"] == CANDIDATE_PLAYER_NAME
    assert payload["candidate"]["available"] is True

    assert (
        json.loads(
            json.dumps(
                payload,
                allow_nan=False,
            )
        )
        == payload
    )


def test_radar_comparison_api_uses_real_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Build a same-position radar overlay from the runtime datasets."""

    monkeypatch.chdir(PROJECT_ROOT)

    application = create_app(
        catalog_loader=(catalog_module.load_transfer_data_catalog),
    )

    with TestClient(application) as client:
        response = client.get(
            "/api/v1/transfer-intelligence/"
            f"radar-comparison/{TARGET_PLAYER_ID}/{CANDIDATE_PLAYER_ID}"
        )

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/json")

    payload = response.json()

    target = payload["target"]
    candidate = payload["candidate"]
    comparison = payload["comparison"]

    assert target["player_id"] == TARGET_PLAYER_ID
    assert target["player_name"] == TARGET_PLAYER_NAME
    assert target["position"] == "M"
    assert target["available"] is True
    assert target["peer_count"] > 0

    assert candidate["player_id"] == CANDIDATE_PLAYER_ID
    assert candidate["player_name"] == CANDIDATE_PLAYER_NAME
    assert candidate["position"] == "M"
    assert candidate["available"] is True
    assert candidate["peer_count"] > 0

    assert target["peer_count"] == candidate["peer_count"]

    target_dimensions = target["dimensions"]
    candidate_dimensions = candidate["dimensions"]

    assert len(target_dimensions) >= 3
    assert len(candidate_dimensions) >= 3

    assert [dimension["key"] for dimension in target_dimensions] == [
        dimension["key"] for dimension in candidate_dimensions
    ]

    for dimension in target_dimensions + candidate_dimensions:
        percentile = dimension["percentile"]

        assert percentile is not None
        assert 0.0 <= percentile <= 100.0
        assert dimension["peer_count"] > 0

    assert comparison == {
        "same_position": True,
        "overlay_available": True,
        "reason": None,
    }

    assert (
        json.loads(
            json.dumps(
                payload,
                allow_nan=False,
            )
        )
        == payload
    )
