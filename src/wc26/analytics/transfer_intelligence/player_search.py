"""Application service for discovering Transfer Intelligence players."""

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
    load_player_tournament_summary,
)
from wc26.analytics.transfer_intelligence.errors import (
    InvalidDatasetError,
    InvalidPlayerSearchError,
)
from wc26.analytics.transfer_intelligence.models import (
    PlayerSearchFilterOption,
    PlayerSearchFilterRange,
    PlayerSearchFiltersRequest,
    PlayerSearchFiltersResult,
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
    "country_name",
    "position",
    "final_role",
    "archetype",
    "age",
    "market_value",
    "market_value_currency",
    "minutes",
    "role_confidence_pct",
    "data_reliability_score",
    "player_quality_score",
)

PLAYER_SEARCH_OPTIONAL_COLUMNS: Final[tuple[str, ...]] = (
    "country_alpha3",
    "spatial_role",
)

_SORT_COLUMNS: Final[dict[str, str]] = {
    "player_name": "_normalized_name",
    "age": "age",
    "market_value": "market_value",
    "minutes": "minutes",
    "role_confidence": "role_confidence_pct",
    "data_reliability": "data_reliability_score",
    "player_quality": "player_quality_score",
}

_NUMERIC_COLUMNS: Final[tuple[str, ...]] = (
    "age",
    "market_value",
    "minutes",
    "role_confidence_pct",
    "data_reliability_score",
    "player_quality_score",
)


def _normalize_search_text(value: str) -> str:
    """Normalize case, whitespace, and common diacritics."""

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


def _normalize_category_values(
    values: tuple[str, ...],
) -> tuple[str, ...]:
    """Trim and de-duplicate categorical filter values."""

    normalized: list[str] = []
    seen: set[str] = set()

    for value in values:
        display_value = " ".join(value.split())

        if not display_value:
            continue

        comparison_value = _normalize_search_text(
            display_value,
        )

        if comparison_value in seen:
            continue

        seen.add(comparison_value)
        normalized.append(display_value)

    return tuple(normalized)


def _validate_optional_number(
    *,
    label: str,
    value: float | None,
    minimum: float | None = None,
    maximum: float | None = None,
) -> None:
    """Validate one optional finite numeric filter."""

    if value is None:
        return

    if not math.isfinite(value):
        raise InvalidPlayerSearchError(f"{label} must be a finite number.")

    if minimum is not None and value < minimum:
        raise InvalidPlayerSearchError(f"{label} must be at least {minimum:g}.")

    if maximum is not None and value > maximum:
        raise InvalidPlayerSearchError(f"{label} must be at most {maximum:g}.")


