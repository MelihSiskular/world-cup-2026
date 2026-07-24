"""Tests for structured transfer analysis service results."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from pytest import CaptureFixture, MonkeyPatch

from wc26.analytics.transfer_intelligence import service
from wc26.analytics.transfer_intelligence.catalog import (
    TransferDataCatalog,
)
from wc26.analytics.transfer_intelligence.config import (
    MODE_CONFIG,
)
from wc26.analytics.transfer_intelligence.models import (
    TransferAnalysisRequest,
    TransferAnalysisResult,
)


@dataclass(slots=True)
class _ServiceDoubles:
    """Controllable dependencies used by service-result tests."""

    target: pd.Series
    base_candidates: pd.DataFrame
    similarity: pd.DataFrame
    heatmap_similarity: pd.DataFrame
    heatmap_profiles: pd.DataFrame
    first_mode: str

    def resolve_transfer_target(
        self,
        players: pd.DataFrame,
        *,
        player: str | None,
        player_id: int | None,
    ) -> pd.Series:
        """Return the prepared target."""

        assert list(players.columns) == [
            "player_id",
            "player_name",
        ]
        assert players["player_id"].tolist() == [10]

        assert player == "Michael Olise"
        assert player_id is None

        return self.target

    def prepare_candidate_base(
        self,
        *,
        players: pd.DataFrame,
        similarity: pd.DataFrame,
        heatmap_similarity: pd.DataFrame,
        heatmap_profiles: pd.DataFrame,
        target: pd.Series,
        minimum_minutes: float,
        minimum_role_confidence: float,
        maximum_market_value: float | None,
        neutral_heatmap_score: float,
    ) -> tuple[
        pd.DataFrame,
        dict[str, float],
    ]:
        """Return a prepared candidate pool."""

        assert players["player_id"].tolist() == [10]

        assert similarity is self.similarity
        assert heatmap_similarity is self.heatmap_similarity
        assert heatmap_profiles is self.heatmap_profiles
        assert target is self.target

        assert minimum_minutes == 150.0
        assert minimum_role_confidence == 50.0
        assert maximum_market_value is None
        assert neutral_heatmap_score == 70.0

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
        """Return one recommendation for the first mode."""

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


def _install_analysis_doubles(
    monkeypatch: MonkeyPatch,
    doubles: _ServiceDoubles,
) -> None:
    """Replace analytical dependencies with test doubles."""

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


def _analysis_request(
    tmp_path: Path,
) -> TransferAnalysisRequest:
    """Build a standard analysis request."""

    return TransferAnalysisRequest(
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


def test_run_transfer_analysis_from_catalog_returns_structured_result(
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
    similarity = pd.DataFrame(
        {
            "source_player_id": [10],
        }
    )
    heatmap_similarity = pd.DataFrame(
        {
            "target_player_id": [10],
        }
    )
    heatmap_profiles = pd.DataFrame(
        {
            "player_id": [10],
        }
    )

    original_players = players.copy(deep=True)
    original_similarity = similarity.copy(deep=True)
    original_heatmap_similarity = heatmap_similarity.copy(deep=True)
    original_heatmap_profiles = heatmap_profiles.copy(deep=True)

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

    catalog = TransferDataCatalog(
        players=players,
        similarity=similarity,
        heatmap_similarity=heatmap_similarity,
        heatmap_profiles=heatmap_profiles,
    )

    mode_names = tuple(MODE_CONFIG)

    doubles = _ServiceDoubles(
        target=target,
        base_candidates=base_candidates,
        similarity=similarity,
        heatmap_similarity=heatmap_similarity,
        heatmap_profiles=heatmap_profiles,
        first_mode=mode_names[0],
    )

    _install_analysis_doubles(
        monkeypatch,
        doubles,
    )

    result = service.run_transfer_analysis_from_catalog(
        _analysis_request(tmp_path),
        catalog,
    )

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

    pd.testing.assert_frame_equal(
        players,
        original_players,
    )
    pd.testing.assert_frame_equal(
        similarity,
        original_similarity,
    )
    pd.testing.assert_frame_equal(
        heatmap_similarity,
        original_heatmap_similarity,
    )
    pd.testing.assert_frame_equal(
        heatmap_profiles,
        original_heatmap_profiles,
    )

    captured = capsys.readouterr()

    assert captured.out == ""
    assert captured.err == ""


def test_run_transfer_analysis_loads_catalog_and_delegates(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    request = _analysis_request(tmp_path)

    catalog = TransferDataCatalog(
        players=pd.DataFrame(),
        similarity=pd.DataFrame(),
        heatmap_similarity=pd.DataFrame(),
        heatmap_profiles=pd.DataFrame(),
    )

    expected = TransferAnalysisResult(
        target={
            "player_id": 10,
            "player_name": "Michael Olise",
        },
        modes=(),
    )

    loader_calls: list[
        tuple[
            Path,
            Path,
            Path,
            Path,
        ]
    ] = []
    analysis_calls: list[
        tuple[
            TransferAnalysisRequest,
            TransferDataCatalog,
        ]
    ] = []

    def fake_load_transfer_data_catalog(
        *,
        features: Path,
        similarity: Path,
        heatmap_similarity: Path,
        heatmap_profiles: Path,
    ) -> TransferDataCatalog:
        loader_calls.append(
            (
                features,
                similarity,
                heatmap_similarity,
                heatmap_profiles,
            )
        )

        return catalog

    def fake_run_transfer_analysis_from_catalog(
        delegated_request: TransferAnalysisRequest,
        delegated_catalog: TransferDataCatalog,
    ) -> TransferAnalysisResult:
        analysis_calls.append(
            (
                delegated_request,
                delegated_catalog,
            )
        )

        return expected

    monkeypatch.setattr(
        service,
        "load_transfer_data_catalog",
        fake_load_transfer_data_catalog,
    )
    monkeypatch.setattr(
        service,
        "run_transfer_analysis_from_catalog",
        fake_run_transfer_analysis_from_catalog,
    )

    result = service.run_transfer_analysis(request)

    assert result is expected

    assert loader_calls == [
        (
            request.features,
            request.similarity,
            request.heatmap_similarity,
            request.heatmap_profiles,
        )
    ]

    assert analysis_calls == [
        (
            request,
            catalog,
        )
    ]
