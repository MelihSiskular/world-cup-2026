"""Download SofaScore match-level player heatmaps.

Endpoint:
https://www.sofascore.com/api/v1/event/{event_id}/player/{player_id}/heatmap

Examples:
    python -m src.get_data.collect_heatmaps \
      --event-id 12812996 --player-id 877994

    python -m src.get_data.collect_heatmaps --limit 10
    python -m src.get_data.collect_heatmaps --workers 4
"""

from __future__ import annotations

import argparse
import json
import random
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

DEFAULT_PLAYER_STATS = Path("data/processed/player_matches_analysis/player_match_stats.csv")
DEFAULT_MATCHES = Path("data/processed/player_matches_analysis/matches.csv")
DEFAULT_RAW_DIR = Path("data/raw/player_heatmaps/match_level")
DEFAULT_PROCESSED_DIR = Path("data/processed/player_heatmaps")

ENDPOINT = "https://www.sofascore.com/api/v1/event/{event_id}/player/{player_id}/heatmap"

EVENT_ID_COLUMNS = ["event_id", "match_id", "sofascore_event_id"]
PLAYER_ID_COLUMNS = ["player_id", "sofascore_player_id"]
PLAYER_NAME_COLUMNS = ["player_name", "name"]
TEAM_ID_COLUMNS = ["national_team_id", "team_id", "player_team_id"]
TEAM_NAME_COLUMNS = [
    "national_team_name",
    "team_name",
    "team",
    "player_team_name",
]
MINUTES_COLUMNS = ["stat_minutesPlayed", "minutes_played", "minutes"]
ROUND_NUMBER_COLUMNS = ["round_number", "round"]
ROUND_NAME_COLUMNS = ["round_name", "stage_name"]
MATCH_DATE_COLUMNS = ["start_timestamp", "match_date", "date"]


@dataclass
class DownloadResult:
    event_id: int
    player_id: int
    player_name: str
    status: str
    point_count: int
    method: str
    raw_path: str
    error: str = ""