def _validate_request(
    request: PlayerSearchRequest,
) -> PlayerSearchRequest:
    """Normalize and validate player-discovery parameters."""

    display_query: str | None = None

    if request.query is not None:
        candidate_query = " ".join(request.query.split())

        if candidate_query:
            display_query = candidate_query

    positions = _normalize_category_values(
        request.positions,
    )
    final_roles = _normalize_category_values(
        request.final_roles,
    )
    archetypes = _normalize_category_values(
        request.archetypes,
    )
    countries = _normalize_category_values(
        request.countries,
    )

    if (
        display_query is not None
        and len(
            _normalize_search_text(
                display_query,
            )
        )
        < MINIMUM_QUERY_LENGTH
    ):
        raise InvalidPlayerSearchError(
            f"Player search query must contain at least {MINIMUM_QUERY_LENGTH} characters."
        )

    has_filter = bool(
        positions
        or final_roles
        or archetypes
        or countries
        or request.minimum_age is not None
        or request.maximum_age is not None
        or request.minimum_market_value is not None
        or request.maximum_market_value is not None
        or request.minimum_minutes is not None
        or request.minimum_role_confidence is not None
        or request.minimum_data_reliability is not None
    )

    if display_query is None and not has_filter:
        raise InvalidPlayerSearchError(
            "Player discovery requires a name query or at least one filter."
        )

    if not (MINIMUM_RESULT_LIMIT <= request.limit <= MAXIMUM_RESULT_LIMIT):
        raise InvalidPlayerSearchError(
            "Player search limit must be between "
            f"{MINIMUM_RESULT_LIMIT} and "
            f"{MAXIMUM_RESULT_LIMIT}."
        )

    if request.offset < 0:
        raise InvalidPlayerSearchError("Player search offset cannot be negative.")

    _validate_optional_number(
        label="Minimum age",
        value=request.minimum_age,
        minimum=0,
    )
    _validate_optional_number(
        label="Maximum age",
        value=request.maximum_age,
        minimum=0,
    )
    _validate_optional_number(
        label="Minimum market value",
        value=request.minimum_market_value,
        minimum=0,
    )
    _validate_optional_number(
        label="Maximum market value",
        value=request.maximum_market_value,
        minimum=0,
    )
    _validate_optional_number(
        label="Minimum minutes",
        value=request.minimum_minutes,
        minimum=0,
    )
    _validate_optional_number(
        label="Minimum role confidence",
        value=request.minimum_role_confidence,
        minimum=0,
        maximum=100,
    )
    _validate_optional_number(
        label="Minimum data reliability",
        value=request.minimum_data_reliability,
        minimum=0,
        maximum=100,
    )

    if (
        request.minimum_age is not None
        and request.maximum_age is not None
        and request.minimum_age > request.maximum_age
    ):
        raise InvalidPlayerSearchError("Minimum age cannot exceed maximum age.")

    if (
        request.minimum_market_value is not None
        and request.maximum_market_value is not None
        and request.minimum_market_value > request.maximum_market_value
    ):
        raise InvalidPlayerSearchError("Minimum market value cannot exceed maximum market value.")

    sort_by = request.sort_by

    if sort_by is None:
        sort_by = "relevance" if display_query is not None else "player_quality"

    if sort_by != "relevance" and sort_by not in _SORT_COLUMNS:
        raise InvalidPlayerSearchError("Unsupported player search sort field.")

    if sort_by == "relevance" and display_query is None:
        raise InvalidPlayerSearchError("Relevance sorting requires a name query.")

    sort_direction = request.sort_direction

    if sort_direction is None:
        sort_direction = (
            "asc"
            if sort_by
            in {
                "relevance",
                "player_name",
            }
            else "desc"
        )

    if sort_direction not in {
        "asc",
        "desc",
    }:
        raise InvalidPlayerSearchError("Player search sort direction must be asc or desc.")

    if sort_by == "relevance":
        sort_direction = "asc"

    return replace(
        request,
        query=display_query,
        positions=positions,
        final_roles=final_roles,
        archetypes=archetypes,
        countries=countries,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )


def _is_missing_value(
    value: object,
) -> bool:
    """Return whether a scalar dataset value is missing."""

    if value is None or value is pd.NA or value is pd.NaT:
        return True

    if isinstance(
        value,
        (
            float,
            np.floating,
        ),
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

    player_name = _optional_text(
        value,
    )

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
    """Attach ISO alpha-3 country codes without changing result order."""

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

        try:
            player_id = _required_player_id(
                row.player_id,
            )
        except InvalidDatasetError:
            continue

        country_codes[player_id] = normalized

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
        country_name=_optional_text(record["country_name"]),
        country_alpha3=_optional_text(record.get("country_alpha3")),
        position=_optional_text(record["position"]),
        final_role=_optional_text(record["final_role"]),
        archetype=_optional_text(record["archetype"]),
        spatial_role=_optional_text(record.get("spatial_role")),
        age=_optional_float(record["age"]),
        market_value=_optional_float(record["market_value"]),
        market_value_currency=_optional_text(record["market_value_currency"]),
        minutes=_optional_float(record["minutes"]),
        role_confidence_pct=_optional_float(record["role_confidence_pct"]),
        data_reliability_score=_optional_float(record["data_reliability_score"]),
        player_quality_score=_optional_float(record["player_quality_score"]),
    )


def _apply_categorical_filter(
    dataframe: pd.DataFrame,
    *,
    column: str,
    values: tuple[str, ...],
) -> pd.DataFrame:
    """Apply one case-insensitive OR categorical filter."""

    if not values:
        return dataframe

    accepted = {_normalize_search_text(value) for value in values}

    normalized_column = dataframe[column].fillna("").astype(str).map(_normalize_search_text)

    return dataframe.loc[
        normalized_column.isin(
            accepted,
        )
    ]


