from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest
from pytest import MonkeyPatch
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
        minimum_minutes=150.0,
        minimum_role_confidence=50.0,
        maximum_market_value=None,
        neutral_heatmap_score=70.0,
    )

    with pytest.raises(FrozenInstanceError):
        request.player = "Dani Olmo"


def test_legacy_main_delegates_to_console(
    monkeypatch: MonkeyPatch,
) -> None:
    calls: list[None] = []

    def fake_run_console() -> None:
        calls.append(None)

    monkeypatch.setattr(
        legacy,
        "run_console",
        fake_run_console,
    )

    legacy.main()

    assert calls == [None]


def test_transfer_analysis_request_keeps_name_compatibility() -> None:
    request = TransferAnalysisRequest(
        player="Michael Olise",
        features=Path("features.csv"),
        similarity=Path("similarity.csv"),
        heatmap_similarity=Path("heatmap-similarity.csv"),
        heatmap_profiles=Path("heatmap-profiles.csv"),
        minimum_minutes=150,
        minimum_role_confidence=50,
        maximum_market_value=None,
        neutral_heatmap_score=70,
    )

    assert request.player == "Michael Olise"
    assert request.player_id is None


def test_transfer_analysis_request_accepts_player_id() -> None:
    request = TransferAnalysisRequest(
        player=None,
        player_id=978838,
        features=Path("features.csv"),
        similarity=Path("similarity.csv"),
        heatmap_similarity=Path("heatmap-similarity.csv"),
        heatmap_profiles=Path("heatmap-profiles.csv"),
        minimum_minutes=150,
        minimum_role_confidence=50,
        maximum_market_value=None,
        neutral_heatmap_score=70,
    )

    assert request.player is None
    assert request.player_id == 978838