def first_column(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    return next((column for column in candidates if column in df.columns), None)


def safe_int(value: Any) -> int | None:
    try:
        return None if value is None or pd.isna(value) else int(float(value))
    except (TypeError, ValueError):
        return None


def safe_float(value: Any) -> float | None:
    try:
        return None if value is None or pd.isna(value) else float(value)
    except (TypeError, ValueError):
        return None


def clean_text(value: Any) -> str:
    return "" if value is None or pd.isna(value) else str(value).strip()


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    return pd.read_csv(path, low_memory=False)


def build_pairs(
    player_stats: pd.DataFrame,
    matches: pd.DataFrame | None,
) -> pd.DataFrame:
    """Return one row for each eligible event-player pair."""
    stats = player_stats.copy()
    event_col = first_column(stats, EVENT_ID_COLUMNS)
    player_col = first_column(stats, PLAYER_ID_COLUMNS)

    if player_col is None:
        raise ValueError(
            "Player ID column not found. Expected one of: " + ", ".join(PLAYER_ID_COLUMNS)
        )

    if event_col is None:
        if matches is None:
            raise ValueError("Event ID is missing and matches.csv is unavailable.")

        matches_event_col = first_column(matches, EVENT_ID_COLUMNS)
        if matches_event_col is None:
            raise ValueError("Event ID column not found in matches.csv.")

        # Prefer a shared match identifier.
        join_candidates = [
            "match_id",
            "slug",
            "start_timestamp",
            "home_team_id",
            "away_team_id",
        ]
        join_col = next(
            (
                column
                for column in join_candidates
                if column in stats.columns and column in matches.columns
            ),
            None,
        )
        if join_col is None:
            raise ValueError(
                "Could not merge player stats with matches.csv. "
                "Add event_id to player_match_stats.csv."
            )

        lookup = (
            matches[[join_col, matches_event_col]]
            .dropna()
            .drop_duplicates(join_col)
            .rename(columns={matches_event_col: "_event_id"})
        )
        stats = stats.merge(lookup, on=join_col, how="left")
        event_col = "_event_id"

    output = pd.DataFrame(
        {
            "event_id": pd.to_numeric(stats[event_col], errors="coerce"),
            "player_id": pd.to_numeric(stats[player_col], errors="coerce"),
        }
    )

    optional = {
        "player_name": PLAYER_NAME_COLUMNS,
        "team_id": TEAM_ID_COLUMNS,
        "team_name": TEAM_NAME_COLUMNS,
        "minutes_played": MINUTES_COLUMNS,
        "round_number": ROUND_NUMBER_COLUMNS,
        "round_name": ROUND_NAME_COLUMNS,
        "match_date": MATCH_DATE_COLUMNS,
    }
    for canonical, candidates in optional.items():
        column = first_column(stats, candidates)
        output[canonical] = stats[column] if column else pd.NA

    output = output.dropna(subset=["event_id", "player_id"])
    output["event_id"] = output["event_id"].astype("int64")
    output["player_id"] = output["player_id"].astype("int64")
    output["player_name"] = output["player_name"].fillna("").astype(str)
    output["minutes_played"] = pd.to_numeric(output["minutes_played"], errors="coerce")

    if output["minutes_played"].notna().any():
        output = output[output["minutes_played"].fillna(0).gt(0)]

    return (
        output.drop_duplicates(["event_id", "player_id"])
        .sort_values(["event_id", "player_id"])
        .reset_index(drop=True)
    )


def headers() -> dict[str, str]:
    return {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.sofascore.com/",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
    }


def validate_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Response is not a JSON object.")
    heatmap = payload.get("heatmap")
    if heatmap is None:
        payload["heatmap"] = []
    elif not isinstance(heatmap, list):
        raise ValueError("Response field 'heatmap' is not a list.")
    return payload


class HeatmapUnavailableError(RuntimeError):
    """The endpoint confirms that no heatmap exists."""


class HeatmapRetryableError(RuntimeError):
    """The request may succeed after waiting or reusing the session."""


class PersistentHeatmapClient:
    """Reuse one browser session for all heatmap requests."""

    def __init__(
        self,
        *,
        headed: bool,
        timeout: float,
        bootstrap_wait: float,
    ) -> None:
        self.headed = headed
        self.timeout_ms = int(timeout * 1000)
        self.bootstrap_wait_ms = int(bootstrap_wait * 1000)
        self._playwright: Any = None
        self._browser: Any = None
        self._context: Any = None
        self._page: Any = None

    def __enter__(
        self,
    ) -> PersistentHeatmapClient:
        try:
            from playwright.sync_api import (
                sync_playwright,
            )
        except ImportError as error:
            raise RuntimeError(
                "Install Playwright with "
                "pip install -e '.[collection]' "
                "and playwright install chromium."
            ) from error

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=not self.headed)
        self._context = self._browser.new_context(
            user_agent=headers()["User-Agent"],
            locale="en-US",
            viewport={
                "width": 1440,
                "height": 1000,
            },
        )
        self._page = self._context.new_page()
        self._page.set_default_timeout(self.timeout_ms)

        response = self._page.goto(
            "https://www.sofascore.com/",
            wait_until="domcontentloaded",
            timeout=self.timeout_ms,
        )

        if response is not None and response.status >= 400:
            raise RuntimeError(f"SofaScore bootstrap failed: HTTP {response.status}.")

        if self.bootstrap_wait_ms > 0:
            self._page.wait_for_timeout(self.bootstrap_wait_ms)

        return self

    def fetch(
        self,
        event_id: int,
        player_id: int,
    ) -> dict[str, Any]:
        if self._page is None:
            raise RuntimeError("Persistent client is not open.")

        endpoint = ENDPOINT.format(
            event_id=event_id,
            player_id=player_id,
        )

        result = self._page.evaluate(
            """
            async ({endpoint}) => {
                try {
                    const response = await fetch(
                        endpoint,
                        {
                            method: "GET",
                            headers: {
                                "accept":
                                    "application/json, "
                                    + "text/plain, */*"
                            },
                            credentials: "include",
                            cache: "no-store"
                        }
                    );

                    return {
                        ok: response.ok,
                        status: response.status,
                        text: await response.text()
                    };
                } catch (error) {
                    return {
                        ok: false,
                        status: 0,
                        text:
                            `${error.name}: `
                            + `${error.message}`
                    };
                }
            }
            """,
            {"endpoint": endpoint},
        )

        status = int(result["status"])
        body = str(result["text"])

        if status == 404:
            raise HeatmapUnavailableError(f"Playwright HTTP 404: {body[:300]}")

        if status in {0, 403, 429} or status >= 500:
            raise HeatmapRetryableError(f"Playwright HTTP {status}: {body[:300]}")

        if not result["ok"]:
            raise RuntimeError(f"Playwright HTTP {status}: {body[:300]}")

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as error:
            raise HeatmapRetryableError("Playwright returned invalid JSON.") from error

        return validate_payload(payload)

    def __exit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> None:
        if self._context is not None:
            self._context.close()

        if self._browser is not None:
            self._browser.close()

        if self._playwright is not None:
            self._playwright.stop()

        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None


