"""
Tests for the player-profile application service.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from wc26.analytics.transfer_intelligence import (
    PlayerProfileRequest,
    get_player_profile,
)
from wc26.analytics.transfer_intelligence.errors import (
    DatasetNotFoundError,
    InvalidDatasetError,
    InvalidPlayerProfileError,
    PlayerNotFoundError,
)
from wc26.analytics.transfer_intelligence.player_profile import (
    PLAYER_PROFILE_COLUMNS,
)


def _profile_row(
    *,
    player_id: object = 978838,
    player_name: object = "Michael Olise",
) -> dict[str, object]:
    return {
        "player_id": player_id,
        "player_name": player_name,
        "national_team_name": "France",
        "country_name": "France",
        "position": "M",
        "age": 24.6,
        "height_cm": 184.0,
        "appearances": 6,
        "starts": 6,
        "minutes": 488.0,
        "weighted_rating": 7.570697,
        "market_value": 144_000_000.0,
        "market_value_currency": "EUR",
        "archetype": "Wide Creator",
        "spatial_role": "Advanced Central Zone",
        "final_role": "Advanced Central Playmaker",
        "lateral_profile": "Central Lane",
        "vertical_profile": "Advanced Middle Third",
        "mobility_profile": "Positionally Stable",
        "role_confidence_pct": 87.19,
        "spatial_reliability": 1.0,
        "data_reliability_score": 74.52,
        "player_quality_score": 88.85,
        "role_reason": "Statistical and spatial profile.",
    }


def _write_features(
    tmp_path: Path,
    rows: list[dict[str, object]],
) -> Path:
    path = tmp_path / "features.csv"

    pd.DataFrame(rows).to_csv(
        path,
        index=False,
    )

    return path


def test_get_player_profile_returns_structured_result(
    tmp_path: Path,
) -> None:
    features = _write_features(
        tmp_path,
        [
            _profile_row(),
            _profile_row(
                player_id=12994,
                player_name="Lionel Messi",
            ),
        ],
    )

    result = get_player_profile(
        PlayerProfileRequest(
            player_id=978838,
            features=features,
        )
    )

    assert result.player_id == 978838
    assert result.player_name == "Michael Olise"
    assert result.national_team_name == "France"
    assert result.position == "M"
    assert result.height_cm == 184.0
    assert result.appearances == 6
    assert result.market_value == 144_000_000.0
    assert result.market_value_currency == "EUR"
    assert result.final_role == "Advanced Central Playmaker"
    assert result.role_confidence_pct == 87.19

    assert result.to_dict()["player_name"] == "Michael Olise"


def test_get_player_profile_preserves_optional_missing_values(
    tmp_path: Path,
) -> None:
    row = _profile_row()
    row["height_cm"] = None
    row["market_value"] = None
    row["archetype"] = None

    features = _write_features(
        tmp_path,
        [row],
    )

    result = get_player_profile(
        PlayerProfileRequest(
            player_id=978838,
            features=features,
        )
    )

    assert result.height_cm is None
    assert result.market_value is None
    assert result.archetype is None

    assert result.to_dict()["height_cm"] is None


@pytest.mark.parametrize(
    "player_id",
    [
        0,
        -1,
        -100,
    ],
)
def test_get_player_profile_rejects_invalid_request_id(
    tmp_path: Path,
    player_id: int,
) -> None:
    features = _write_features(
        tmp_path,
        [_profile_row()],
    )

    with pytest.raises(
        InvalidPlayerProfileError,
        match="positive integer",
    ):
        get_player_profile(
            PlayerProfileRequest(
                player_id=player_id,
                features=features,
            )
        )


def test_get_player_profile_rejects_unknown_player(
    tmp_path: Path,
) -> None:
    features = _write_features(
        tmp_path,
        [_profile_row()],
    )

    with pytest.raises(
        PlayerNotFoundError,
        match="Player not found for ID",
    ):
        get_player_profile(
            PlayerProfileRequest(
                player_id=999999,
                features=features,
            )
        )


def test_get_player_profile_rejects_missing_dataset(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        DatasetNotFoundError,
        match="Player feature table not found",
    ):
        get_player_profile(
            PlayerProfileRequest(
                player_id=978838,
                features=tmp_path / "missing.csv",
            )
        )


def test_get_player_profile_rejects_missing_columns(
    tmp_path: Path,
) -> None:
    features = tmp_path / "features.csv"

    pd.DataFrame(
        {
            "player_id": [978838],
            "player_name": ["Michael Olise"],
        }
    ).to_csv(
        features,
        index=False,
    )

    with pytest.raises(
        InvalidDatasetError,
        match="Missing player profile columns",
    ):
        get_player_profile(
            PlayerProfileRequest(
                player_id=978838,
                features=features,
            )
        )


def test_get_player_profile_rejects_duplicate_player_ids(
    tmp_path: Path,
) -> None:
    features = _write_features(
        tmp_path,
        [
            _profile_row(),
            _profile_row(
                player_name="Conflicting Player",
            ),
        ],
    )

    with pytest.raises(
        InvalidDatasetError,
        match="duplicate player IDs",
    ):
        get_player_profile(
            PlayerProfileRequest(
                player_id=978838,
                features=features,
            )
        )


@pytest.mark.parametrize(
    "invalid_player_id",
    [
        None,
        "not-an-id",
        10.5,
        float("inf"),
    ],
)
def test_get_player_profile_rejects_invalid_dataset_ids(
    tmp_path: Path,
    invalid_player_id: object,
) -> None:
    features = _write_features(
        tmp_path,
        [
            _profile_row(
                player_id=invalid_player_id,
            )
        ],
    )

    with pytest.raises(
        InvalidDatasetError,
        match="invalid player_id",
    ):
        get_player_profile(
            PlayerProfileRequest(
                player_id=978838,
                features=features,
            )
        )


def test_player_profile_columns_match_test_fixture() -> None:
    assert set(_profile_row()) == set(PLAYER_PROFILE_COLUMNS)
