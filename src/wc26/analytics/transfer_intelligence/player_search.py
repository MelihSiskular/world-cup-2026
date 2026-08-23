"""Application service for searching Transfer Intelligence players."""

from __future__ import annotations

import math
import unicodedata
from collections.abc import Mapping
from dataclasses import replace
from typing import Any, Final, cast

import numpy as np
import pandas as pd

from wc26.analytics.transfer_intelligence.datasets import (
    load_player_features,
)
from wc26.analytics.transfer_intelligence.errors import (
    InvalidDatasetError,
    InvalidPlayerSearchError,
)
from wc26.analytics.transfer_intelligence.models import (
    PlayerSearchItem,
    PlayerSearchRequest,
    PlayerSearchResult,
)

MINIMUM_QUERY_LENGTH: Final[int] = 2
MINIMUM_RESULT_LIMIT: Final[int] = 1
MAXIMUM_RESULT_LIMIT: Final[int] = 25

PLAYER_SEARCH_COLUMNS: Final[tuple[str, ...]] = (
    "player_id",
    "player_name",
    "national_team_name",
    "position",
    "final_role",
    "archetype",
    "age",
    "market_value",
    "market_value_currency",
)

PLAYER_SEARCH_OPTIONAL_COLUMNS: Final[tuple[str, ...]] = (
    "country_alpha3",
    "spatial_role",
)


def _normalize_search_text(value: str) -> str:
    """Normalize case, whitespace, and common diacritics for searching."""

    normalized = unicodedata.normalize(
        "NFKD",
        value,
    )

    without_diacritics = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )

    without_diacritics = (
        without_diacritics.replace("ı", "i")
        .replace("æ", "ae")
        .replace("œ", "oe")
        .replace("ø", "o")
        .replace("ł", "l")
    )

    return " ".join(without_diacritics.casefold().split())


def _validate_request(
    request: PlayerSearchRequest,
) -> tuple[str, str]:
    """Validate search parameters and return display and normalized queries."""

    display_query = " ".join(request.query.split())
    normalized_query = _normalize_search_text(display_query)

    if len(normalized_query) < MINIMUM_QUERY_LENGTH:
        raise InvalidPlayerSearchError(
            f"Player search query must contain at least {MINIMUM_QUERY_LENGTH} characters."
        )

    if not (MINIMUM_RESULT_LIMIT <= request.limit <= MAXIMUM_RESULT_LIMIT):
        raise InvalidPlayerSearchError(
            "Player search limit must be between "
            f"{MINIMUM_RESULT_LIMIT} and "
            f"{MAXIMUM_RESULT_LIMIT}."
        )

    return display_query, normalized_query


def _is_missing_value(
    value: object,
) -> bool:
    """Return whether a scalar dataset value is missing."""

    if value is None or value is pd.NA or value is pd.NaT:
        return True

    if isinstance(
        value,
        (float, np.floating),
    ):
        return math.isnan(float(value))

    return False


def _optional_text(
    value: object,
) -> str | None:
    """Convert a dataset value into an optional string."""

    if _is_missing_value(value):
        return None

    text = str(value).strip()

    return text or None


def _optional_float(
    value: object,
) -> float | None:
    """Convert a dataset value into an optional finite float."""

    if _is_missing_value(value):
        return None

    try:
        result = float(str(value).strip())
    except ValueError:
        return None

    if not math.isfinite(result):
        return None

    return result


def _required_player_id(
    value: object,
) -> int:
    """Convert and validate a player identifier."""

    if _is_missing_value(value):
        raise InvalidDatasetError("Player search dataset contains an invalid player_id.")

    try:
        numeric_value = float(str(value).strip())
    except ValueError as exception:
        raise InvalidDatasetError(
            "Player search dataset contains an invalid player_id."
        ) from exception

    if not math.isfinite(numeric_value) or not numeric_value.is_integer():
        raise InvalidDatasetError("Player search dataset contains an invalid player_id.")

    return int(numeric_value)


def _required_player_name(
    value: object,
) -> str:
    """Convert and validate a player name."""

    player_name = _optional_text(value)

    if player_name is None:
        raise InvalidDatasetError("Player search dataset contains an invalid player_name.")

    return player_name


def _match_rank(
    player_name: str,
    query: str,
) -> int:
    """Rank exact, prefix, token-prefix, and contains matches."""

    if player_name == query:
        return 0

    if player_name.startswith(query):
        return 1

    if any(token.startswith(query) for token in player_name.split()):
        return 2

    return 3


