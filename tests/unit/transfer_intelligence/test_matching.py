from __future__ import annotations

import pandas as pd
import pytest

from wc26.analytics.transfer_intelligence.matching import (
    resolve_player,
)


@pytest.fixture
def players() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "player_id": 1,
                "player_name": "Michael Olise",
            },
            {
                "player_id": 2,
                "player_name": "Florian Wirtz",
            },
            {
                "player_id": 3,
                "player_name": "Alex Smith",
            },
            {
                "player_id": 4,
                "player_name": "Alex Jones",
            },
        ]
    )


def test_resolve_player_matches_exact_name(
    players: pd.DataFrame,
) -> None:
    result = resolve_player(
        players,
        "MICHAEL OLISE",
    )

    assert result["player_id"] == 1
    assert result["player_name"] == "Michael Olise"


def test_resolve_player_matches_unique_partial_name(
    players: pd.DataFrame,
) -> None:
    result = resolve_player(
        players,
        "Wirtz",
    )

    assert result["player_id"] == 2


def test_resolve_player_rejects_unknown_name(
    players: pd.DataFrame,
) -> None:
    with pytest.raises(
        ValueError,
        match="Player not found",
    ):
        resolve_player(
            players,
            "Unknown Player",
        )


def test_resolve_player_rejects_ambiguous_name(
    players: pd.DataFrame,
) -> None:
    with pytest.raises(
        ValueError,
        match="Multiple players matched",
    ):
        resolve_player(
            players,
            "Alex",
        )