def _prepare_search_frame(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str]]:
    """Validate and prepare the searchable feature table."""

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

    for column in _NUMERIC_COLUMNS:
        search_frame[column] = pd.to_numeric(
            search_frame[column],
            errors="coerce",
        )

    return search_frame, result_columns


def _filter_search_frame(
    dataframe: pd.DataFrame,
    request: PlayerSearchRequest,
) -> pd.DataFrame:
    """Apply name, categorical, and numeric filters."""

    result = dataframe

    if request.query is not None:
        normalized_query = _normalize_search_text(
            request.query,
        )

        result = result.loc[
            result["_normalized_name"].str.contains(
                normalized_query,
                regex=False,
                na=False,
            )
        ]

    result = _apply_categorical_filter(
        result,
        column="position",
        values=request.positions,
    )
    result = _apply_categorical_filter(
        result,
        column="final_role",
        values=request.final_roles,
    )
    result = _apply_categorical_filter(
        result,
        column="archetype",
        values=request.archetypes,
    )
    result = _apply_categorical_filter(
        result,
        column="country_name",
        values=request.countries,
    )

    if request.minimum_age is not None:
        result = result.loc[result["age"] >= request.minimum_age]

    if request.maximum_age is not None:
        result = result.loc[result["age"] <= request.maximum_age]

    if request.minimum_market_value is not None:
        result = result.loc[result["market_value"] >= request.minimum_market_value]

    if request.maximum_market_value is not None:
        result = result.loc[result["market_value"] <= request.maximum_market_value]

    if request.minimum_minutes is not None:
        result = result.loc[result["minutes"] >= request.minimum_minutes]

    if request.minimum_role_confidence is not None:
        result = result.loc[result["role_confidence_pct"] >= request.minimum_role_confidence]

    if request.minimum_data_reliability is not None:
        result = result.loc[result["data_reliability_score"] >= request.minimum_data_reliability]

    return result


def _sort_search_frame(
    dataframe: pd.DataFrame,
    request: PlayerSearchRequest,
) -> pd.DataFrame:
    """Apply deterministic discovery ordering."""

    sort_by = request.sort_by
    sort_direction = request.sort_direction

    if sort_by is None or sort_direction is None:
        raise RuntimeError("Validated player search sorting is unavailable.")

    if sort_by == "relevance":
        if request.query is None:
            raise RuntimeError("Relevance sorting requires a query.")

        normalized_query = _normalize_search_text(
            request.query,
        )

        ranked = dataframe.copy()
        ranked["_match_rank"] = ranked["_normalized_name"].map(
            lambda player_name: _match_rank(
                str(player_name),
                normalized_query,
            )
        )

        return ranked.sort_values(
            by=[
                "_match_rank",
                "_normalized_name",
                "player_id",
            ],
            ascending=[
                True,
                True,
                True,
            ],
            kind="stable",
            na_position="last",
        )

    if sort_by == "player_quality" and sort_direction == "desc" and request.query is None:
        return dataframe.sort_values(
            by=[
                "player_quality_score",
                "data_reliability_score",
                "minutes",
                "_normalized_name",
                "player_id",
            ],
            ascending=[
                False,
                False,
                False,
                True,
                True,
            ],
            kind="stable",
            na_position="last",
        )

    column = _SORT_COLUMNS[sort_by]

    return dataframe.sort_values(
        by=[
            column,
            "_normalized_name",
            "player_id",
        ],
        ascending=[
            sort_direction == "asc",
            True,
            True,
        ],
        kind="stable",
        na_position="last",
    )


