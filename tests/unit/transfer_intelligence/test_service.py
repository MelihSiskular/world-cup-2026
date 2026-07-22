from __future__ import annotations

from argparse import Namespace
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from src.transfer_intelligence import (
    find_replacements as legacy,
)

from wc26.analytics.transfer_intelligence.service import (
    TransferAnalysisRequest,
)


def test_transfer_request_is_immutable() -> None:
    request = TransferAnalysisRequest(
        player="Michael Olise",
        features=Path("features.csv"),
        similarity=Path("similarity.csv"),
        heatmap_similarity=Path("heatmap_similarity.csv"),
        heatmap_profiles=Path("heatmap_profiles.csv"),
        output_dir=Path("results"),
        minimum_minutes=180.0,
        minimum_role_confidence=50.0,
        maximum_market_value=None,
        neutral_heatmap_score=50.0,
        top_n=10,
    )

    with pytest.raises(FrozenInstanceError):
        request.top_n = 20  # type: ignore[misc]


def test_main_builds_request_and_delegates(
    monkeypatch,
) -> None:
    args = Namespace(
        player="Michael Olise",
        features="features.csv",
        similarity="similarity.csv",
        heatmap_similarity="heatmap_similarity.csv",
        heatmap_profiles="heatmap_profiles.csv",
        output_dir="results",
        minimum_minutes=180.0,
        minimum_role_confidence=50.0,
        maximum_market_value=75_000_000.0,
        neutral_heatmap_score=50.0,
        top_n=10,
    )

    received_requests: list[TransferAnalysisRequest] = []

    monkeypatch.setattr(
        legacy,
        "parse_args",
        lambda: args,
    )
    monkeypatch.setattr(
        legacy,
        "run_transfer_analysis",
        received_requests.append,
    )

    legacy.main()

    assert received_requests == [
        TransferAnalysisRequest(
            player="Michael Olise",
            features=Path("features.csv"),
            similarity=Path("similarity.csv"),
            heatmap_similarity=Path("heatmap_similarity.csv"),
            heatmap_profiles=Path("heatmap_profiles.csv"),
            output_dir=Path("results"),
            minimum_minutes=180.0,
            minimum_role_confidence=50.0,
            maximum_market_value=75_000_000.0,
            neutral_heatmap_score=50.0,
            top_n=10,
        )
    ]
