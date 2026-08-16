"""Tests for radar-comparison API response contracts."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from wc26.api.schemas.transfer_intelligence import (
    RadarComparisonMetadataResponse,
    RadarComparisonResponse,
    RadarDimensionResponse,
)


def _dimension(
    key: str,
    percentile: float,
) -> dict[str, object]:
    return {
        "key": key,
        "label": key.replace("_", " ").title(),
        "raw_score": 1.0,
        "percentile": percentile,
        "peer_count": 216,
    }


def _player(
    *,
    player_id: int,
    player_name: str,
    position: str,
) -> dict[str, object]:
    return {
        "player_id": player_id,
        "player_name": player_name,
        "position": position,
        "available": True,
        "peer_count": 216,
        "dimensions": [
            _dimension(
                "creativity",
                90.0,
            ),
            _dimension(
                "progression",
                80.0,
            ),
            _dimension(
                "dribbling",
                70.0,
            ),
        ],
    }


def test_radar_comparison_schema_accepts_valid_overlay() -> None:
    response = RadarComparisonResponse.model_validate(
        {
            "target": _player(
                player_id=978838,
                player_name="Michael Olise",
                position="M",
            ),
            "candidate": _player(
                player_id=789071,
                player_name="Dani Olmo",
                position="M",
            ),
            "comparison": {
                "same_position": True,
                "overlay_available": True,
                "reason": None,
            },
        }
    )

    assert response.target.available is True
    assert response.candidate.available is True

    assert (
        response.comparison.overlay_available
        is True
    )

    assert (
        response.comparison.reason
        is None
    )


def test_radar_dimension_rejects_out_of_range_percentile() -> None:
    with pytest.raises(
        ValidationError
    ):
        RadarDimensionResponse.model_validate(
            {
                "key": "creativity",
                "label": "Creativity",
                "raw_score": 1.0,
                "percentile": 101.0,
                "peer_count": 216,
            }
        )


def test_radar_dimension_rejects_percentile_without_raw_score() -> None:
    with pytest.raises(
        ValidationError,
        match="requires a raw score",
    ):
        RadarDimensionResponse.model_validate(
            {
                "key": "creativity",
                "label": "Creativity",
                "raw_score": None,
                "percentile": 90.0,
                "peer_count": 216,
            }
        )


def test_radar_metadata_rejects_overlay_for_different_position() -> None:
    with pytest.raises(
        ValidationError,
        match="same position",
    ):
        RadarComparisonMetadataResponse.model_validate(
            {
                "same_position": False,
                "overlay_available": True,
                "reason": None,
            }
        )


def test_radar_metadata_requires_reason_when_overlay_unavailable() -> None:
    with pytest.raises(
        ValidationError,
        match="requires a reason",
    ):
        RadarComparisonMetadataResponse.model_validate(
            {
                "same_position": False,
                "overlay_available": False,
                "reason": None,
            }
        )


def test_radar_comparison_rejects_overlay_with_mismatched_axes() -> None:
    candidate = _player(
        player_id=789071,
        player_name="Dani Olmo",
        position="M",
    )

    candidate["dimensions"] = [
        _dimension(
            "creativity",
            90.0,
        ),
        _dimension(
            "passing_volume",
            80.0,
        ),
        _dimension(
            "dribbling",
            70.0,
        ),
    ]

    with pytest.raises(
        ValidationError,
        match="matching ordered dimensions",
    ):
        RadarComparisonResponse.model_validate(
            {
                "target": _player(
                    player_id=978838,
                    player_name="Michael Olise",
                    position="M",
                ),
                "candidate": candidate,
                "comparison": {
                    "same_position": True,
                    "overlay_available": True,
                    "reason": None,
                },
            }
        )


def test_unavailable_profile_may_keep_partial_evidence() -> None:
    response = RadarComparisonResponse.model_validate(
        {
            "target": {
                "player_id": 10,
                "player_name": "Partial Player",
                "position": "M",
                "available": False,
                "peer_count": 216,
                "dimensions": [
                    {
                        "key": "creativity",
                        "label": "Creativity",
                        "raw_score": 1.0,
                        "percentile": 60.0,
                        "peer_count": 216,
                    },
                    {
                        "key": "progression",
                        "label": "Progression",
                        "raw_score": None,
                        "percentile": None,
                        "peer_count": 215,
                    },
                ],
            },
            "candidate": _player(
                player_id=20,
                player_name="Candidate Player",
                position="M",
            ),
            "comparison": {
                "same_position": True,
                "overlay_available": False,
                "reason": "target_profile_unavailable",
            },
        }
    )

    assert response.target.available is False
    assert len(response.target.dimensions) == 2
