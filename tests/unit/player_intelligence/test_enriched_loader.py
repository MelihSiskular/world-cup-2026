"""Tests for enriched tournament-summary loading."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from wc26.analytics.transfer_intelligence.datasets import (
    load_player_tournament_summary,
)
from wc26.analytics.transfer_intelligence.errors import (
    InvalidDatasetError,
)


def write_dataset(
    path: Path,
    *,
    player_ids: list[int],
) -> None:
    pd.DataFrame(
        {
            "player_id": player_ids,
            "player_primary_position": ["M" for _ in player_ids],
            "matches_played": [5 for _ in player_ids],
            "starts": [4 for _ in player_ids],
            "substitute_appearances": [1 for _ in player_ids],
            "captain_appearances": [0 for _ in player_ids],
            "total_minutes": [360 for _ in player_ids],
            "formations_used": [1 for _ in player_ids],
            "primary_formation": ["4-2-3-1" for _ in player_ids],
            "primary_lineup_position": ["M" for _ in player_ids],
        }
    ).to_csv(
        path,
        index=False,
    )


def test_loads_valid_enriched_summary(
    tmp_path: Path,
) -> None:
    path = tmp_path / "summary.csv"

    write_dataset(
        path,
        player_ids=[
            1,
            2,
        ],
    )

    dataframe = load_player_tournament_summary(path)

    assert list(dataframe["player_id"]) == [
        1,
        2,
    ]


def test_rejects_duplicate_player_ids(
    tmp_path: Path,
) -> None:
    path = tmp_path / "summary.csv"

    write_dataset(
        path,
        player_ids=[
            1,
            1,
        ],
    )

    with pytest.raises(
        InvalidDatasetError,
        match="duplicate",
    ):
        load_player_tournament_summary(path)


def test_rejects_missing_required_column(
    tmp_path: Path,
) -> None:
    path = tmp_path / "summary.csv"

    write_dataset(
        path,
        player_ids=[
            1,
        ],
    )

    dataframe = pd.read_csv(path).drop(columns=["total_minutes"])

    dataframe.to_csv(
        path,
        index=False,
    )

    with pytest.raises(
        InvalidDatasetError,
        match="total_minutes",
    ):
        load_player_tournament_summary(path)
