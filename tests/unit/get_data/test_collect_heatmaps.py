from __future__ import annotations

import pandas as pd
from src.get_data.collect_heatmaps import (
    HeatmapUnavailableError,
    download_one,
    merge_long_tables,
    merge_manifest_tables,
    select_missing_pairs,
)


def test_manifest_merge_preserves_success_after_failed_retry() -> None:
    existing = pd.DataFrame(
        [
            {
                "event_id": 10,
                "player_id": 20,
                "player_name": "Player",
                "status": "downloaded",
                "point_count": 2,
                "method": "playwright",
                "raw_path": "raw.json",
                "error": "",
            }
        ]
    )
    updates = pd.DataFrame(
        [
            {
                "event_id": 10,
                "player_id": 20,
                "player_name": "Player",
                "status": "failed",
                "point_count": 0,
                "method": "none",
                "raw_path": "raw.json",
                "error": "HTTP 403",
            }
        ]
    )

    merged = merge_manifest_tables(
        existing,
        updates,
    )

    assert len(merged) == 1
    assert merged.iloc[0]["status"] == "downloaded"
    assert merged.iloc[0]["point_count"] == 2


def test_manifest_merge_adds_a_new_pair() -> None:
    existing = pd.DataFrame(
        columns=[
            "event_id",
            "player_id",
            "player_name",
            "status",
            "point_count",
            "method",
            "raw_path",
            "error",
        ]
    )
    updates = pd.DataFrame(
        [
            {
                "event_id": 11,
                "player_id": 21,
                "player_name": "New Player",
                "status": "cached",
                "point_count": 1,
                "method": "cache",
                "raw_path": "new.json",
                "error": "",
            }
        ]
    )

    merged = merge_manifest_tables(
        existing,
        updates,
    )

    assert len(merged) == 1
    assert merged.iloc[0]["event_id"] == 11
    assert merged.iloc[0]["player_id"] == 21


def test_long_merge_replaces_only_the_refreshed_pair() -> None:
    columns = [
        "event_id",
        "player_id",
        "player_name",
        "team_id",
        "team_name",
        "minutes_played",
        "round_number",
        "round_name",
        "match_date",
        "point_index",
        "x",
        "y",
        "count",
        "raw_file",
    ]

    existing = pd.DataFrame(
        [
            [10, 20, "A", 1, "T", 90, 1, "", "", 0, 1, 2, 1, "old-a"],
            [11, 21, "B", 1, "T", 90, 1, "", "", 0, 3, 4, 1, "old-b"],
        ],
        columns=columns,
    )
    refreshed = pd.DataFrame(
        [
            [10, 20, "A", 1, "T", 90, 1, "", "", 0, 8, 9, 2, "new-a"],
        ],
        columns=columns,
    )

    merged = merge_long_tables(
        existing,
        refreshed,
        {(10, 20)},
    )

    assert len(merged) == 2

    refreshed_row = merged[merged["player_id"].eq(20)].iloc[0]
    preserved_row = merged[merged["player_id"].eq(21)].iloc[0]

    assert refreshed_row["x"] == 8
    assert refreshed_row["raw_file"] == "new-a"
    assert preserved_row["x"] == 3
    assert preserved_row["raw_file"] == "old-b"


class RetryThenSuccessClient:
    def __init__(self) -> None:
        self.calls = 0

    def fetch(
        self,
        event_id: int,
        player_id: int,
    ) -> dict[str, object]:
        self.calls += 1

        if self.calls == 1:
            raise RuntimeError("temporary 403")

        return {
            "heatmap": [
                {"x": 60, "y": 25},
            ]
        }


class UnavailableClient:
    def fetch(
        self,
        event_id: int,
        player_id: int,
    ) -> dict[str, object]:
        raise HeatmapUnavailableError("Playwright HTTP 404")


def test_persistent_download_retries_and_saves_cache(
    tmp_path,
) -> None:
    client = RetryThenSuccessClient()
    row = pd.Series(
        {
            "event_id": 30,
            "player_id": 40,
            "player_name": "Retry Player",
        }
    )

    result = download_one(
        row,
        client=client,
        raw_dir=tmp_path,
        force=False,
        delay=0,
        attempts=2,
        backoff=0,
    )

    assert client.calls == 2
    assert result.status == "downloaded"
    assert result.point_count == 1
    assert (tmp_path / "30_40.json").exists()


def test_persistent_download_marks_404_unavailable(
    tmp_path,
) -> None:
    row = pd.Series(
        {
            "event_id": 31,
            "player_id": 41,
            "player_name": "Missing Player",
        }
    )

    result = download_one(
        row,
        client=UnavailableClient(),
        raw_dir=tmp_path,
        force=False,
        delay=0,
        attempts=3,
        backoff=0,
    )

    assert result.status == "unavailable"
    assert result.point_count == 0
    assert not (tmp_path / "31_41.json").exists()


def test_missing_selection_skips_canonical_and_terminal_pairs() -> None:
    pairs = pd.DataFrame(
        [
            {"event_id": 1, "player_id": 10},
            {"event_id": 2, "player_id": 20},
            {"event_id": 3, "player_id": 30},
        ]
    )
    existing_long = pd.DataFrame(
        [
            {
                "event_id": 1,
                "player_id": 10,
            }
        ]
    )
    existing_manifest = pd.DataFrame(
        [
            {
                "event_id": 2,
                "player_id": 20,
                "status": "unavailable",
                "point_count": 0,
            }
        ]
    )

    missing = select_missing_pairs(
        pairs,
        existing_manifest,
        existing_long,
    )

    assert missing[["event_id", "player_id"]].to_dict("records") == [
        {
            "event_id": 3,
            "player_id": 30,
        }
    ]


def test_empty_refresh_does_not_emit_future_warning() -> None:
    columns = [
        "event_id",
        "player_id",
        "player_name",
        "team_id",
        "team_name",
        "minutes_played",
        "round_number",
        "round_name",
        "match_date",
        "point_index",
        "x",
        "y",
        "count",
        "raw_file",
    ]
    existing = pd.DataFrame(
        [
            [
                1,
                10,
                "Player",
                1,
                "Team",
                90,
                1,
                "",
                "",
                0,
                1,
                2,
                1,
                "raw",
            ]
        ],
        columns=columns,
    )
    refreshed = pd.DataFrame(columns=columns)

    merged = merge_long_tables(
        existing,
        refreshed,
        set(),
    )

    assert len(merged) == 1
