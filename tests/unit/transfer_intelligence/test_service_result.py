"""Tests for structured transfer analysis service results."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from pytest import CaptureFixture, MonkeyPatch

from wc26.analytics.transfer_intelligence import service
from wc26.analytics.transfer_intelligence.config import (
    MODE_CONFIG,
)
from wc26.analytics.transfer_intelligence.models import (
    TransferAnalysisRequest,
    TransferAnalysisResult,
)


def test_run_transfer_analysis_returns_structured_result(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    players = pd.DataFrame(
        {
            "player_id": ["10"],
            "player_name": ["Michael Olise"],
        }
    )

    target = pd.Series(
        {
            "player_id": np.int64(10),
            "player_name": "Michael Olise",
            "position": "M",
            "rating": np.float64(8.4),
            "optional_metric": np.nan,
            "pandas_missing": pd.NA,
            "missing_date": pd.NaT,
        }
    )

    base_candidates = pd.DataFrame(
        {
            "player_id": [20],
            "player_name": ["Dani Olmo"],
        }
    )

    mode_names = tuple(MODE_CONFIG)
    first_mode = mode_names[0]

    def fake_generate_mode_results(
        candidates: pd.DataFrame,
        mode: str,
        target_heatmap_profile: object,
    ) -> pd.DataFrame:
        assert candidates is base_candidates
        assert target_heatmap_profile == {
            "left": 0.4,
            "centre": 0.6,
        }

        if mode != first_mode:
            return pd.DataFrame()

        return pd.DataFrame(
            [
                {
                    "player_id": np.int64(20),
                    "player_name": "Dani Olmo",
                    "recommendation_score": np.float64(91.2),
                    "market_value_eur": np.int64(60_000_000),
                    "missing_metric": np.nan,
                }
            ]
        )

    monkeypatch.setattr(
        service.pd,
        "read_csv",
        lambda *args, **kwargs: players.copy(),
    )
    monkeypatch.setattr(
        service,
        "load_similarity",
        lambda path: pd.DataFrame(),
    )
    monkeypatch.setattr(
        service,
        "load_heatmap_similarity",
        lambda path: pd.DataFrame(),
    )
    monkeypatch.setattr(
        service,
        "load_heatmap_profiles",
        lambda path: pd.DataFrame(),
    )
    monkeypatch.setattr(
        service,
        "resolve_player",
        lambda player_frame, player_name: target,
    )
    monkeypatch.setattr(
        service,
        "prepare_candidate_base",
        lambda **kwargs: (
            base_candidates,
            {
                "left": 0.4,
                "centre": 0.6,
            },
        ),
    )
    monkeypatch.setattr(
        service,
        "generate_mode_results",
        fake_generate_mode_results,
    )

    request = TransferAnalysisRequest(
        player="Michael Olise",
        features=tmp_path / "features.csv",
        similarity=tmp_path / "similarity.csv",
        heatmap_similarity=tmp_path / "heatmap_similarity.csv",
        heatmap_profiles=tmp_path / "heatmap_profiles.csv",
        output_dir=tmp_path / "results",
        minimum_minutes=150.0,
        minimum_role_confidence=50.0,
        maximum_market_value=None,
        neutral_heatmap_score=70.0,
        top_n=5,
    )

    result = service.run_transfer_analysis(request)

    assert isinstance(result, TransferAnalysisResult)

    assert result.target == {
        "player_id": 10,
        "player_name": "Michael Olise",
        "position": "M",
        "rating": 8.4,
        "optional_metric": None,
        "pandas_missing": None,
        "missing_date": None,
    }

    assert tuple(mode.mode for mode in result.modes) == mode_names

    first_result = result.modes[0]

    assert first_result.mode == first_mode
    assert len(first_result.recommendations) == 1

    assert first_result.recommendations[0].data == {
        "player_id": 20,
        "player_name": "Dani Olmo",
        "recommendation_score": 91.2,
        "market_value_eur": 60_000_000,
        "missing_metric": None,
    }

    assert all(not mode.recommendations for mode in result.modes[1:])

    serialized = result.to_dict()

    json.dumps(
        serialized,
        allow_nan=False,
    )

    assert not request.output_dir.exists()

    captured = capsys.readouterr()

    assert captured.out == ""
    assert captured.err == ""
