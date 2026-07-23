"""Tests for transfer intelligence CSV exporters."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from wc26.analytics.transfer_intelligence.exporting import (
    export_transfer_csv,
)
from wc26.analytics.transfer_intelligence.models import (
    TransferAnalysisResult,
    TransferModeResult,
    TransferRecommendation,
)


def test_export_transfer_csv_writes_non_empty_modes(
    tmp_path: Path,
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
                            "market_value_eur": 60_000_000,
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

    exported_files = export_transfer_csv(
        result,
        tmp_path,
    )

    expected_path = tmp_path / "michael_olise_immediate_recommendations.csv"

    assert exported_files == (expected_path,)
    assert expected_path.exists()

    exported_frame = pd.read_csv(expected_path)

    assert exported_frame.to_dict(orient="records") == [
        {
            "player_name": "Dani Olmo",
            "recommendation_score": 91.2,
            "market_value_eur": 60_000_000,
        }
    ]

    assert not (tmp_path / "michael_olise_development_recommendations.csv").exists()


def test_export_transfer_csv_rejects_missing_player_name(
    tmp_path: Path,
) -> None:
    result = TransferAnalysisResult(
        target={
            "position": "M",
        },
        modes=(),
    )

    with pytest.raises(
        ValueError,
        match="valid player_name",
    ):
        export_transfer_csv(
            result,
            tmp_path,
        )
