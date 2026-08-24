"""Tests for the player-discovery application service."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from wc26.analytics.transfer_intelligence import (
    PlayerSearchRequest,
    search_players,
)
from wc26.analytics.transfer_intelligence.errors import (
    DatasetNotFoundError,
    InvalidDatasetError,
    InvalidPlayerSearchError,
)


def _player(
    *,
    player_id: int,
    player_name: str,
    national_team_name: str = "Test Nation",
    country_name: str = "Test Country",
    position: str = "M",
    final_role: str = "Test Role",
    archetype: str = "Test Archetype",
    spatial_role: str = "Test Spatial Role",
    age: float = 25.0,
    market_value: float = 10_000_000.0,
    market_value_currency: str = "EUR",
    minutes: float = 300.0,
    role_confidence_pct: float = 75.0,
    data_reliability_score: float = 70.0,
    player_quality_score: float = 60.0,
) -> dict[str, object]:
    return {
        "player_id": player_id,
        "player_name": player_name,
        "national_team_name": national_team_name,
        "country_name": country_name,
        "position": position,
        "final_role": final_role,
        "archetype": archetype,
        "spatial_role": spatial_role,
        "age": age,
        "market_value": market_value,
        "market_value_currency": market_value_currency,
        "minutes": minutes,
        "role_confidence_pct": role_confidence_pct,
        "data_reliability_score": data_reliability_score,
        "player_quality_score": player_quality_score,
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


def test_search_players_matches_case_and_diacritics(
    tmp_path: Path,
) -> None:
    features = _write_features(
        tmp_path,
        [
            _player(
                player_id=1,
                player_name="Luka Modrić",
            ),
            _player(
                player_id=2,
                player_name="Arda Güler",
            ),
            _player(
                player_id=3,
                player_name="Michael Olise",
            ),
        ],
    )

    modric_result = search_players(
        PlayerSearchRequest(
            query="MODRIC",
            features=features,
            limit=10,
        )
    )

    guler_result = search_players(
        PlayerSearchRequest(
            query="guler",
            features=features,
            limit=10,
        )
    )

    assert [player.player_name for player in modric_result.players] == ["Luka Modrić"]

    assert [player.player_name for player in guler_result.players] == ["Arda Güler"]


def test_search_players_preserves_name_relevance_order(
    tmp_path: Path,
) -> None:
    features = _write_features(
        tmp_path,
        [
            _player(
                player_id=1,
                player_name="John Alex Smith",
            ),
            _player(
                player_id=2,
                player_name="Alexis Mac Allister",
            ),
            _player(
                player_id=3,
                player_name="Alex",
            ),
            _player(
                player_id=4,
                player_name="Alexander Isak",
            ),
        ],
    )

    result = search_players(
        PlayerSearchRequest(
            query="alex",
            features=features,
            limit=10,
        )
    )

    assert [player.player_name for player in result.players] == [
        "Alex",
        "Alexander Isak",
        "Alexis Mac Allister",
        "John Alex Smith",
    ]

    assert result.sort_by == "relevance"
    assert result.sort_direction == "asc"


def test_search_players_filters_categories_with_and_or_semantics(
    tmp_path: Path,
) -> None:
    features = _write_features(
        tmp_path,
        [
            _player(
                player_id=1,
                player_name="Alpha Defender",
                country_name="France",
                position="D",
                archetype="Ball-Carrying Defender",
                final_role="Left Wide Centre-Back",
            ),
            _player(
                player_id=2,
                player_name="Beta Defender",
                country_name="Spain",
                position="D",
                archetype="Safe-Possession Defender",
                final_role="Safe Ball-Playing Centre-Back",
            ),
            _player(
                player_id=3,
                player_name="Gamma Forward",
                country_name="France",
                position="F",
                archetype="Poacher",
                final_role="Poacher",
            ),
        ],
    )

    result = search_players(
        PlayerSearchRequest(
            query=None,
            features=features,
            limit=10,
            positions=(
                "D",
                "F",
            ),
            countries=("France",),
            archetypes=(
                "Ball-Carrying Defender",
                "Safe-Possession Defender",
            ),
        )
    )

    assert [player.player_name for player in result.players] == ["Alpha Defender"]


def test_search_players_applies_inclusive_numeric_bounds(
    tmp_path: Path,
) -> None:
    features = _write_features(
        tmp_path,
        [
            _player(
                player_id=1,
                player_name="Boundary Player",
                age=24.0,
                market_value=30_000_000.0,
                minutes=300.0,
                role_confidence_pct=70.0,
                data_reliability_score=60.0,
            ),
            _player(
                player_id=2,
                player_name="Outside Player",
                age=25.0,
                market_value=31_000_000.0,
                minutes=299.0,
                role_confidence_pct=69.0,
                data_reliability_score=59.0,
            ),
        ],
    )

    result = search_players(
        PlayerSearchRequest(
            query=None,
            features=features,
            limit=10,
            minimum_age=24.0,
            maximum_age=24.0,
            minimum_market_value=30_000_000.0,
            maximum_market_value=30_000_000.0,
            minimum_minutes=300.0,
            minimum_role_confidence=70.0,
            minimum_data_reliability=60.0,
        )
    )

    assert [player.player_name for player in result.players] == ["Boundary Player"]


def test_search_players_filters_before_paginating_and_sorts_deterministically(
    tmp_path: Path,
) -> None:
    features = _write_features(
        tmp_path,
        [
            _player(
                player_id=1,
                player_name="Lowest Quality",
                position="D",
                player_quality_score=60.0,
                data_reliability_score=90.0,
                minutes=500.0,
            ),
            _player(
                player_id=2,
                player_name="Highest Quality",
                position="D",
                player_quality_score=90.0,
                data_reliability_score=70.0,
                minutes=300.0,
            ),
            _player(
                player_id=3,
                player_name="Middle Quality",
                position="D",
                player_quality_score=75.0,
                data_reliability_score=80.0,
                minutes=400.0,
            ),
            _player(
                player_id=4,
                player_name="Excluded Forward",
                position="F",
                player_quality_score=99.0,
            ),
        ],
    )

    result = search_players(
        PlayerSearchRequest(
            query=None,
            features=features,
            limit=1,
            offset=1,
            positions=("D",),
        )
    )

    assert result.total == 3
    assert result.count == 1
    assert result.offset == 1
    assert result.limit == 1
    assert result.has_more is True
    assert result.sort_by == "player_quality"
    assert result.sort_direction == "desc"

    assert [player.player_name for player in result.players] == ["Middle Quality"]


def test_search_players_applies_explicit_sorting(
    tmp_path: Path,
) -> None:
    features = _write_features(
        tmp_path,
        [
            _player(
                player_id=1,
                player_name="Older Player",
                position="D",
                age=31.0,
            ),
            _player(
                player_id=2,
                player_name="Younger Player",
                position="D",
                age=21.0,
            ),
        ],
    )

    result = search_players(
        PlayerSearchRequest(
            query=None,
            features=features,
            limit=10,
            positions=("D",),
            sort_by="age",
            sort_direction="asc",
        )
    )

    assert [player.player_name for player in result.players] == [
        "Younger Player",
        "Older Player",
    ]


def test_search_players_removes_duplicate_ids_before_pagination(
    tmp_path: Path,
) -> None:
    features = _write_features(
        tmp_path,
        [
            _player(
                player_id=1,
                player_name="Michael Olise",
            ),
            _player(
                player_id=1,
                player_name="Michael Olise",
            ),
            _player(
                player_id=2,
                player_name="Olivier Giroud",
            ),
        ],
    )

    result = search_players(
        PlayerSearchRequest(
            query="oli",
            features=features,
            limit=1,
        )
    )

    assert result.total == 2
    assert result.count == 1
    assert result.has_more is True


def test_search_players_returns_empty_paginated_result(
    tmp_path: Path,
) -> None:
    features = _write_features(
        tmp_path,
        [
            _player(
                player_id=1,
                player_name="Michael Olise",
            ),
        ],
    )

    result = search_players(
        PlayerSearchRequest(
            query="unknown",
            features=features,
            limit=10,
        )
    )

    assert result.to_dict() == {
        "query": "unknown",
        "count": 0,
        "total": 0,
        "offset": 0,
        "limit": 10,
        "has_more": False,
        "sort_by": "relevance",
        "sort_direction": "asc",
        "players": [],
    }


@pytest.mark.parametrize(
    "search_request",
    [
        PlayerSearchRequest(
            query="a",
            features=Path("unused.csv"),
            limit=10,
        ),
        PlayerSearchRequest(
            query="   ",
            features=Path("unused.csv"),
            limit=10,
        ),
        PlayerSearchRequest(
            query=None,
            features=Path("unused.csv"),
            limit=10,
        ),
        PlayerSearchRequest(
            query="olise",
            features=Path("unused.csv"),
            limit=0,
        ),
        PlayerSearchRequest(
            query="olise",
            features=Path("unused.csv"),
            limit=26,
        ),
        PlayerSearchRequest(
            query="olise",
            features=Path("unused.csv"),
            limit=10,
            offset=-1,
        ),
        PlayerSearchRequest(
            query=None,
            features=Path("unused.csv"),
            limit=10,
            positions=("D",),
            minimum_age=30.0,
            maximum_age=20.0,
        ),
        PlayerSearchRequest(
            query=None,
            features=Path("unused.csv"),
            limit=10,
            positions=("D",),
            minimum_market_value=50.0,
            maximum_market_value=10.0,
        ),
        PlayerSearchRequest(
            query=None,
            features=Path("unused.csv"),
            limit=10,
            positions=("D",),
            minimum_role_confidence=101.0,
        ),
        PlayerSearchRequest(
            query=None,
            features=Path("unused.csv"),
            limit=10,
            positions=("D",),
            sort_by="unsupported",
        ),
        PlayerSearchRequest(
            query=None,
            features=Path("unused.csv"),
            limit=10,
            positions=("D",),
            sort_by="relevance",
        ),
    ],
)
def test_search_players_rejects_invalid_parameters(
    search_request: PlayerSearchRequest,
) -> None:
    with pytest.raises(
        InvalidPlayerSearchError,
    ):
        search_players(
            search_request,
        )


def test_search_players_rejects_missing_feature_table(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        DatasetNotFoundError,
        match="Player feature table not found",
    ):
        search_players(
            PlayerSearchRequest(
                query="olise",
                features=tmp_path / "missing.csv",
                limit=10,
            )
        )


def test_search_players_rejects_invalid_feature_contract(
    tmp_path: Path,
) -> None:
    features = tmp_path / "features.csv"

    pd.DataFrame(
        {
            "player_id": [1],
            "player_name": ["Michael Olise"],
        }
    ).to_csv(
        features,
        index=False,
    )

    with pytest.raises(
        InvalidDatasetError,
        match="Missing player search columns",
    ):
        search_players(
            PlayerSearchRequest(
                query="olise",
                features=features,
                limit=10,
            )
        )