def enrich_player_search_country_codes(
    result: PlayerSearchResult,
    player_tournament_summary: pd.DataFrame | None,
) -> PlayerSearchResult:
    """Attach ISO alpha-3 country codes without changing search ranking."""

    if (
        player_tournament_summary is None
        or player_tournament_summary.empty
        or "player_id" not in player_tournament_summary.columns
        or "country_alpha3" not in player_tournament_summary.columns
    ):
        return result

    identity_frame = player_tournament_summary[
        [
            "player_id",
            "country_alpha3",
        ]
    ].copy()

    identity_frame["player_id"] = pd.to_numeric(
        identity_frame["player_id"],
        errors="coerce",
    )

    identity_frame = identity_frame.dropna(subset=["player_id"]).drop_duplicates(
        subset=["player_id"],
        keep="first",
    )

    country_codes: dict[int, str] = {}

    for row in identity_frame.itertuples(
        index=False,
    ):
        code = _optional_text(
            row.country_alpha3,
        )

        if code is None:
            continue

        normalized = code.strip().upper()

        if len(normalized) != 3 or not normalized.isascii() or not normalized.isalpha():
            continue

        country_codes[int(row.player_id)] = normalized

    if not country_codes:
        return result

    return replace(
        result,
        players=tuple(
            replace(
                player,
                country_alpha3=country_codes.get(
                    player.player_id,
                ),
            )
            for player in result.players
        ),
    )


def _record_to_item(
    record: Mapping[str, object],
) -> PlayerSearchItem:
    """Convert one dataset record into the public search contract."""

    return PlayerSearchItem(
        player_id=_required_player_id(record["player_id"]),
        player_name=_required_player_name(record["player_name"]),
        national_team_name=_optional_text(record["national_team_name"]),
        country_alpha3=_optional_text(
            record.get("country_alpha3"),
        ),
        position=_optional_text(record["position"]),
        final_role=_optional_text(record["final_role"]),
        archetype=_optional_text(record["archetype"]),
        spatial_role=_optional_text(
            record.get("spatial_role"),
        ),
        age=_optional_float(record["age"]),
        market_value=_optional_float(record["market_value"]),
        market_value_currency=_optional_text(record["market_value_currency"]),
    )


def _search_players_in_dataframe(
    *,
    dataframe: pd.DataFrame,
    display_query: str,
    normalized_query: str,
    limit: int,
) -> PlayerSearchResult:
    """Search a prepared player DataFrame."""

    missing_columns = set(PLAYER_SEARCH_COLUMNS).difference(dataframe.columns)

    if missing_columns:
        raise InvalidDatasetError(
            "Missing player search columns: " + ", ".join(sorted(missing_columns))
        )

    result_columns = list(PLAYER_SEARCH_COLUMNS)

    result_columns.extend(
        column for column in PLAYER_SEARCH_OPTIONAL_COLUMNS if column in dataframe.columns
    )

    search_frame = dataframe[result_columns].copy()

    search_frame = search_frame.dropna(
        subset=[
            "player_id",
            "player_name",
        ]
    )

    search_frame["_normalized_name"] = (
        search_frame["player_name"].astype(str).map(_normalize_search_text)
    )

    matches = search_frame.loc[
        search_frame["_normalized_name"].str.contains(
            normalized_query,
            regex=False,
            na=False,
        )
    ].copy()

    matches["_match_rank"] = matches["_normalized_name"].map(
        lambda player_name: _match_rank(
            str(player_name),
            normalized_query,
        )
    )

    matches = (
        matches.sort_values(
            by=[
                "_match_rank",
                "_normalized_name",
                "player_id",
            ],
            kind="stable",
        )
        .drop_duplicates(
            subset=["player_id"],
            keep="first",
        )
        .head(limit)
    )

    records = cast(
        list[dict[str, Any]],
        matches[result_columns].to_dict(orient="records"),
    )

    players = tuple(_record_to_item(record) for record in records)

    return PlayerSearchResult(
        query=display_query,
        players=players,
    )


def search_players_from_dataframe(
    request: PlayerSearchRequest,
    dataframe: pd.DataFrame,
) -> PlayerSearchResult:
    """Search players using an already loaded feature table."""

    display_query, normalized_query = _validate_request(request)

    return _search_players_in_dataframe(
        dataframe=dataframe,
        display_query=display_query,
        normalized_query=normalized_query,
        limit=request.limit,
    )


def search_players(
    request: PlayerSearchRequest,
) -> PlayerSearchResult:
    """Search players using the configured feature dataset."""

    display_query, normalized_query = _validate_request(request)

    dataframe = load_player_features(request.features)

    return _search_players_in_dataframe(
        dataframe=dataframe,
        display_query=display_query,
        normalized_query=normalized_query,
        limit=request.limit,
    )


__all__ = [
    "MAXIMUM_RESULT_LIMIT",
    "MINIMUM_QUERY_LENGTH",
    "MINIMUM_RESULT_LIMIT",
    "PLAYER_SEARCH_COLUMNS",
    "search_players",
    "search_players_from_dataframe",
]
