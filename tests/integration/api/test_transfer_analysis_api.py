"""Real-data smoke tests for the Transfer Intelligence API."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

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


EXPECTED_MODES = {
    "immediate",
    "development",
    "value",
    "short_term",
}


def _assert_valid_explainability(
    recommendation: dict[str, Any],
    *,
    mode_name: str,
) -> None:
    """Validate one real recommendation explanation."""

    explanation = recommendation["explainability"]

    assert explanation["mode"] == mode_name

    score = explanation["score"]

    assert score["final_score"] == pytest.approx(recommendation[f"{mode_name}_score"])

    assert score["weighted_signal_total"] + score["bonus_total"] == pytest.approx(
        score["pre_clip_score"],
        abs=0.02,
    )

    expected_final_score = min(
        100.0,
        max(
            0.0,
            score["pre_clip_score"],
        ),
    )

    assert score["final_score"] == pytest.approx(
        expected_final_score,
        abs=0.01,
    )

    assert score["was_clipped"] is (
        score["pre_clip_score"] < 0.0 or score["pre_clip_score"] > 100.0
    )

    signals = explanation["signals"]

    assert len(signals) == 8

    assert {signal["key"] for signal in signals} == {
        "statistical_similarity_pct",
        "role_fit_pct",
        "spatial_similarity_pct",
        "effective_heatmap_score_pct",
        "player_quality_score",
        "data_reliability_score",
        "market_value_advantage_pct",
        "age_suitability_pct",
    }

    heatmap_signal = next(
        signal for signal in signals if signal["key"] == "effective_heatmap_score_pct"
    )

    assert heatmap_signal["evidence_status"] in {
        "available",
        "fallback",
        "missing",
    }

    if heatmap_signal["evidence_status"] == "fallback":
        assert heatmap_signal["source_score"] is None

    if heatmap_signal["evidence_status"] == "available":
        assert heatmap_signal["source_score"] is not None

    bonuses = explanation["bonuses"]

    assert {bonus["key"] for bonus in bonuses} == {
        "same_final_role",
        "same_archetype",
    }

    reasons = explanation["reasons"]

    assert 1 <= len(reasons) <= 4

    assert recommendation["why_recommended"] == "; ".join(reason["text"] for reason in reasons)


def _assert_valid_analysis_payload(
    payload: dict[str, Any],
    *,
    expected_player_id: int,
    expected_player_name: str,
) -> None:
    """Validate the stable Transfer Analysis response contract."""

    assert payload["target"]["player_id"] == expected_player_id
    assert payload["target"]["player_name"] == expected_player_name

    assert set(payload["modes"]) == EXPECTED_MODES

    for mode_name, mode_result in payload["modes"].items():
        assert mode_result["mode"] == mode_name
        assert isinstance(
            mode_result["recommendations"],
            list,
        )

        for recommendation in mode_result["recommendations"]:
            _assert_valid_explainability(
                recommendation,
                mode_name=mode_name,
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


def test_transfer_analysis_api_preserves_name_based_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Run the analysis using the existing player-name contract."""

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

    _assert_valid_analysis_payload(
        response.json(),
        expected_player_id=978838,
        expected_player_name="Michael Olise",
    )


def test_search_result_can_open_profile_and_run_analysis_by_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify the complete stable-identity client flow."""

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

        assert search_response.status_code == 200, search_response.text

        search_payload = search_response.json()

        michael_olise = next(
            player
            for player in search_payload["players"]
            if player["player_name"] == "Michael Olise"
        )

        player_id = michael_olise["player_id"]

        profile_response = client.get(f"/api/v1/players/{player_id}")

        assert profile_response.status_code == 200, profile_response.text

        profile_payload = profile_response.json()

        analysis_response = client.post(
            "/api/v1/transfer-intelligence/analyze",
            json={
                "player_id": player_id,
                "minimum_minutes": 150,
                "minimum_role_confidence": 50,
                "maximum_market_value": None,
                "neutral_heatmap_score": 70,
            },
        )

    assert player_id == 978838

    assert profile_payload["player_id"] == player_id
    assert profile_payload["player_name"] == michael_olise["player_name"]

    assert analysis_response.status_code == 200, analysis_response.text
    assert analysis_response.headers["content-type"].startswith("application/json")

    analysis_payload = analysis_response.json()

    _assert_valid_analysis_payload(
        analysis_payload,
        expected_player_id=player_id,
        expected_player_name=profile_payload["player_name"],
    )
