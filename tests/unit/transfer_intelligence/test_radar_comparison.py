from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import numpy as np
import pandas as pd
import pytest

from wc26.analytics.transfer_intelligence.catalog import (
    TransferDataCatalog,
)
from wc26.analytics.transfer_intelligence.errors import (
    InvalidTransferAnalysisRequestError,
    PlayerNotFoundError,
)
from wc26.analytics.transfer_intelligence.models import (
    RadarComparisonRequest,
)
from wc26.analytics.transfer_intelligence.radar_comparison import (
    get_radar_comparison_from_catalog,
)

MIDFIELDER_DIMENSIONS = (
    "creativity",
    "progression",
    "passing_volume",
    "ball_security",
    "dribbling",
    "scoring_threat",
    "defensive_work",
    "wide_creation",
)

FORWARD_DIMENSIONS = (
    "finishing",
    "shooting_volume",
    "creativity",
    "dribbling",
    "link_play",
    "aerial_presence",
    "off_ball_threat",
    "ball_security",
)


def _midfielder(
    player_id: int,
    player_name: str,
    score: float,
) -> dict[str, object]:
    return {
        "player_id": player_id,
        "player_name": player_name,
        "position": "M",
        **{f"archetype_score_{dimension}": score for dimension in MIDFIELDER_DIMENSIONS},
    }


def _forward(
    player_id: int,
    player_name: str,
    score: float,
) -> dict[str, object]:
    return {
        "player_id": player_id,
        "player_name": player_name,
        "position": "F",
        **{f"archetype_score_{dimension}": score for dimension in FORWARD_DIMENSIONS},
    }


def _catalog(
    players: pd.DataFrame,
) -> TransferDataCatalog:
    return TransferDataCatalog(
        players=players,
        similarity=pd.DataFrame(),
        heatmap_similarity=pd.DataFrame(),
        heatmap_profiles=pd.DataFrame(),
    )


def _midfielder_catalog() -> TransferDataCatalog:
    players = pd.DataFrame(
        [
            _midfielder(
                10,
                "Target Player",
                3.0,
            ),
            _midfielder(
                20,
                "Candidate Player",
                4.0,
            ),
            _midfielder(
                30,
                "Peer One",
                1.0,
            ),
            _midfielder(
                40,
                "Peer Two",
                2.0,
            ),
        ]
    )

    return _catalog(players)


def test_radar_comparison_request_is_immutable() -> None:
    request = RadarComparisonRequest(
        target_player_id=10,
        candidate_player_id=20,
    )

    with pytest.raises(FrozenInstanceError):
        request.target_player_id = 1


def test_same_position_radar_builds_ordered_percentile_profiles() -> None:
    result = get_radar_comparison_from_catalog(
        RadarComparisonRequest(
            target_player_id=10,
            candidate_player_id=20,
        ),
        _midfielder_catalog(),
    )

    assert result.target.player_name == "Target Player"
    assert result.target.position == "M"
    assert result.target.available is True
    assert result.target.peer_count == 4

    assert tuple(dimension.key for dimension in result.target.dimensions) == MIDFIELDER_DIMENSIONS

    assert all(dimension.raw_score == 3.0 for dimension in result.target.dimensions)

    assert all(dimension.percentile == 75.0 for dimension in result.target.dimensions)

    assert all(dimension.peer_count == 4 for dimension in result.target.dimensions)

    assert result.candidate.available is True

    assert all(dimension.percentile == 100.0 for dimension in result.candidate.dimensions)

    assert result.comparison.same_position is True
    assert result.comparison.overlay_available is True
    assert result.comparison.reason is None


def test_radar_comparison_preserves_directional_archetype_scores() -> None:
    result = get_radar_comparison_from_catalog(
        RadarComparisonRequest(
            target_player_id=10,
            candidate_player_id=20,
        ),
        _midfielder_catalog(),
    )

    target_security = next(
        dimension for dimension in result.target.dimensions if dimension.key == "ball_security"
    )

    candidate_security = next(
        dimension for dimension in result.candidate.dimensions if dimension.key == "ball_security"
    )

    assert target_security.raw_score == 3.0
    assert target_security.percentile == 75.0

    assert candidate_security.raw_score == 4.0
    assert candidate_security.percentile == 100.0


