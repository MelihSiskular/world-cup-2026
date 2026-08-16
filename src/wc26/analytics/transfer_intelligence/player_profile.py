"""Application service for retrieving one player profile."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import replace
from typing import Any, Final, cast

import numpy as np
import pandas as pd

from wc26.analytics.player_intelligence.profile import (
    PlayerIntelligenceProfile,
    build_player_intelligence_profile,
)
from wc26.analytics.transfer_intelligence.datasets import (
    load_player_features,
    load_player_tournament_summary,
)
from wc26.analytics.transfer_intelligence.errors import (
    InvalidDatasetError,
    InvalidPlayerProfileError,
    PlayerNotFoundError,
)
from wc26.analytics.transfer_intelligence.models import (
    PlayerInsightResult,
    PlayerIntelligenceResult,
    PlayerPerformanceMetricGroupResult,
    PlayerPerformanceMetricResult,
    PlayerProfileRequest,
    PlayerProfileResult,
    PlayerSampleContextResult,
    PlayerTournamentSummaryResult,
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


def _prepare_feature_table(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Validate and select player-profile columns."""

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


def _convert_player_intelligence(
    profile: PlayerIntelligenceProfile,
) -> tuple[
    PlayerTournamentSummaryResult,
    PlayerIntelligenceResult,
]:
    """Convert internal analytics into the stable profile result contract."""

    tournament = PlayerTournamentSummaryResult(
        matches=profile.tournament.matches,
        starts=profile.tournament.starts,
        substitute_appearances=(profile.tournament.substitute_appearances),
        captain_appearances=(profile.tournament.captain_appearances),
        minutes=profile.tournament.minutes,
        formations_used=profile.tournament.formations_used,
        primary_formation=profile.tournament.primary_formation,
        primary_lineup_position=(profile.tournament.primary_lineup_position),
    )

    groups = tuple(
        PlayerPerformanceMetricGroupResult(
            key=group.key.value,
            metrics=tuple(
                PlayerPerformanceMetricResult(
                    key=metric.key,
                    label=metric.label,
                    short_label=metric.short_label,
                    unit=metric.unit.value,
                    value=metric.value,
                    performance_percentile=(metric.performance_percentile),
                    peer_count=metric.peer_count,
                )
                for metric in group.metrics
            ),
        )
        for group in profile.groups
    )

    def convert_insight(
        insight: object,
    ) -> PlayerInsightResult:
        from wc26.analytics.player_intelligence.insights import (
            PlayerInsight,
        )

        if not isinstance(insight, PlayerInsight):
            raise TypeError("Unexpected player intelligence insight.")

        return PlayerInsightResult(
            kind=insight.kind.value,
            group=insight.group.value,
            group_label=insight.group_label,
            metric_key=insight.metric_key,
            metric_label=insight.metric_label,
            metric_short_label=insight.metric_short_label,
            value=insight.value,
            percentile=insight.percentile,
            peer_count=insight.peer_count,
            evidence=insight.evidence,
        )

    intelligence = PlayerIntelligenceResult(
        position_group=profile.position_group.value,
        sample=PlayerSampleContextResult(
            target_minutes=profile.sample.target_minutes,
            minimum_peer_minutes=(profile.sample.minimum_peer_minutes),
            target_meets_peer_minimum=(profile.sample.target_meets_peer_minimum),
        ),
        groups=groups,
        strengths=tuple(convert_insight(insight) for insight in profile.strengths),
        watch_outs=tuple(convert_insight(insight) for insight in profile.watch_outs),
    )

    return tournament, intelligence


def _enrich_player_profile(
    profile: PlayerProfileResult,
    tournament_dataframe: pd.DataFrame | None,
) -> PlayerProfileResult:
    """Attach tournament intelligence when an enriched table is available."""

    if tournament_dataframe is None or tournament_dataframe.empty:
        return profile

    try:
        intelligence_profile = build_player_intelligence_profile(
            tournament_dataframe,
            player_id=profile.player_id,
        )
    except ValueError as exc:
        raise InvalidDatasetError(f"Player intelligence dataset is invalid: {exc}") from exc

    tournament, intelligence = _convert_player_intelligence(intelligence_profile)

    return replace(
        profile,
        tournament=tournament,
        intelligence=intelligence,
    )


def _get_player_profile_from_validated_request(
    request: PlayerProfileRequest,
    dataframe: pd.DataFrame,
    player_tournament_summary: pd.DataFrame | None = None,
) -> PlayerProfileResult:
    """Return one profile from an already loaded table."""

    prepared_dataframe = _prepare_feature_table(dataframe)
    prepared_dataframe = _validate_player_ids(prepared_dataframe)

    matches = prepared_dataframe.loc[
        prepared_dataframe["_normalized_player_id"].eq(request.player_id)
    ]

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

    profile = _record_to_profile(record)

    return _enrich_player_profile(
        profile,
        player_tournament_summary,
    )


def get_player_profile_from_dataframe(
    request: PlayerProfileRequest,
    dataframe: pd.DataFrame,
    player_tournament_summary: pd.DataFrame | None = None,
) -> PlayerProfileResult:
    """Return one profile using an already loaded feature table."""

    _validate_request(request)

    return _get_player_profile_from_validated_request(
        request,
        dataframe,
        player_tournament_summary,
    )


def get_player_profile(
    request: PlayerProfileRequest,
) -> PlayerProfileResult:
    """Return one profile using the configured feature dataset."""

    _validate_request(request)

    dataframe = load_player_features(request.features)

    player_tournament_summary = (
        load_player_tournament_summary(request.player_tournament_summary)
        if request.player_tournament_summary is not None
        else None
    )

    return _get_player_profile_from_validated_request(
        request,
        dataframe,
        player_tournament_summary,
    )


__all__ = [
    "PLAYER_PROFILE_COLUMNS",
    "get_player_profile",
    "get_player_profile_from_dataframe",
]
