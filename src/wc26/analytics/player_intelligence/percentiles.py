"""Same-position percentile calculations for player intelligence."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

import numpy as np
import pandas as pd

from wc26.analytics.player_intelligence.metric_registry import (
    MetricDefinition,
    PositionGroup,
    metrics_for_position_group,
)
from wc26.analytics.player_intelligence.positions import (
    normalize_position_group,
)

DEFAULT_MINIMUM_COHORT_MINUTES: Final[float] = 180.0
DEFAULT_MINIMUM_PEER_COUNT: Final[int] = 10

PLAYER_ID_COLUMN: Final[str] = "player_id"
POSITION_COLUMN: Final[str] = "player_primary_position"
MINUTES_COLUMN: Final[str] = "total_minutes"


@dataclass(frozen=True, slots=True)
class MetricPercentileResult:
    """One player metric interpreted against a same-position peer cohort."""

    metric_key: str
    value: float
    percentile: float
    peer_count: int


@dataclass(frozen=True, slots=True)
class PlayerPercentileProfile:
    """Position-aware percentile profile for one player."""

    player_id: int
    position_group: PositionGroup
    minimum_cohort_minutes: float
    metrics: tuple[MetricPercentileResult, ...]


def _finite_float(
    value: object,
) -> float | None:
    """Convert one scalar to a finite float when possible."""

    if value is None or value is pd.NA or value is pd.NaT:
        return None

    try:
        result = float(str(value).strip())
    except ValueError:
        return None

    if not math.isfinite(result):
        return None

    return result


def _validate_required_columns(
    dataframe: pd.DataFrame,
) -> None:
    """Validate columns required by the percentile engine."""

    required_columns = {
        PLAYER_ID_COLUMN,
        POSITION_COLUMN,
        MINUTES_COLUMN,
    }

    missing_columns = required_columns.difference(dataframe.columns)

    if missing_columns:
        raise ValueError(
            "Missing percentile dataset columns: " + ", ".join(sorted(missing_columns))
        )


def _target_row(
    dataframe: pd.DataFrame,
    *,
    player_id: int,
) -> pd.Series:
    """Return exactly one target-player row."""

    numeric_ids = pd.to_numeric(
        dataframe[PLAYER_ID_COLUMN],
        errors="coerce",
    )

    matches = dataframe.loc[numeric_ids.eq(player_id)]

    if matches.empty:
        raise ValueError(f"Player not found for percentile profile: {player_id}")

    if len(matches) != 1:
        raise ValueError(f"Percentile dataset returned multiple rows for player ID: {player_id}")

    return matches.iloc[0]


def _eligible_position_cohort(
    dataframe: pd.DataFrame,
    *,
    position_group: PositionGroup,
    minimum_minutes: float,
) -> pd.DataFrame:
    """Return reliable same-position peers for percentile comparison."""

    normalized_positions = dataframe[POSITION_COLUMN].map(normalize_position_group)

    minutes = pd.to_numeric(
        dataframe[MINUTES_COLUMN],
        errors="coerce",
    )

    return dataframe.loc[normalized_positions.eq(position_group) & minutes.ge(minimum_minutes)]


def _distribution_percentile(
    *,
    player_value: float,
    peer_values: pd.Series,
    higher_is_better: bool,
) -> tuple[float, int] | None:
    """Return performance percentile and usable peer count.

    Percentiles use the midpoint of ties. This keeps an entirely tied
    distribution at the 50th percentile while still allowing values above
    or below the observed peer distribution to reach 100 or 0.
    """

    numeric_values = pd.to_numeric(
        peer_values,
        errors="coerce",
    )

    values = numeric_values.to_numpy(
        dtype=float,
        na_value=np.nan,
    )

    values = values[np.isfinite(values)]

    peer_count = len(values)

    if peer_count == 0:
        return None

    less_count = int(np.count_nonzero(values < player_value))

    equal_count = int(np.count_nonzero(values == player_value))

    distribution_percentile = (less_count + 0.5 * equal_count) / peer_count * 100.0

    performance_percentile = (
        distribution_percentile if higher_is_better else 100.0 - distribution_percentile
    )

    performance_percentile = min(
        100.0,
        max(
            0.0,
            performance_percentile,
        ),
    )

    return (
        round(
            performance_percentile,
            1,
        ),
        peer_count,
    )


def _metric_percentile(
    *,
    target: pd.Series,
    cohort: pd.DataFrame,
    metric: MetricDefinition,
    minimum_peer_count: int,
) -> MetricPercentileResult | None:
    """Calculate one metric percentile when evidence is sufficient."""

    if metric.source_column not in target.index:
        return None

    if metric.source_column not in cohort.columns:
        return None

    player_value = _finite_float(target[metric.source_column])

    if player_value is None:
        return None

    result = _distribution_percentile(
        player_value=player_value,
        peer_values=cohort[metric.source_column],
        higher_is_better=metric.higher_is_better,
    )

    if result is None:
        return None

    percentile, peer_count = result

    if peer_count < minimum_peer_count:
        return None

    return MetricPercentileResult(
        metric_key=metric.key,
        value=player_value,
        percentile=percentile,
        peer_count=peer_count,
    )


def calculate_player_percentiles(
    dataframe: pd.DataFrame,
    *,
    player_id: int,
    minimum_cohort_minutes: float = (DEFAULT_MINIMUM_COHORT_MINUTES),
    minimum_peer_count: int = (DEFAULT_MINIMUM_PEER_COUNT),
) -> PlayerPercentileProfile:
    """Build a position-aware performance percentile profile."""

    if player_id <= 0:
        raise ValueError("Player ID must be positive.")

    if minimum_cohort_minutes < 0:
        raise ValueError("Minimum cohort minutes cannot be negative.")

    if minimum_peer_count <= 0:
        raise ValueError("Minimum peer count must be positive.")

    _validate_required_columns(dataframe)

    target = _target_row(
        dataframe,
        player_id=player_id,
    )

    position_group = normalize_position_group(target[POSITION_COLUMN])

    if position_group is None:
        raise ValueError(f"Player position cannot be normalized for player ID: {player_id}")

    cohort = _eligible_position_cohort(
        dataframe,
        position_group=position_group,
        minimum_minutes=minimum_cohort_minutes,
    )

    results: list[MetricPercentileResult] = []

    for metric in metrics_for_position_group(position_group):
        metric_result = _metric_percentile(
            target=target,
            cohort=cohort,
            metric=metric,
            minimum_peer_count=minimum_peer_count,
        )

        if metric_result is not None:
            results.append(metric_result)

    return PlayerPercentileProfile(
        player_id=player_id,
        position_group=position_group,
        minimum_cohort_minutes=minimum_cohort_minutes,
        metrics=tuple(results),
    )


__all__ = [
    "DEFAULT_MINIMUM_COHORT_MINUTES",
    "DEFAULT_MINIMUM_PEER_COUNT",
    "MetricPercentileResult",
    "PlayerPercentileProfile",
    "calculate_player_percentiles",
]