def _search_players_in_dataframe(
    *,
    dataframe: pd.DataFrame,
    request: PlayerSearchRequest,
) -> PlayerSearchResult:
    """Discover players in one prepared feature table."""

    search_frame, result_columns = _prepare_search_frame(
        dataframe,
    )

    matches = _filter_search_frame(
        search_frame,
        request,
    ).copy()

    matches = matches.drop_duplicates(
        subset=["player_id"],
        keep="first",
    )

    matches = _sort_search_frame(
        matches,
        request,
    )

    total = len(matches)

    page = matches.iloc[request.offset : request.offset + request.limit]

    records = cast(
        list[dict[str, Any]],
        page[result_columns].to_dict(orient="records"),
    )

    players = tuple(_record_to_item(record) for record in records)

    if request.sort_by is None or request.sort_direction is None:
        raise RuntimeError("Validated player search metadata is unavailable.")

    return PlayerSearchResult(
        query=request.query,
        players=players,
        total=total,
        offset=request.offset,
        limit=request.limit,
        sort_by=request.sort_by,
        sort_direction=request.sort_direction,
    )


def search_players_from_dataframe(
    request: PlayerSearchRequest,
    dataframe: pd.DataFrame,
) -> PlayerSearchResult:
    """Discover players using an already loaded feature table."""

    validated_request = _validate_request(
        request,
    )

    return _search_players_in_dataframe(
        dataframe=dataframe,
        request=validated_request,
    )


def search_players(
    request: PlayerSearchRequest,
) -> PlayerSearchResult:
    """Discover players using the configured feature dataset."""

    validated_request = _validate_request(
        request,
    )

    dataframe = load_player_features(validated_request.features)

    return _search_players_in_dataframe(
        dataframe=dataframe,
        request=validated_request,
    )


_POSITION_LABELS: Final[dict[str, str]] = {
    "G": "Goalkeeper",
    "D": "Defender",
    "M": "Midfielder",
    "F": "Forward",
}

_POSITION_ORDER: Final[dict[str, int]] = {
    "G": 0,
    "D": 1,
    "M": 2,
    "F": 3,
}


def _valid_country_code(
    value: object,
) -> str | None:
    """Return one normalized ISO alpha-3 code when valid."""

    code = _optional_text(
        value,
    )

    if code is None:
        return None

    normalized = code.upper()

    if len(normalized) != 3 or not normalized.isascii() or not normalized.isalpha():
        return None

    return normalized


def _country_codes_by_country(
    dataframe: pd.DataFrame,
    player_tournament_summary: pd.DataFrame | None,
) -> dict[str, str]:
    """Resolve country codes using player identity evidence."""

    player_countries: dict[int, str] = {}
    country_codes: dict[str, str] = {}

    for record in cast(
        list[dict[str, Any]],
        dataframe[
            [
                "player_id",
                "country_name",
            ]
        ].to_dict(orient="records"),
    ):
        country_name = _optional_text(record["country_name"])

        if country_name is None:
            continue

        try:
            player_id = _required_player_id(record["player_id"])
        except InvalidDatasetError:
            continue

        player_countries[player_id] = country_name

        if "country_alpha3" in dataframe.columns:
            code = _valid_country_code(
                dataframe.loc[
                    dataframe["player_id"] == record["player_id"],
                    "country_alpha3",
                ].iloc[0]
            )

            if code is not None:
                country_codes.setdefault(
                    country_name,
                    code,
                )

    if (
        player_tournament_summary is None
        or player_tournament_summary.empty
        or "player_id" not in player_tournament_summary.columns
        or "country_alpha3" not in player_tournament_summary.columns
    ):
        return country_codes

    summary_records = cast(
        list[dict[str, Any]],
        player_tournament_summary[
            [
                "player_id",
                "country_alpha3",
            ]
        ].to_dict(orient="records"),
    )

    for record in summary_records:
        try:
            player_id = _required_player_id(record["player_id"])
        except InvalidDatasetError:
            continue

        country_name = player_countries.get(player_id)
        code = _valid_country_code(record["country_alpha3"])

        if country_name is not None and code is not None:
            country_codes.setdefault(
                country_name,
                code,
            )

    return country_codes


