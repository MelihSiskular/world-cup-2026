from __future__ import annotations

from typing import Any

import pandas as pd
from pytest import MonkeyPatch

from wc26.analytics.transfer_intelligence import reporting
from wc26.analytics.transfer_intelligence.models import (
    TransferAnalysisResult,
    TransferModeResult,
    TransferRecommendation,
)
from wc26.analytics.transfer_intelligence.utils import (
    format_market_value,
    format_optional_score,
)


def test_print_transfer_report_adapts_structured_result(
    monkeypatch: MonkeyPatch,
) -> None:
    result = TransferAnalysisResult(
        target={
            "player_name": "Michael Olise",
            "position": "M",
        },
        modes=(
            TransferModeResult(
                mode="immediate",
                recommendations=(
                    TransferRecommendation(
                        data={
                            "player_name": "Dani Olmo",
                            "recommendation_score": 91.2,
                        }
                    ),
                ),
            ),
            TransferModeResult(
                mode="development",
                recommendations=(),
            ),
        ),
    )

    captured_target: pd.Series[Any] | None = None
    captured_results: dict[str, pd.DataFrame] | None = None
    captured_top_n: int | None = None

    def fake_print_report(
        target: pd.Series[Any],
        results: dict[str, pd.DataFrame],
        top_n: int,
    ) -> None:
        nonlocal captured_target
        nonlocal captured_results
        nonlocal captured_top_n

        captured_target = target
        captured_results = results
        captured_top_n = top_n

    monkeypatch.setattr(
        reporting,
        "print_report",
        fake_print_report,
    )

    reporting.print_transfer_report(
        result,
        top_n=5,
    )

    assert captured_target is not None
    assert captured_target.to_dict() == {
        "player_name": "Michael Olise",
        "position": "M",
    }

    assert captured_results is not None
    assert set(captured_results) == {
        "immediate",
        "development",
    }

    assert captured_results["immediate"].to_dict(orient="records") == [
        {
            "player_name": "Dani Olmo",
            "recommendation_score": 91.2,
        }
    ]

    assert captured_results["development"].empty
    assert captured_top_n == 5


def test_reporting_uses_formatting_utilities() -> None:
    assert reporting.format_market_value is format_market_value
    assert reporting.format_optional_score is format_optional_score
