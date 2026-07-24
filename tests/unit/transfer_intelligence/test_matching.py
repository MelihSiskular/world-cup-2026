from __future__ import annotations

import pandas as pd
import pytest

from wc26.analytics.transfer_intelligence.errors import (
    AmbiguousPlayerError,
    InvalidDatasetError,
    InvalidTransferAnalysisRequestError,
    PlayerNotFoundError,
)
from wc26.analytics.transfer_intelligence.matching import (
    resolve_player,
    resolve_player_by_id,
    resolve_transfer_target,
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
        PlayerNotFoundError,
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
        AmbiguousPlayerError,
        match="Multiple players matched",
    ):
        resolve_player(
            players,
            "Alex",
        )


def test_resolve_player_by_id_returns_exact_player() -> None:
    players = pd.DataFrame(
        [
            {
                "player_id": 978838,
                "player_name": "Michael Olise",
            },
            {
                "player_id": 12994,
                "player_name": "Lionel Messi",
            },
        ]
    )

    result = resolve_player_by_id(
        players,
        978838,
    )

    assert result["player_id"] == 978838
    assert result["player_name"] == "Michael Olise"


def test_resolve_player_by_id_accepts_numeric_string_values() -> None:
    players = pd.DataFrame(
        [
            {
                "player_id": "978838",
                "player_name": "Michael Olise",
            },
        ]
    )

    result = resolve_player_by_id(
        players,
        978838,
    )

    assert result["player_name"] == "Michael Olise"


def test_resolve_player_by_id_rejects_unknown_id() -> None:
    players = pd.DataFrame(
        [
            {
                "player_id": 978838,
                "player_name": "Michael Olise",
            },
        ]
    )

    with pytest.raises(
        PlayerNotFoundError,
        match="Player not found for ID: 999999",
    ):
        resolve_player_by_id(
            players,
            999999,
        )


def test_resolve_player_by_id_rejects_duplicate_id() -> None:
    players = pd.DataFrame(
        [
            {
                "player_id": 978838,
                "player_name": "Michael Olise",
            },
            {
                "player_id": 978838,
                "player_name": "Conflicting Player",
            },
        ]
    )

    with pytest.raises(
        InvalidDatasetError,
        match="Multiple players matched player ID",
    ):
        resolve_player_by_id(
            players,
            978838,
        )


def test_resolve_transfer_target_preserves_name_lookup() -> None:
    players = pd.DataFrame(
        [
            {
                "player_id": 978838,
                "player_name": "Michael Olise",
            },
        ]
    )

    result = resolve_transfer_target(
        players,
        player="Michael Olise",
        player_id=None,
    )

    assert result["player_id"] == 978838
    assert result["player_name"] == "Michael Olise"


def test_resolve_transfer_target_supports_player_id() -> None:
    players = pd.DataFrame(
        [
            {
                "player_id": 978838,
                "player_name": "Michael Olise",
            },
        ]
    )

    result = resolve_transfer_target(
        players,
        player=None,
        player_id=978838,
    )

    assert result["player_name"] == "Michael Olise"


@pytest.mark.parametrize(
    ("player", "player_id"),
    [
        (None, None),
        ("", None),
        ("   ", None),
        ("Michael Olise", 978838),
    ],
)
def test_resolve_transfer_target_requires_one_identifier(
    player: str | None,
    player_id: int | None,
) -> None:
    players = pd.DataFrame(
        [
            {
                "player_id": 978838,
                "player_name": "Michael Olise",
            },
        ]
    )

    with pytest.raises(
        InvalidTransferAnalysisRequestError,
        match="exactly one",
    ):
        resolve_transfer_target(
            players,
            player=player,
            player_id=player_id,
        )


@pytest.mark.parametrize(
    "player_id",
    [
        0,
        -1,
        -100,
    ],
)
def test_resolve_transfer_target_rejects_non_positive_id(
    player_id: int,
) -> None:
    players = pd.DataFrame(
        [
            {
                "player_id": 978838,
                "player_name": "Michael Olise",
            },
        ]
    )

    with pytest.raises(
        InvalidTransferAnalysisRequestError,
        match="positive integer",
    ):
        resolve_transfer_target(
            players,
            player=None,
            player_id=player_id,
        )
