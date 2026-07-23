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
        output_dir=Path("results"),
        minimum_minutes=180.0,
        minimum_role_confidence=50.0,
        maximum_market_value=None,
        neutral_heatmap_score=50.0,
        top_n=10,
    )

    with pytest.raises(FrozenInstanceError):
        request.top_n = 20  # type: ignore[misc]


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
