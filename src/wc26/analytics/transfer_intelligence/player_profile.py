"""Application service for retrieving one player profile."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any, Final, cast

import numpy as np
import pandas as pd

from wc26.analytics.transfer_intelligence.errors import (
    DatasetNotFoundError,
    InvalidDatasetError,
    InvalidPlayerProfileError,
    PlayerNotFoundError,
)
from wc26.analytics.transfer_intelligence.models import (
    PlayerProfileRequest,
    PlayerProfileResult,
)

PLAYER_PROFILE_COLUMNS: Final[tuple[str, ...]] = (
    "player_id",
    "player_name",
    "national_team_name",
    "country_name",
    "position",
    "age",
    "height_cm",
    "appearances",
    "starts",
    "minutes",
    "weighted_rating",
    "market_value",
    "market_value_currency",
    "archetype",
    "spatial_role",
    "final_role",
    "lateral_profile",
    "vertical_profile",
    "mobility_profile",
    "role_confidence_pct",
    "spatial_reliability",
    "data_reliability_score",
    "player_quality_score",
    "role_reason",
)


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
    """Convert a scalar dataset value into optional text."""

    if _is_missing_value(value):
        return None

    text = str(value).strip()

    return text or None


def _required_text(
    value: object,
    *,
    field_name: str,
) -> str:
    """Convert a required dataset value into text."""

    result = _optional_text(value)

    if result is None:
        raise InvalidDatasetError(f"Player profile dataset contains an invalid {field_name}.")

    return result


def _optional_float(
    value: object,
) -> float | None:
    """Convert a scalar dataset value into an optional finite float."""

    if _is_missing_value(value):
        return None

    try:
        result = float(str(value).strip())
    except ValueError:
        return None

    if not math.isfinite(result):
        return None

    return result


def _optional_int(
    value: object,
) -> int | None:
    """Convert a scalar dataset value into an optional integer."""

    numeric_value = _optional_float(value)

    if numeric_value is None:
        return None

    if not numeric_value.is_integer():
        return None

    return int(numeric_value)


def _validate_request(
    request: PlayerProfileRequest,
) -> None:
    """Validate the player-profile request."""

    if request.player_id <= 0:
        raise InvalidPlayerProfileError("Player ID must be a positive integer.")


def _read_feature_table(
    request: PlayerProfileRequest,
) -> pd.DataFrame:
    """Read and validate the player feature table."""

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

    missing_columns = set(PLAYER_PROFILE_COLUMNS).difference(dataframe.columns)

    if missing_columns:
        raise InvalidDatasetError(
            "Missing player profile columns: " + ", ".join(sorted(missing_columns))
        )

    return dataframe[list(PLAYER_PROFILE_COLUMNS)].copy()


def _validate_player_ids(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Validate and normalize player identifiers."""

    player_ids = pd.to_numeric(
        dataframe["player_id"],
        errors="coerce",
    )

    if player_ids.isna().any():
        raise InvalidDatasetError("Player profile dataset contains an invalid player_id.")

    player_id_values = player_ids.astype(float)

    if not np.isfinite(player_id_values.to_numpy()).all():
        raise InvalidDatasetError("Player profile dataset contains an invalid player_id.")

    if not player_id_values.mod(1).eq(0).all():
        raise InvalidDatasetError("Player profile dataset contains an invalid player_id.")

    result = dataframe.copy()

    result["_normalized_player_id"] = player_id_values.astype("int64")

    if result["_normalized_player_id"].duplicated().any():
        raise InvalidDatasetError("Player profile dataset contains duplicate player IDs.")

    return result


def _record_to_profile(
    record: Mapping[str, object],
) -> PlayerProfileResult:
    """Convert one dataset row into the public profile contract."""

    player_id = _optional_int(record["player_id"])

    if player_id is None:
        raise InvalidDatasetError("Player profile dataset contains an invalid player_id.")

    return PlayerProfileResult(
        player_id=player_id,
        player_name=_required_text(
            record["player_name"],
            field_name="player_name",
        ),
        national_team_name=_optional_text(record["national_team_name"]),
        country_name=_optional_text(record["country_name"]),
        position=_optional_text(record["position"]),
        age=_optional_float(record["age"]),
        height_cm=_optional_float(record["height_cm"]),
        appearances=_optional_int(record["appearances"]),
        starts=_optional_int(record["starts"]),
        minutes=_optional_float(record["minutes"]),
        weighted_rating=_optional_float(record["weighted_rating"]),
        market_value=_optional_float(record["market_value"]),
        market_value_currency=_optional_text(record["market_value_currency"]),
        archetype=_optional_text(record["archetype"]),
        spatial_role=_optional_text(record["spatial_role"]),
        final_role=_optional_text(record["final_role"]),
        lateral_profile=_optional_text(record["lateral_profile"]),
        vertical_profile=_optional_text(record["vertical_profile"]),
        mobility_profile=_optional_text(record["mobility_profile"]),
        role_confidence_pct=_optional_float(record["role_confidence_pct"]),
        spatial_reliability=_optional_float(record["spatial_reliability"]),
        data_reliability_score=_optional_float(record["data_reliability_score"]),
        player_quality_score=_optional_float(record["player_quality_score"]),
        role_reason=_optional_text(record["role_reason"]),
    )


def get_player_profile(
    request: PlayerProfileRequest,
) -> PlayerProfileResult:
    """Return the profile for one stable player identifier."""

    _validate_request(request)

    dataframe = _read_feature_table(request)
    dataframe = _validate_player_ids(dataframe)

    matches = dataframe.loc[dataframe["_normalized_player_id"].eq(request.player_id)]

    if matches.empty:
        raise PlayerNotFoundError(f"Player not found for ID: {request.player_id}")

    if len(matches) != 1:
        raise InvalidDatasetError(
            "Player profile dataset returned multiple rows for one player ID."
        )

    record = cast(
        dict[str, Any],
        matches.iloc[0][list(PLAYER_PROFILE_COLUMNS)].to_dict(),
    )

    return _record_to_profile(record)


__all__ = [
    "PLAYER_PROFILE_COLUMNS",
    "get_player_profile",
]