def _build_filter_options(
    dataframe: pd.DataFrame,
    *,
    column: str,
    labels: Mapping[str, str] | None = None,
    country_codes: Mapping[str, str] | None = None,
) -> tuple[PlayerSearchFilterOption, ...]:
    """Build stable categorical options and distinct-player counts."""

    options: list[PlayerSearchFilterOption] = []

    grouped = dataframe.groupby(
        column,
        sort=False,
        dropna=True,
    )

    for value, group in grouped:
        option_value = _optional_text(value)

        if option_value is None:
            continue

        label = (
            labels.get(
                option_value,
                option_value,
            )
            if labels is not None
            else option_value
        )

        code = country_codes.get(option_value) if country_codes is not None else None

        options.append(
            PlayerSearchFilterOption(
                value=option_value,
                label=label,
                count=int(group["player_id"].nunique()),
                country_alpha3=code,
            )
        )

    if column == "position":
        options.sort(
            key=lambda option: (
                _POSITION_ORDER.get(
                    option.value,
                    99,
                ),
                _normalize_search_text(option.label),
            )
        )
    else:
        options.sort(
            key=lambda option: (
                _normalize_search_text(option.label),
                option.value,
            )
        )

    return tuple(options)


def _build_filter_range(
    dataframe: pd.DataFrame,
    *,
    column: str,
) -> PlayerSearchFilterRange:
    """Build an observed finite range for one numeric column."""

    values = pd.to_numeric(
        dataframe[column],
        errors="coerce",
    )

    values = values.loc[np.isfinite(values)]

    if values.empty:
        return PlayerSearchFilterRange(
            minimum=None,
            maximum=None,
        )

    return PlayerSearchFilterRange(
        minimum=float(values.min()),
        maximum=float(values.max()),
    )


def get_player_search_filters_from_dataframe(
    dataframe: pd.DataFrame,
    player_tournament_summary: pd.DataFrame | None = None,
) -> PlayerSearchFiltersResult:
    """Build advanced-filter metadata from preloaded datasets."""

    search_frame, _ = _prepare_search_frame(dataframe)

    search_frame = search_frame.drop_duplicates(
        subset=["player_id"],
        keep="first",
    )

    currencies = sorted(
        {
            currency
            for currency in (
                _optional_text(value) for value in search_frame["market_value_currency"].tolist()
            )
            if currency is not None
        }
    )

    if len(currencies) > 1:
        raise InvalidDatasetError(
            "Player search market-value filtering requires one shared currency."
        )

    country_codes = _country_codes_by_country(
        search_frame,
        player_tournament_summary,
    )

    return PlayerSearchFiltersResult(
        player_count=len(search_frame),
        positions=_build_filter_options(
            search_frame,
            column="position",
            labels=_POSITION_LABELS,
        ),
        final_roles=_build_filter_options(
            search_frame,
            column="final_role",
        ),
        archetypes=_build_filter_options(
            search_frame,
            column="archetype",
        ),
        countries=_build_filter_options(
            search_frame,
            column="country_name",
            country_codes=country_codes,
        ),
        age=_build_filter_range(
            search_frame,
            column="age",
        ),
        market_value=_build_filter_range(
            search_frame,
            column="market_value",
        ),
        minutes=_build_filter_range(
            search_frame,
            column="minutes",
        ),
        role_confidence=_build_filter_range(
            search_frame,
            column="role_confidence_pct",
        ),
        data_reliability=_build_filter_range(
            search_frame,
            column="data_reliability_score",
        ),
        market_value_currency=(currencies[0] if currencies else None),
    )


def get_player_search_filters(
    request: PlayerSearchFiltersRequest,
) -> PlayerSearchFiltersResult:
    """Build advanced-filter metadata from configured datasets."""

    dataframe = load_player_features(request.features)

    player_tournament_summary = (
        load_player_tournament_summary(request.player_tournament_summary)
        if request.player_tournament_summary is not None
        else None
    )

    return get_player_search_filters_from_dataframe(
        dataframe,
        player_tournament_summary,
    )


__all__ = [
    "MAXIMUM_RESULT_LIMIT",
    "MINIMUM_QUERY_LENGTH",
    "MINIMUM_RESULT_LIMIT",
    "PLAYER_SEARCH_COLUMNS",
    "get_player_search_filters",
    "get_player_search_filters_from_dataframe",
    "search_players",
    "search_players_from_dataframe",
]
