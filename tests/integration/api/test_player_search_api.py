"""Real-data smoke tests for the Player Search API."""

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


def test_player_search_api_uses_real_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(project_root)

    application = create_app()

    with TestClient(application) as client:
        response = client.get(
            "/api/v1/players/search",
            params={
                "q": "olise",
                "limit": 10,
            },
        )

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/json")

    payload = response.json()

    assert payload["query"] == "olise"
    assert payload["count"] >= 1
    assert payload["count"] == len(payload["players"])

    player_names = {player["player_name"] for player in payload["players"]}

    assert "Michael Olise" in player_names

    michael_olise = next(
        player for player in payload["players"] if player["player_name"] == "Michael Olise"
    )

    assert isinstance(
        michael_olise["player_id"],
        int,
    )
    assert michael_olise["national_team_name"]
    assert michael_olise["position"]

    assert (
        json.loads(
            json.dumps(
                payload,
                allow_nan=False,
            )
        )
        == payload
    )


def test_player_search_api_matches_without_diacritics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(project_root)

    application = create_app()

    with TestClient(application) as client:
        response = client.get(
            "/api/v1/players/search",
            params={
                "q": "modric",
            },
        )

    assert response.status_code == 200

    player_names = {player["player_name"] for player in response.json()["players"]}

    assert "Luka Modrić" in player_names
