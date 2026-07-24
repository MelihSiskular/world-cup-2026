"""Tests for the player-search application service."""

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
    position: str = "M",
    final_role: str = "Test Role",
    archetype: str = "Test Archetype",
    age: float = 25.0,
    market_value: float = 10_000_000.0,
    market_value_currency: str = "EUR",
) -> dict[str, object]:
    return {
        "player_id": player_id,
        "player_name": player_name,
        "national_team_name": national_team_name,
        "position": position,
        "final_role": final_role,
        "archetype": archetype,
        "age": age,
        "market_value": market_value,
        "market_value_currency": market_value_currency,
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


def test_search_players_ranks_exact_match_first(
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

    assert result.players[0].player_name == "Alex"

    assert [player.player_name for player in result.players] == [
        "Alex",
        "Alexander Isak",
        "Alexis Mac Allister",
        "John Alex Smith",
    ]


def test_search_players_applies_limit_and_removes_duplicate_ids(
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
            _player(
                player_id=3,
                player_name="Oliver Burke",
            ),
        ],
    )

    result = search_players(
        PlayerSearchRequest(
            query="oli",
            features=features,
            limit=2,
        )
    )

    assert result.count == 2

    assert len({player.player_id for player in result.players}) == 2


def test_search_players_returns_empty_result(
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

    assert result.query == "unknown"
    assert result.count == 0
    assert result.players == ()
    assert result.to_dict() == {
        "query": "unknown",
        "count": 0,
        "players": [],
    }


@pytest.mark.parametrize(
    ("query", "limit"),
    [
        ("a", 10),
        ("   ", 10),
        ("olise", 0),
        ("olise", 26),
    ],
)
def test_search_players_rejects_invalid_parameters(
    tmp_path: Path,
    query: str,
    limit: int,
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

    with pytest.raises(
        InvalidPlayerSearchError,
    ):
        search_players(
            PlayerSearchRequest(
                query=query,
                features=features,
                limit=limit,
            )
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
