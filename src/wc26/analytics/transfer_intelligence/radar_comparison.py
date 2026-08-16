"""Position-aware playing-style radar comparison."""

from __future__ import annotations

import math
from typing import Any, Final

import pandas as pd

from wc26.analytics.transfer_intelligence.catalog import (
    TransferDataCatalog,
)
from wc26.analytics.transfer_intelligence.errors import (
    InvalidDatasetError,
    InvalidTransferAnalysisRequestError,
)
from wc26.analytics.transfer_intelligence.matching import (
    resolve_player_by_id,
)
from wc26.analytics.transfer_intelligence.models import (
    RadarComparisonMetadataResult,
    RadarComparisonRequest,
    RadarComparisonResult,
    RadarDimensionResult,
    RadarPlayerResult,
)

POSITION_RADAR_DIMENSIONS: Final[
    dict[
        str,
        tuple[
            tuple[str, str, str],
            ...,
        ],
    ]
] = {
    "G": (
        (
            "shot_stopping",
            "Shot Stopping",
            "archetype_score_shot_stopping",
        ),
        (
            "box_command",
            "Box Command",
            "archetype_score_box_command",
        ),
        (
            "short_distribution",
            "Short Distribution",
            "archetype_score_short_distribution",
        ),
        (
            "long_distribution",
            "Long Distribution",
            "archetype_score_long_distribution",
        ),
        (
            "sweeping",
            "Sweeping",
            "archetype_score_sweeping",
        ),
        (
            "security",
            "Security",
            "archetype_score_security",
        ),
    ),
    "D": (
        (
            "defending",
            "Defending",
            "archetype_score_defending",
        ),
        (
            "duels",
            "Duels",
            "archetype_score_duels",
        ),
        (
            "aerial",
            "Aerial",
            "archetype_score_aerial",
        ),
        (
            "passing",
            "Passing",
            "archetype_score_passing",
        ),
        (
            "progression",
            "Progression",
            "archetype_score_progression",
        ),
        (
            "security",
            "Security",
            "archetype_score_security",
        ),
        (
            "wide_attack",
            "Wide Attack",
            "archetype_score_wide_attack",
        ),
    ),
    "M": (
        (
            "creativity",
            "Creativity",
            "archetype_score_creativity",
        ),
        (
            "progression",
            "Progression",
            "archetype_score_progression",
        ),
        (
            "passing_volume",
            "Passing Volume",
            "archetype_score_passing_volume",
        ),
        (
            "ball_security",
            "Ball Security",
            "archetype_score_ball_security",
        ),
        (
            "dribbling",
            "Dribbling",
            "archetype_score_dribbling",
        ),
        (
            "scoring_threat",
            "Scoring Threat",
            "archetype_score_scoring_threat",
        ),
        (
            "defensive_work",
            "Defensive Work",
            "archetype_score_defensive_work",
        ),
        (
            "wide_creation",
            "Wide Creation",
            "archetype_score_wide_creation",
        ),
    ),
    "F": (
        (
            "finishing",
            "Finishing",
            "archetype_score_finishing",
        ),
        (
            "shooting_volume",
            "Shooting Volume",
            "archetype_score_shooting_volume",
        ),
        (
            "creativity",
            "Creativity",
            "archetype_score_creativity",
        ),
        (
            "dribbling",
            "Dribbling",
            "archetype_score_dribbling",
        ),
        (
            "link_play",
            "Link Play",
            "archetype_score_link_play",
        ),
        (
            "aerial_presence",
            "Aerial Presence",
            "archetype_score_aerial_presence",
        ),
        (
            "off_ball_threat",
            "Off-ball Threat",
            "archetype_score_off_ball_threat",
        ),
        (
            "ball_security",
            "Ball Security",
            "archetype_score_ball_security",
        ),
    ),
}


_MINIMUM_AVAILABLE_DIMENSIONS: Final[int] = 3


def _optional_float(
    value: object,
) -> float | None:
    """Return one finite analytical value or None."""

    if value is None or value is pd.NA or value is pd.NaT:
        return None

    try:
        result = float(str(value).strip())
    except (
        TypeError,
        ValueError,
    ):
        return None

    if not math.isfinite(result):
        return None

    return result


def _player_name(
    player: pd.Series[Any],
) -> str:
    """Return a valid player display name."""

    value = player.get("player_name")

    if value is None or pd.isna(value):
        raise InvalidDatasetError("Player catalog contains a missing player_name.")

    result = str(value).strip()

    if not result:
        raise InvalidDatasetError("Player catalog contains an empty player_name.")

    return result


def _normalize_position_value(
    value: object,
) -> str | None:
    """Normalize one player position code."""

    if value is None or value is pd.NA or value is pd.NaT:
        return None

    text = str(value).strip().upper()

    if not text:
        return None

    return text


def _normalized_positions(
    players: pd.DataFrame,
) -> pd.Series:
    """Return normalized catalog position codes."""

    if "position" not in players.columns:
        return pd.Series(
            pd.NA,
            index=players.index,
            dtype="string",
        )

    return players["position"].astype("string").str.strip().str.upper()


