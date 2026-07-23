"""Tests for the transfer intelligence console entrypoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from pytest import MonkeyPatch

from wc26.analytics.transfer_intelligence import entrypoint
from wc26.analytics.transfer_intelligence.models import (
    TransferAnalysisResult,
)
from wc26.analytics.transfer_intelligence.service import (
    TransferAnalysisRequest,
)


def test_main_builds_request_and_runs_service(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    features = tmp_path / "features.csv"
    similarity = tmp_path / "similarity.csv"
    heatmap_similarity = tmp_path / "heatmap_similarity.csv"
    heatmap_profiles = tmp_path / "heatmap_profiles.csv"
    output_dir = tmp_path / "output"

    args = argparse.Namespace(
        player="Michael Olise",
        features=features,
        similarity=similarity,
        heatmap_similarity=heatmap_similarity,
        heatmap_profiles=heatmap_profiles,
        output_dir=output_dir,
        minimum_minutes=250.0,
        minimum_role_confidence=65.0,
        maximum_market_value=100_000_000.0,
        neutral_heatmap_score=72.0,
        top_n=7,
    )

    captured_request: TransferAnalysisRequest | None = None

    def fake_parse_args() -> argparse.Namespace:
        return args

    def fake_run_transfer_analysis(
        request: TransferAnalysisRequest,
    ) -> TransferAnalysisResult:
        nonlocal captured_request
        captured_request = request

        return TransferAnalysisResult(
            target={},
            modes=(),
        )

    monkeypatch.setattr(entrypoint, "parse_args", fake_parse_args)
    monkeypatch.setattr(
        entrypoint,
        "run_transfer_analysis",
        fake_run_transfer_analysis,
    )

    entrypoint.main()

    assert captured_request == TransferAnalysisRequest(
        player="Michael Olise",
        features=features,
        similarity=similarity,
        heatmap_similarity=heatmap_similarity,
        heatmap_profiles=heatmap_profiles,
        output_dir=output_dir,
        minimum_minutes=250.0,
        minimum_role_confidence=65.0,
        maximum_market_value=100_000_000.0,
        neutral_heatmap_score=72.0,
        top_n=7,
    )
