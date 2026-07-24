"""Tests for structured transfer analysis service results."""

from __future__ import annotations

import json
from dataclasses import dataclass
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


@dataclass(slots=True)
class _ServiceDoubles:
    """Controllable dependencies used by the service-result test."""

    players: pd.DataFrame
    target: pd.Series
    base_candidates: pd.DataFrame
    first_mode: str

    def read_csv(
        self,
        *args: object,
        **kwargs: object,
    ) -> pd.DataFrame:
        """Return a fresh copy of the player feature table."""

        del args, kwargs

        return self.players.copy()

    @staticmethod
    def load_empty_dataset(
        path: object,
    ) -> pd.DataFrame:
        """Return an empty supporting dataset."""

        del path

        return pd.DataFrame()

    def resolve_transfer_target(
        self,
        players: pd.DataFrame,
        *,
        player: str | None,
        player_id: int | None,
    ) -> pd.Series:
        """Return the prepared target and validate name compatibility."""

        assert list(players.columns) == [
            "player_id",
            "player_name",
        ]
        assert player == "Michael Olise"
        assert player_id is None

        return self.target

    def prepare_candidate_base(
        self,
        *args: object,
        **kwargs: object,
    ) -> tuple[
        pd.DataFrame,
        dict[str, float],
    ]:
        """Return the prepared candidate pool and heatmap profile."""

        del args, kwargs

        return (
            self.base_candidates,
            {
                "left": 0.4,
                "centre": 0.6,
            },
        )

    def generate_mode_results(
        self,
        candidates: pd.DataFrame,
        mode: str,
        target_heatmap_profile: object,
    ) -> pd.DataFrame:
        """Return one recommendation for the first configured mode."""

        assert candidates is self.base_candidates
        assert target_heatmap_profile == {
            "left": 0.4,
            "centre": 0.6,
        }

        if mode != self.first_mode:
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


def _install_service_doubles(
    monkeypatch: MonkeyPatch,
    doubles: _ServiceDoubles,
) -> None:
    """Replace external service dependencies with deterministic doubles."""

    monkeypatch.setattr(
        service.pd,
        "read_csv",
        doubles.read_csv,
    )
    monkeypatch.setattr(
        service,
        "load_similarity",
        doubles.load_empty_dataset,
    )
    monkeypatch.setattr(
        service,
        "load_heatmap_similarity",
        doubles.load_empty_dataset,
    )
    monkeypatch.setattr(
        service,
        "load_heatmap_profiles",
        doubles.load_empty_dataset,
    )
    monkeypatch.setattr(
        service,
        "resolve_transfer_target",
        doubles.resolve_transfer_target,
    )
    monkeypatch.setattr(
        service,
        "prepare_candidate_base",
        doubles.prepare_candidate_base,
    )
    monkeypatch.setattr(
        service,
        "generate_mode_results",
        doubles.generate_mode_results,
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

    doubles = _ServiceDoubles(
        players=players,
        target=target,
        base_candidates=base_candidates,
        first_mode=mode_names[0],
    )

    _install_service_doubles(
        monkeypatch,
        doubles,
    )

    request = TransferAnalysisRequest(
        player="Michael Olise",
        features=tmp_path / "features.csv",
        similarity=tmp_path / "similarity.csv",
        heatmap_similarity=(tmp_path / "heatmap_similarity.csv"),
        heatmap_profiles=(tmp_path / "heatmap_profiles.csv"),
        minimum_minutes=150.0,
        minimum_role_confidence=50.0,
        maximum_market_value=None,
        neutral_heatmap_score=70.0,
    )

    result = service.run_transfer_analysis(request)

    assert isinstance(
        result,
        TransferAnalysisResult,
    )

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

    assert first_result.mode == mode_names[0]
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

    captured = capsys.readouterr()

    assert captured.out == ""
    assert captured.err == ""
