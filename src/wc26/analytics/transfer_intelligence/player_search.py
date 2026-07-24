"""Application service for searching Transfer Intelligence players."""

from __future__ import annotations

import math
import unicodedata
from collections.abc import Mapping
from typing import Any, Final, cast

import numpy as np
import pandas as pd

from wc26.analytics.transfer_intelligence.errors import (
    DatasetNotFoundError,
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


def _record_to_item(
    record: Mapping[str, object],
) -> PlayerSearchItem:
    """Convert one dataset record into the public search contract."""

    return PlayerSearchItem(
        player_id=_required_player_id(record["player_id"]),
        player_name=_required_player_name(record["player_name"]),
        national_team_name=_optional_text(record["national_team_name"]),
        position=_optional_text(record["position"]),
        final_role=_optional_text(record["final_role"]),
        archetype=_optional_text(record["archetype"]),
        age=_optional_float(record["age"]),
        market_value=_optional_float(record["market_value"]),
        market_value_currency=_optional_text(record["market_value_currency"]),
    )


def search_players(
    request: PlayerSearchRequest,
) -> PlayerSearchResult:
    """Search players by a case- and diacritic-insensitive name query."""

    display_query, normalized_query = _validate_request(request)

    if not request.features.exists():
        raise DatasetNotFoundError(f"Player feature table not found: {request.features}")

    try:
        dataframe = pd.read_csv(
            request.features,
            low_memory=False,
        )
    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
    ) as exception:
        raise InvalidDatasetError("Player feature table could not be read.") from exception

    missing_columns = set(PLAYER_SEARCH_COLUMNS).difference(dataframe.columns)

    if missing_columns:
        raise InvalidDatasetError(
            "Missing player search columns: " + ", ".join(sorted(missing_columns))
        )

    search_frame = dataframe[list(PLAYER_SEARCH_COLUMNS)].copy()

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
        .head(request.limit)
    )

    records = cast(
        list[dict[str, Any]],
        matches[list(PLAYER_SEARCH_COLUMNS)].to_dict(orient="records"),
    )

    players = tuple(_record_to_item(record) for record in records)

    return PlayerSearchResult(
        query=display_query,
        players=players,
    )


__all__ = [
    "MAXIMUM_RESULT_LIMIT",
    "MINIMUM_QUERY_LENGTH",
    "MINIMUM_RESULT_LIMIT",
    "PLAYER_SEARCH_COLUMNS",
    "search_players",
]