def test_radar_comparison_keeps_missing_dimension_explicit() -> None:
    catalog = _midfielder_catalog()

    players = catalog.players.copy()

    players.loc[
        players["player_id"].eq(10),
        "archetype_score_passing_volume",
    ] = np.nan

    result = get_radar_comparison_from_catalog(
        RadarComparisonRequest(
            target_player_id=10,
            candidate_player_id=20,
        ),
        _catalog(players),
    )

    passing = next(
        dimension for dimension in result.target.dimensions if dimension.key == "passing_volume"
    )

    assert result.target.available is True

    assert passing.raw_score is None
    assert passing.percentile is None
    assert passing.peer_count == 3


def test_cross_position_comparison_uses_separate_profiles() -> None:
    players = pd.DataFrame(
        [
            _midfielder(
                10,
                "Target Midfielder",
                2.0,
            ),
            _midfielder(
                30,
                "Midfielder Peer",
                1.0,
            ),
            _forward(
                20,
                "Candidate Forward",
                2.0,
            ),
            _forward(
                40,
                "Forward Peer",
                1.0,
            ),
        ]
    )

    result = get_radar_comparison_from_catalog(
        RadarComparisonRequest(
            target_player_id=10,
            candidate_player_id=20,
        ),
        _catalog(players),
    )

    assert result.target.position == "M"
    assert result.candidate.position == "F"

    assert tuple(dimension.key for dimension in result.target.dimensions) == MIDFIELDER_DIMENSIONS

    assert tuple(dimension.key for dimension in result.candidate.dimensions) == FORWARD_DIMENSIONS

    assert result.target.available is True
    assert result.candidate.available is True

    assert result.comparison.same_position is False
    assert result.comparison.overlay_available is False
    assert result.comparison.reason == "different_position_profiles"


def test_unsupported_position_keeps_profile_unavailable() -> None:
    unsupported = {
        "player_id": 10,
        "player_name": "Unsupported Player",
        "position": "X",
    }

    players = pd.DataFrame(
        [
            unsupported,
            _midfielder(
                20,
                "Candidate Player",
                2.0,
            ),
        ]
    )

    result = get_radar_comparison_from_catalog(
        RadarComparisonRequest(
            target_player_id=10,
            candidate_player_id=20,
        ),
        _catalog(players),
    )

    assert result.target.position == "X"
    assert result.target.available is False
    assert result.target.peer_count == 0
    assert result.target.dimensions == ()

    assert result.comparison.overlay_available is False
    assert result.comparison.reason == "target_profile_unavailable"


def test_radar_comparison_serializes_without_nan() -> None:
    result = get_radar_comparison_from_catalog(
        RadarComparisonRequest(
            target_player_id=10,
            candidate_player_id=20,
        ),
        _midfielder_catalog(),
    )

    payload = result.to_dict()

    assert payload["target"]["available"] is True
    assert payload["comparison"]["overlay_available"] is True

    json.dumps(
        payload,
        allow_nan=False,
    )


def test_radar_comparison_rejects_same_player() -> None:
    with pytest.raises(
        InvalidTransferAnalysisRequestError,
        match="two different players",
    ):
        get_radar_comparison_from_catalog(
            RadarComparisonRequest(
                target_player_id=10,
                candidate_player_id=10,
            ),
            _midfielder_catalog(),
        )


def test_radar_comparison_rejects_non_positive_player_id() -> None:
    with pytest.raises(
        InvalidTransferAnalysisRequestError,
        match="positive integers",
    ):
        get_radar_comparison_from_catalog(
            RadarComparisonRequest(
                target_player_id=0,
                candidate_player_id=20,
            ),
            _midfielder_catalog(),
        )


def test_radar_comparison_preserves_player_not_found_error() -> None:
    with pytest.raises(
        PlayerNotFoundError,
        match="999",
    ):
        get_radar_comparison_from_catalog(
            RadarComparisonRequest(
                target_player_id=10,
                candidate_player_id=999,
            ),
            _midfielder_catalog(),
        )
