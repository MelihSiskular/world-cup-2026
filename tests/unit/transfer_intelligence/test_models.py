"""Tests for transfer intelligence contract models."""

from __future__ import annotations

import json
from pathlib import Path

from wc26.analytics.transfer_intelligence.models import (
    TransferAnalysisRequest,
    TransferAnalysisResult,
    TransferModeResult,
    TransferRecommendation,
)


def test_transfer_analysis_request_stores_input_contract(
    tmp_path: Path,
) -> None:
    request = TransferAnalysisRequest(
        player="Michael Olise",
        features=tmp_path / "features.csv",
        similarity=tmp_path / "similarity.csv",
        heatmap_similarity=tmp_path / "heatmap_similarity.csv",
        heatmap_profiles=tmp_path / "heatmap_profiles.csv",
        output_dir=tmp_path / "results",
        minimum_minutes=150.0,
        minimum_role_confidence=50.0,
        maximum_market_value=80_000_000.0,
        neutral_heatmap_score=70.0,
        top_n=5,
    )

    assert request.player == "Michael Olise"
    assert request.top_n == 5
    assert request.maximum_market_value == 80_000_000.0


def test_transfer_recommendation_returns_detached_dictionary() -> None:
    recommendation = TransferRecommendation(
        data={
            "player_name": "Dani Olmo",
            "recommendation_score": 91.2,
        }
    )

    result = recommendation.to_dict()
    result["player_name"] = "Changed Player"

    assert recommendation.data["player_name"] == "Dani Olmo"


def test_transfer_analysis_result_is_json_serializable() -> None:
    recommendation = TransferRecommendation(
        data={
            "player_name": "Dani Olmo",
            "recommendation_score": 91.2,
            "market_value_eur": 60_000_000,
            "optional_metric": None,
        }
    )

    mode = TransferModeResult(
        mode="immediate",
        recommendations=(recommendation,),
    )

    result = TransferAnalysisResult(
        target={
            "player_name": "Michael Olise",
            "position": "M",
        },
        modes=(mode,),
    )

    serialized = result.to_dict()

    assert serialized == {
        "target": {
            "player_name": "Michael Olise",
            "position": "M",
        },
        "modes": {
            "immediate": {
                "mode": "immediate",
                "recommendations": [
                    {
                        "player_name": "Dani Olmo",
                        "recommendation_score": 91.2,
                        "market_value_eur": 60_000_000,
                        "optional_metric": None,
                    }
                ],
            }
        },
    }

    assert json.loads(json.dumps(serialized)) == serialized