def _dimension_population(
    players: pd.DataFrame,
    *,
    position: str,
    column: str,
) -> pd.Series:
    """Return finite same-position values for one radar dimension."""

    if column not in players.columns:
        return pd.Series(dtype="float64")

    positions = _normalized_positions(players)

    values = pd.to_numeric(
        players.loc[
            positions.eq(position),
            column,
        ],
        errors="coerce",
    )

    values = values.replace(
        [
            float("inf"),
            float("-inf"),
        ],
        float("nan"),
    )

    return values.dropna()


def _percentile_rank(
    value: float | None,
    population: pd.Series,
) -> float | None:
    """Return empirical percentile within one position population."""

    if value is None or population.empty:
        return None

    percentile = float(population.le(value).mean() * 100.0)

    return max(
        0.0,
        min(
            100.0,
            percentile,
        ),
    )


def _build_player_result(
    *,
    player: pd.Series[Any],
    players: pd.DataFrame,
    player_id: int,
) -> RadarPlayerResult:
    """Build one position-relative radar profile."""

    position = _normalize_position_value(player.get("position"))

    if position is None or position not in POSITION_RADAR_DIMENSIONS:
        return RadarPlayerResult(
            player_id=player_id,
            player_name=_player_name(player),
            position=position,
            available=False,
            peer_count=0,
            dimensions=(),
        )

    normalized_positions = _normalized_positions(players)

    position_population = players.loc[normalized_positions.eq(position)]

    peer_count = int(len(position_population))

    dimensions: list[RadarDimensionResult] = []

    for (
        key,
        label,
        column,
    ) in POSITION_RADAR_DIMENSIONS[position]:
        raw_score = _optional_float(player.get(column))

        population = _dimension_population(
            players,
            position=position,
            column=column,
        )

        dimensions.append(
            RadarDimensionResult(
                key=key,
                label=label,
                raw_score=raw_score,
                percentile=_percentile_rank(
                    raw_score,
                    population,
                ),
                peer_count=int(len(population)),
            )
        )

    available_dimension_count = sum(dimension.percentile is not None for dimension in dimensions)

    return RadarPlayerResult(
        player_id=player_id,
        player_name=_player_name(player),
        position=position,
        available=(available_dimension_count >= _MINIMUM_AVAILABLE_DIMENSIONS),
        peer_count=peer_count,
        dimensions=tuple(dimensions),
    )


def _comparison_metadata(
    target: RadarPlayerResult,
    candidate: RadarPlayerResult,
) -> RadarComparisonMetadataResult:
    """Resolve whether both profiles can share one overlay radar."""

    same_position = target.position is not None and target.position == candidate.position

    if not target.available and not candidate.available:
        return RadarComparisonMetadataResult(
            same_position=same_position,
            overlay_available=False,
            reason="profiles_unavailable",
        )

    if not target.available:
        return RadarComparisonMetadataResult(
            same_position=same_position,
            overlay_available=False,
            reason="target_profile_unavailable",
        )

    if not candidate.available:
        return RadarComparisonMetadataResult(
            same_position=same_position,
            overlay_available=False,
            reason="candidate_profile_unavailable",
        )

    if not same_position:
        return RadarComparisonMetadataResult(
            same_position=False,
            overlay_available=False,
            reason="different_position_profiles",
        )

    target_keys = tuple(dimension.key for dimension in target.dimensions)
    candidate_keys = tuple(dimension.key for dimension in candidate.dimensions)

    if target_keys != candidate_keys:
        return RadarComparisonMetadataResult(
            same_position=True,
            overlay_available=False,
            reason="dimension_contract_mismatch",
        )

    return RadarComparisonMetadataResult(
        same_position=True,
        overlay_available=True,
        reason=None,
    )


def get_radar_comparison_from_catalog(
    request: RadarComparisonRequest,
    catalog: TransferDataCatalog,
) -> RadarComparisonResult:
    """Compare two position-relative playing-style radar profiles."""

    if request.target_player_id <= 0 or request.candidate_player_id <= 0:
        raise InvalidTransferAnalysisRequestError(
            "Radar comparison player IDs must be positive integers."
        )

    if request.target_player_id == request.candidate_player_id:
        raise InvalidTransferAnalysisRequestError(
            "Radar comparison requires two different players."
        )

    target = resolve_player_by_id(
        catalog.players,
        request.target_player_id,
    )
    candidate = resolve_player_by_id(
        catalog.players,
        request.candidate_player_id,
    )

    target_result = _build_player_result(
        player=target,
        players=catalog.players,
        player_id=request.target_player_id,
    )

    candidate_result = _build_player_result(
        player=candidate,
        players=catalog.players,
        player_id=request.candidate_player_id,
    )

    comparison = _comparison_metadata(
        target_result,
        candidate_result,
    )

    return RadarComparisonResult(
        target=target_result,
        candidate=candidate_result,
        comparison=comparison,
    )


__all__ = [
    "POSITION_RADAR_DIMENSIONS",
    "get_radar_comparison_from_catalog",
]
