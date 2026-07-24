"""Real-data smoke tests for the Player Profile API."""

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


def test_player_profile_api_uses_real_dataset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Retrieve Michael Olise through his stable player ID."""

    project_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(project_root)

    application = create_app()

    with TestClient(application) as client:
        response = client.get("/api/v1/players/978838")

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/json")

    payload = response.json()

    assert payload["player_id"] == 978838
    assert payload["player_name"] == "Michael Olise"
    assert payload["national_team_name"] == "France"
    assert payload["country_name"] == "France"
    assert payload["position"] == "M"

    assert payload["final_role"]
    assert payload["archetype"]
    assert payload["market_value_currency"] == "EUR"

    assert isinstance(
        payload["appearances"],
        int,
    )
    assert isinstance(
        payload["starts"],
        int,
    )
    assert isinstance(
        payload["weighted_rating"],
        float,
    )

    assert (
        json.loads(
            json.dumps(
                payload,
                allow_nan=False,
            )
        )
        == payload
    )


def test_player_search_result_can_open_player_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the complete autocomplete-to-profile client flow."""

    project_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(project_root)

    application = create_app()

    with TestClient(application) as client:
        search_response = client.get(
            "/api/v1/players/search",
            params={
                "q": "olise",
                "limit": 10,
            },
        )

        assert search_response.status_code == 200

        search_payload = search_response.json()

        michael_olise = next(
            player
            for player in search_payload["players"]
            if player["player_name"] == "Michael Olise"
        )

        profile_response = client.get(f"/api/v1/players/{michael_olise['player_id']}")

    assert profile_response.status_code == 200

    profile_payload = profile_response.json()

    assert michael_olise["player_id"] == 978838
    assert profile_payload["player_id"] == (michael_olise["player_id"])
    assert profile_payload["player_name"] == (michael_olise["player_name"])
    assert profile_payload["national_team_name"] == (michael_olise["national_team_name"])
    assert profile_payload["position"] == (michael_olise["position"])


def test_player_profile_api_returns_not_found_for_unknown_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return the standard error contract for an unknown player ID."""

    project_root = Path(__file__).resolve().parents[3]
    monkeypatch.chdir(project_root)

    application = create_app()

    with TestClient(application) as client:
        response = client.get("/api/v1/players/999999999")

    assert response.status_code == 404

    assert response.json() == {
        "error": {
            "code": "player_not_found",
            "message": ("Player not found for ID: 999999999"),
        }
    }