def raw_path(raw_dir: Path, event_id: int, player_id: int) -> Path:
    return raw_dir / f"{event_id}_{player_id}.json"


def read_cache(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return validate_payload(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temporary.replace(path)


def download_one(
    row: pd.Series,
    *,
    client: PersistentHeatmapClient,
    raw_dir: Path,
    force: bool,
    delay: float,
    attempts: int,
    backoff: float,
) -> DownloadResult:
    event_id = int(row["event_id"])
    player_id = int(row["player_id"])
    player_name = clean_text(row.get("player_name"))
    path = raw_path(
        raw_dir,
        event_id,
        player_id,
    )

    if not force:
        cached = read_cache(path)

        if cached is not None:
            return DownloadResult(
                event_id=event_id,
                player_id=player_id,
                player_name=player_name,
                status="cached",
                point_count=len(cached.get("heatmap", [])),
                method="cache",
                raw_path=str(path),
            )

    errors: list[str] = []

    for attempt in range(1, attempts + 1):
        if delay > 0:
            time.sleep(
                delay
                + random.uniform(
                    0,
                    delay * 0.35,
                )
            )

        try:
            payload = client.fetch(
                event_id,
                player_id,
            )
            save_json(path, payload)

            return DownloadResult(
                event_id=event_id,
                player_id=player_id,
                player_name=player_name,
                status="downloaded",
                point_count=len(payload.get("heatmap", [])),
                method="playwright-persistent",
                raw_path=str(path),
            )
        except HeatmapUnavailableError as error:
            return DownloadResult(
                event_id=event_id,
                player_id=player_id,
                player_name=player_name,
                status="unavailable",
                point_count=0,
                method="playwright-persistent",
                raw_path=str(path),
                error=str(error),
            )
        except Exception as error:
            errors.append(f"attempt={attempt} {type(error).__name__}: {error}")

            if attempt < attempts:
                wait_seconds = backoff * (2 ** (attempt - 1)) + random.uniform(
                    0,
                    max(backoff * 0.25, 0),
                )

                if wait_seconds > 0:
                    time.sleep(wait_seconds)

    return DownloadResult(
        event_id=event_id,
        player_id=player_id,
        player_name=player_name,
        status="failed",
        point_count=0,
        method="playwright-persistent",
        raw_path=str(path),
        error=" | ".join(errors),
    )


def build_long_csv(
    pairs: pd.DataFrame,
    raw_dir: Path,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for record in pairs.to_dict("records"):
        event_id = int(record["event_id"])
        player_id = int(record["player_id"])
        path = raw_path(
            raw_dir,
            event_id,
            player_id,
        )
        payload = read_cache(path)

        if payload is None:
            continue

        for point_index, point in enumerate(payload.get("heatmap", [])):
            if not isinstance(point, dict):
                continue

            x = safe_float(point.get("x"))
            y = safe_float(point.get("y"))

            if x is None or y is None:
                continue

            count = (
                safe_float(point.get("count"))
                or safe_float(point.get("value"))
                or safe_float(point.get("intensity"))
                or 1.0
            )

            rows.append(
                {
                    "event_id": event_id,
                    "player_id": player_id,
                    "player_name": clean_text(record.get("player_name")),
                    "team_id": safe_int(record.get("team_id")),
                    "team_name": clean_text(record.get("team_name")),
                    "minutes_played": safe_float(record.get("minutes_played")),
                    "round_number": record.get("round_number"),
                    "round_name": clean_text(record.get("round_name")),
                    "match_date": record.get("match_date"),
                    "point_index": point_index,
                    "x": x,
                    "y": y,
                    "count": count,
                    "raw_file": str(path),
                }
            )

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

    return pd.DataFrame(
        rows,
        columns=columns,
    )


def dataframe_pair_keys(
    dataframe: pd.DataFrame,
) -> set[tuple[int, int]]:
    if dataframe.empty or "event_id" not in dataframe or "player_id" not in dataframe:
        return set()

    keys = dataframe[["event_id", "player_id"]].copy()

    keys["event_id"] = pd.to_numeric(
        keys["event_id"],
        errors="coerce",
    )
    keys["player_id"] = pd.to_numeric(
        keys["player_id"],
        errors="coerce",
    )
    keys = keys.dropna()

    return {
        (
            int(row.event_id),
            int(row.player_id),
        )
        for row in keys.itertuples(index=False)
    }


def merge_manifest_tables(
    existing: pd.DataFrame,
    updates: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "event_id",
        "player_id",
        "player_name",
        "status",
        "point_count",
        "method",
        "raw_path",
        "error",
    ]

    records: dict[
        tuple[int, int],
        dict[str, Any],
    ] = {}

    for record in existing.to_dict("records"):
        event_id = safe_int(record.get("event_id"))
        player_id = safe_int(record.get("player_id"))

        if event_id is None or player_id is None:
            continue

        records[(event_id, player_id)] = {column: record.get(column, "") for column in columns}

    protected_statuses = {
        "downloaded",
        "cached",
        "unavailable",
    }

    for record in updates.to_dict("records"):
        event_id = safe_int(record.get("event_id"))
        player_id = safe_int(record.get("player_id"))

        if event_id is None or player_id is None:
            continue

        key = (event_id, player_id)
        current = records.get(key)

        if (
            clean_text(record.get("status")) == "failed"
            and current is not None
            and clean_text(current.get("status")) in protected_statuses
        ):
            continue

        records[key] = {column: record.get(column, "") for column in columns}

    merged = pd.DataFrame(
        records.values(),
        columns=columns,
    )

    if merged.empty:
        return merged

    return merged.sort_values(["event_id", "player_id"]).reset_index(drop=True)


def merge_long_tables(
    existing: pd.DataFrame,
    refreshed: pd.DataFrame,
    replace_pairs: set[tuple[int, int]],
) -> pd.DataFrame:
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

    if existing.empty:
        preserved = pd.DataFrame(columns=columns)
    else:
        existing_keys = [
            (
                safe_int(record.get("event_id")),
                safe_int(record.get("player_id")),
            )
            for record in existing.to_dict("records")
        ]

        keep_mask = [key not in replace_pairs for key in existing_keys]
        preserved = existing.loc[
            keep_mask,
            columns,
        ]

    frames = [preserved]

    if not refreshed.empty:
        frames.append(refreshed.reindex(columns=columns))

    merged = pd.concat(
        frames,
        ignore_index=True,
    )

    if merged.empty:
        return pd.DataFrame(columns=columns)

    return (
        merged.drop_duplicates(
            [
                "event_id",
                "player_id",
                "point_index",
            ],
            keep="last",
        )
        .sort_values(
            [
                "event_id",
                "player_id",
                "point_index",
            ]
        )
        .reset_index(drop=True)
    )


def select_missing_pairs(
    pairs: pd.DataFrame,
    existing_manifest: pd.DataFrame,
    existing_long: pd.DataFrame,
) -> pd.DataFrame:
    covered_pairs = dataframe_pair_keys(existing_long)

    if not existing_manifest.empty:
        statuses = existing_manifest["status"].fillna("").astype(str)
        point_counts = pd.to_numeric(
            existing_manifest["point_count"],
            errors="coerce",
        )

        terminal_mask = statuses.eq("unavailable") | (
            statuses.isin(["downloaded", "cached"]) & point_counts.fillna(-1).eq(0)
        )

        covered_pairs.update(dataframe_pair_keys(existing_manifest.loc[terminal_mask]))

    missing_mask = pairs.apply(
        lambda row: (
            (
                int(row["event_id"]),
                int(row["player_id"]),
            )
            not in covered_pairs
        ),
        axis=1,
    )

    return pairs.loc[missing_mask].reset_index(drop=True)


def atomic_write_csv(
    dataframe: pd.DataFrame,
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_name(f".{path.name}.{time.time_ns()}.tmp")

    try:
        dataframe.to_csv(
            temporary,
            index=False,
        )
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download SofaScore player heatmaps.")
    parser.add_argument("--player-stats", type=Path, default=DEFAULT_PLAYER_STATS)
    parser.add_argument("--matches", type=Path, default=DEFAULT_MATCHES)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--processed-dir", type=Path, default=DEFAULT_PROCESSED_DIR)
    parser.add_argument("--event-id", type=int)
    parser.add_argument("--player-id", type=int)
    parser.add_argument("--player", type=str)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=25.0)
    parser.add_argument("--delay", type=float, default=0.15)
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--cache-only",
        action="store_true",
        help=("Merge valid raw cache files without performing network requests."),
    )
    parser.add_argument(
        "--missing-only",
        action="store_true",
        help=("Process only pairs without canonical heatmap data or a terminal manifest result."),
    )
    parser.add_argument(
        "--attempts",
        type=int,
        default=3,
        help="Maximum persistent-browser attempts per pair.",
    )
    parser.add_argument(
        "--backoff",
        type=float,
        default=3.0,
        help="Initial exponential retry delay in seconds.",
    )
    parser.add_argument(
        "--bootstrap-wait",
        type=float,
        default=3.0,
        help=("Seconds to wait after loading SofaScore before the first API request."),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if (args.event_id is None) != (args.player_id is None):
        raise ValueError("--event-id and --player-id must be supplied together.")

    if args.attempts < 1:
        raise ValueError("--attempts must be at least 1.")

    if args.backoff < 0:
        raise ValueError("--backoff must not be negative.")

    if args.bootstrap_wait < 0:
        raise ValueError("--bootstrap-wait must not be negative.")

    if not args.cache_only and args.workers != 1:
        raise ValueError("Persistent network collection requires --workers 1.")

    stats = load_csv(args.player_stats)
    matches = load_csv(args.matches) if args.matches.exists() else None
    pairs = build_pairs(stats, matches)

    if args.event_id is not None:
        selected = pairs[
            pairs["event_id"].eq(args.event_id) & pairs["player_id"].eq(args.player_id)
        ]
        if selected.empty:
            selected = pd.DataFrame(
                [
                    {
                        "event_id": args.event_id,
                        "player_id": args.player_id,
                        "player_name": args.player or "",
                        "team_id": pd.NA,
                        "team_name": "",
                        "minutes_played": pd.NA,
                        "round_number": pd.NA,
                        "round_name": "",
                        "match_date": pd.NA,
                    }
                ]
            )
        pairs = selected

    if args.player:
        pairs = pairs[
            pairs["player_name"].str.contains(args.player, case=False, regex=False, na=False)
        ]

    if args.missing_only:
        selection_manifest_path = args.processed_dir / "player_heatmap_download_manifest.csv"
        selection_long_path = args.processed_dir / "player_heatmaps_match_level.csv"

        selection_manifest = (
            pd.read_csv(
                selection_manifest_path,
                low_memory=False,
            )
            if selection_manifest_path.exists()
            else pd.DataFrame()
        )
        selection_long = (
            pd.read_csv(
                selection_long_path,
                low_memory=False,
            )
            if selection_long_path.exists()
            else pd.DataFrame()
        )

        pairs = select_missing_pairs(
            pairs,
            selection_manifest,
            selection_long,
        )

    if args.limit is not None:
        pairs = pairs.head(args.limit)

    if pairs.empty:
        raise ValueError("No eligible event-player pairs found.")

    args.raw_dir.mkdir(parents=True, exist_ok=True)
    args.processed_dir.mkdir(parents=True, exist_ok=True)

    results: list[DownloadResult] = []
    cache_misses = 0

    if args.cache_only:
        for _, row in pairs.iterrows():
            event_id = int(row["event_id"])
            player_id = int(row["player_id"])
            path = raw_path(
                args.raw_dir,
                event_id,
                player_id,
            )
            cached = read_cache(path)

            if cached is None:
                cache_misses += 1
                continue

            results.append(
                DownloadResult(
                    event_id=event_id,
                    player_id=player_id,
                    player_name=clean_text(row.get("player_name")),
                    status="cached",
                    point_count=len(cached.get("heatmap", [])),
                    method="cache",
                    raw_path=str(path),
                )
            )
    else:
        with PersistentHeatmapClient(
            headed=args.headed,
            timeout=args.timeout,
            bootstrap_wait=args.bootstrap_wait,
        ) as client:
            for index, (_, row) in enumerate(
                pairs.iterrows(),
                start=1,
            ):
                result = download_one(
                    row,
                    client=client,
                    raw_dir=args.raw_dir,
                    force=args.force,
                    delay=args.delay,
                    attempts=args.attempts,
                    backoff=args.backoff,
                )
                results.append(result)

                print(
                    f"[{index}/{len(pairs)}] "
                    f"{result.status.upper():<12} "
                    f"event={result.event_id} "
                    f"player={result.player_id} "
                    f"points={result.point_count} "
                    f"method={result.method}"
                )

    manifest_columns = [
        "event_id",
        "player_id",
        "player_name",
        "status",
        "point_count",
        "method",
        "raw_path",
        "error",
    ]

    manifest_updates = pd.DataFrame(
        [asdict(result) for result in results],
        columns=manifest_columns,
    )

    manifest_path = args.processed_dir / "player_heatmap_download_manifest.csv"
    long_path = args.processed_dir / "player_heatmaps_match_level.csv"

    existing_manifest = (
        pd.read_csv(
            manifest_path,
            low_memory=False,
        )
        if manifest_path.exists()
        else pd.DataFrame(columns=manifest_columns)
    )

    long_columns = [
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

    existing_long = (
        pd.read_csv(
            long_path,
            low_memory=False,
        )
        if long_path.exists()
        else pd.DataFrame(columns=long_columns)
    )

    merged_manifest = merge_manifest_tables(
        existing_manifest,
        manifest_updates,
    )

    successful_updates = manifest_updates[manifest_updates["status"].isin(["downloaded", "cached"])]
    replace_pairs = dataframe_pair_keys(successful_updates)

    if replace_pairs:
        refresh_mask = pairs.apply(
            lambda row: (
                (
                    int(row["event_id"]),
                    int(row["player_id"]),
                )
                in replace_pairs
            ),
            axis=1,
        )
        refresh_pairs = pairs.loc[refresh_mask]
        refreshed_long = build_long_csv(
            refresh_pairs,
            args.raw_dir,
        )
    else:
        refreshed_long = pd.DataFrame(columns=long_columns)

    merged_long = merge_long_tables(
        existing_long,
        refreshed_long,
        replace_pairs,
    )

    if results:
        atomic_write_csv(
            merged_manifest,
            manifest_path,
        )
        atomic_write_csv(
            merged_long,
            long_path,
        )

    manifest = manifest_updates
    long_df = merged_long

    if args.cache_only:
        print(f"Cache files merged: {len(results)}")
        print(f"Pairs without cache: {cache_misses}")

    counts = manifest["status"].value_counts() if not manifest.empty else {}
    print("\n" + "=" * 78)
    print("HEATMAP DOWNLOAD SUMMARY")
    print("=" * 78)
    for status in [
        "downloaded",
        "cached",
        "unavailable",
        "failed",
    ]:
        count = int(counts.get(status, 0)) if hasattr(counts, "get") else 0
        print(f"{status:<16}{count:>8}")
    print(f"{'heatmap points':<16}{len(long_df):>8}")
    print("\nOUTPUTS")
    print(f"Raw JSON: {args.raw_dir}")
    print(f"Manifest: {manifest_path}")
    print(f"Long CSV: {long_path}")


if __name__ == "__main__":
    main()
