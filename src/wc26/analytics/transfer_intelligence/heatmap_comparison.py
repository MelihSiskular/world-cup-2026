"""Measured player heatmap comparison service."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

import numpy as np
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
    HeatmapComparisonRequest,
    HeatmapComparisonResult,
    HeatmapPlayerResult,
    HeatmapSimilarityResult,
)

_REQUIRED_SIMILARITY_COLUMNS = frozenset(
    {
        "target_player_id",
        "candidate_player_id",
        "heatmap_similarity_score_pct",
    }
)


def _optional_float(
    value: object,
) -> float | None:
    """Return one finite float or None for unavailable evidence."""

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


def _optional_int(
    value: object,
) -> int | None:
    """Return one finite integer-valued number or None."""

    result = _optional_float(value)

    if result is None:
        return None

    if not result.is_integer():
        return None

    return int(result)


def _player_name(
    player: pd.Series[Any],
) -> str:
    """Return a valid player display name from the player catalog."""

    value = player.get("player_name")

    if value is None or pd.isna(value):
        raise InvalidDatasetError("Player catalog contains a missing player_name.")

    result = str(value).strip()

    if not result:
        raise InvalidDatasetError("Player catalog contains an empty player_name.")

    return result


def _resolve_heatmap_profile(
    heatmap_profiles: pd.DataFrame,
    *,
    player_id: int,
) -> pd.Series[Any] | None:
    """Resolve at most one heatmap profile for a player."""

    if heatmap_profiles.empty or "player_id" not in heatmap_profiles.columns:
        return None

    player_ids = pd.to_numeric(
        heatmap_profiles["player_id"],
        errors="coerce",
    )

    matches = heatmap_profiles.loc[player_ids.eq(player_id)]

    if matches.empty:
        return None

    if len(matches) != 1:
        raise InvalidDatasetError(f"Multiple heatmap profiles matched player ID: {player_id}")

    return matches.iloc[0]


def _serialize_grid(
    grid: np.ndarray,
) -> tuple[tuple[float, ...], ...]:
    """Detach one NumPy grid into an immutable result value."""

    return tuple(tuple(float(value) for value in row) for row in grid)


def _build_player_result(
    *,
    player: pd.Series[Any],
    heatmap_profiles: pd.DataFrame,
    heatmap_grids: Mapping[int, np.ndarray],
    player_id: int,
) -> HeatmapPlayerResult:
    """Build one player-side heatmap result."""

    grid = heatmap_grids.get(player_id)

    if grid is not None and not isinstance(
        grid,
        np.ndarray,
    ):
        raise InvalidDatasetError(
            f"Heatmap grid catalog contains a non-array value for player ID: {player_id}"
        )

    profile = _resolve_heatmap_profile(
        heatmap_profiles,
        player_id=player_id,
    )

    if grid is None:
        grid_width = None
        grid_height = None
        serialized_grid = None
    else:
        if grid.ndim != 2:
            raise InvalidDatasetError(
                f"Heatmap grid must be two-dimensional for player ID: {player_id}"
            )

        grid_height = int(grid.shape[0])
        grid_width = int(grid.shape[1])
        serialized_grid = _serialize_grid(grid)

    def profile_value(
        column: str,
    ) -> object:
        if profile is None:
            return None

        return profile.get(column)

    return HeatmapPlayerResult(
        player_id=player_id,
        player_name=_player_name(player),
        available=(grid is not None),
        grid_width=grid_width,
        grid_height=grid_height,
        grid=serialized_grid,
        matches_with_heatmap=_optional_int(profile_value("matches_with_heatmap")),
        heatmap_point_count=_optional_int(profile_value("heatmap_point_count")),
        weighted_mean_x=_optional_float(profile_value("weighted_mean_x")),
        weighted_mean_y=_optional_float(profile_value("weighted_mean_y")),
        peak_cell_x=_optional_float(profile_value("peak_cell_x")),
        peak_cell_y=_optional_float(profile_value("peak_cell_y")),
        heatmap_entropy=_optional_float(profile_value("heatmap_entropy")),
    )


def _unavailable_similarity() -> HeatmapSimilarityResult:
    """Return the explicit no-measured-evidence state."""

    return HeatmapSimilarityResult(
        available=False,
        heatmap_similarity_score_pct=None,
        heatmap_cosine_similarity_pct=None,
        occupation_overlap_pct=None,
        peak_zone_similarity_pct=None,
        peak_zone_distance=None,
        entropy_similarity_pct=None,
        target_matches_with_heatmap=None,
        candidate_matches_with_heatmap=None,
        target_heatmap_points=None,
        candidate_heatmap_points=None,
    )


def _resolve_measured_similarity(
    heatmap_similarity: pd.DataFrame,
    *,
    target_player_id: int,
    candidate_player_id: int,
) -> HeatmapSimilarityResult:
    """Resolve measured pair evidence in target-to-candidate orientation."""

    if heatmap_similarity.empty:
        return _unavailable_similarity()

    missing_columns = _REQUIRED_SIMILARITY_COLUMNS.difference(heatmap_similarity.columns)

    if missing_columns:
        raise InvalidDatasetError(
            "Heatmap similarity catalog is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    target_ids = pd.to_numeric(
        heatmap_similarity["target_player_id"],
        errors="coerce",
    )
    candidate_ids = pd.to_numeric(
        heatmap_similarity["candidate_player_id"],
        errors="coerce",
    )

    direct = heatmap_similarity.loc[
        target_ids.eq(target_player_id) & candidate_ids.eq(candidate_player_id)
    ].copy()

    reverse = heatmap_similarity.loc[
        target_ids.eq(candidate_player_id) & candidate_ids.eq(target_player_id)
    ].copy()

    if not reverse.empty:
        reverse = reverse.rename(
            columns={
                "candidate_matches_with_heatmap": ("target_matches_with_heatmap"),
                "target_matches_with_heatmap": ("candidate_matches_with_heatmap"),
                "candidate_heatmap_points": ("target_heatmap_points"),
                "target_heatmap_points": ("candidate_heatmap_points"),
            }
        )

    pairwise = pd.concat(
        [
            direct,
            reverse,
        ],
        ignore_index=True,
    )

    if pairwise.empty:
        return _unavailable_similarity()

    pairwise["heatmap_similarity_score_pct"] = pd.to_numeric(
        pairwise["heatmap_similarity_score_pct"],
        errors="coerce",
    )

    pairwise = pairwise.dropna(subset=["heatmap_similarity_score_pct"])

    if pairwise.empty:
        return _unavailable_similarity()

    row = pairwise.sort_values(
        "heatmap_similarity_score_pct",
        ascending=False,
    ).iloc[0]

    score = _optional_float(row.get("heatmap_similarity_score_pct"))

    if score is None:
        return _unavailable_similarity()

    return HeatmapSimilarityResult(
        available=True,
        heatmap_similarity_score_pct=score,
        heatmap_cosine_similarity_pct=(_optional_float(row.get("heatmap_cosine_similarity_pct"))),
        occupation_overlap_pct=_optional_float(row.get("occupation_overlap_pct")),
        peak_zone_similarity_pct=_optional_float(row.get("peak_zone_similarity_pct")),
        peak_zone_distance=_optional_float(row.get("peak_zone_distance")),
        entropy_similarity_pct=_optional_float(row.get("entropy_similarity_pct")),
        target_matches_with_heatmap=_optional_int(row.get("target_matches_with_heatmap")),
        candidate_matches_with_heatmap=_optional_int(row.get("candidate_matches_with_heatmap")),
        target_heatmap_points=_optional_int(row.get("target_heatmap_points")),
        candidate_heatmap_points=_optional_int(row.get("candidate_heatmap_points")),
    )


def get_heatmap_comparison_from_catalog(
    request: HeatmapComparisonRequest,
    catalog: TransferDataCatalog,
) -> HeatmapComparisonResult:
    """Compare two players using measured tournament heatmap evidence."""

    if request.target_player_id <= 0 or request.candidate_player_id <= 0:
        raise InvalidTransferAnalysisRequestError(
            "Heatmap comparison player IDs must be positive integers."
        )

    if request.target_player_id == request.candidate_player_id:
        raise InvalidTransferAnalysisRequestError(
            "Heatmap comparison requires two different players."
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
        heatmap_profiles=catalog.heatmap_profiles,
        heatmap_grids=catalog.heatmap_grids,
        player_id=request.target_player_id,
    )
    candidate_result = _build_player_result(
        player=candidate,
        heatmap_profiles=catalog.heatmap_profiles,
        heatmap_grids=catalog.heatmap_grids,
        player_id=request.candidate_player_id,
    )

    similarity = _resolve_measured_similarity(
        catalog.heatmap_similarity,
        target_player_id=(request.target_player_id),
        candidate_player_id=(request.candidate_player_id),
    )

    return HeatmapComparisonResult(
        target=target_result,
        candidate=candidate_result,
        similarity=similarity,
    )


__all__ = [
    "get_heatmap_comparison_from_catalog",
]
