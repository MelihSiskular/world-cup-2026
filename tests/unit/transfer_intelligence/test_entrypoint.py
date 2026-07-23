"""Tests for the transfer intelligence console entrypoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from pytest import MonkeyPatch

from wc26.analytics.transfer_intelligence import entrypoint
from wc26.analytics.transfer_intelligence.models import (
    TransferAnalysisRequest,
    TransferAnalysisResult,
)


def test_main_builds_request_and_orchestrates_outputs(
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

    analysis_result = TransferAnalysisResult(
        target={
            "player_name": "Michael Olise",
        },
        modes=(),
    )

    captured_request: TransferAnalysisRequest | None = None

    report_calls: list[tuple[TransferAnalysisResult, int]] = []

    export_calls: list[tuple[TransferAnalysisResult, Path]] = []

    operation_order: list[str] = []

    def fake_parse_args() -> argparse.Namespace:
        return args

    def fake_run_transfer_analysis(
        request: TransferAnalysisRequest,
    ) -> TransferAnalysisResult:
        nonlocal captured_request

        operation_order.append("service")
        captured_request = request

        return analysis_result

    def fake_print_transfer_report(
        result: TransferAnalysisResult,
        top_n: int,
    ) -> None:
        operation_order.append("report")

        report_calls.append(
            (
                result,
                top_n,
            )
        )

    def fake_export_transfer_csv(
        result: TransferAnalysisResult,
        output_path: Path,
    ) -> tuple[Path, ...]:
        operation_order.append("export")

        export_calls.append(
            (
                result,
                output_path,
            )
        )

        return ()

    monkeypatch.setattr(
        entrypoint,
        "parse_args",
        fake_parse_args,
    )
    monkeypatch.setattr(
        entrypoint,
        "run_transfer_analysis",
        fake_run_transfer_analysis,
    )
    monkeypatch.setattr(
        entrypoint,
        "print_transfer_report",
        fake_print_transfer_report,
    )
    monkeypatch.setattr(
        entrypoint,
        "export_transfer_csv",
        fake_export_transfer_csv,
    )

    entrypoint.main()

    assert captured_request == TransferAnalysisRequest(
        player="Michael Olise",
        features=features,
        similarity=similarity,
        heatmap_similarity=heatmap_similarity,
        heatmap_profiles=heatmap_profiles,
        minimum_minutes=250.0,
        minimum_role_confidence=65.0,
        maximum_market_value=100_000_000.0,
        neutral_heatmap_score=72.0,
    )

    assert report_calls == [
        (
            analysis_result,
            7,
        )
    ]

    assert export_calls == [
        (
            analysis_result,
            output_dir,
        )
    ]

    assert operation_order == [
        "service",
        "report",
        "export",
    ]
