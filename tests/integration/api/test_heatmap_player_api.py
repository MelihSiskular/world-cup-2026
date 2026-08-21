"""Real-data smoke test for the single-player heatmap API."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wc26.analytics.transfer_intelligence.catalog import (
    load_transfer_data_catalog,
)
from wc26.api import create_app

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("WC26_RUN_INTEGRATION") != "1",
        reason=(
            "Set WC26_RUN_INTEGRATION=1 "
            "to run real-data integration tests."
        ),
    ),
]


def test_heatmap_player_api_uses_real_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = Path(__file__).resolve().parents[3]

    monkeypatch.chdir(project_root)

    application = create_app(
        catalog_loader=load_transfer_data_catalog,
    )

    with TestClient(application) as client:
        response = client.get(
            "/api/v1/transfer-intelligence/heatmap/978838"
        )

    assert response.status_code == 200, response.text

    payload = response.json()

    assert payload["player_id"] == 978838
    assert payload["player_name"] == "Michael Olise"
    assert payload["available"] is True

    assert isinstance(
        payload["grid_width"],
        int,
    )
    assert isinstance(
        payload["grid_height"],
        int,
    )
    assert isinstance(
        payload["grid"],
        list,
    )

    assert isinstance(
        payload["weighted_mean_x"],
        float,
    )
    assert isinstance(
        payload["weighted_mean_y"],
        float,
    )
