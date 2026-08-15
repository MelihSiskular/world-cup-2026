"""Tests for heatmap comparison domain contracts."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import numpy as np
import pandas as pd
import pytest

from wc26.analytics.transfer_intelligence.catalog import (
    TransferDataCatalog,
)
from wc26.analytics.transfer_intelligence.errors import (
    InvalidTransferAnalysisRequestError,
    PlayerNotFoundError,
)
from wc26.analytics.transfer_intelligence.heatmap_comparison import (
    get_heatmap_comparison_from_catalog,
)
from wc26.analytics.transfer_intelligence.models import (
    HeatmapComparisonRequest,
    HeatmapComparisonResult,
    HeatmapPlayerResult,
    HeatmapSimilarityResult,
)


def test_heatmap_comparison_request_is_immutable() -> None:
    request = HeatmapComparisonRequest(
        target_player_id=978838,
        candidate_player_id=789071,
    )

    with pytest.raises(FrozenInstanceError):
        request.target_player_id = 1


def test_heatmap_comparison_result_serializes_nested_grid() -> None:
    target = HeatmapPlayerResult(
        player_id=978838,
        player_name="Michael Olise",
        available=True,
        grid_width=2,
        grid_height=2,
        grid=(
            (0.1, 0.2),
            (0.3, 0.4),
        ),
        matches_with_heatmap=7,
        heatmap_point_count=300,
        weighted_mean_x=58.0,
        weighted_mean_y=42.0,
        peak_cell_x=60.0,
        peak_cell_y=40.0,
        heatmap_entropy=0.93,
    )

    candidate = HeatmapPlayerResult(
        player_id=789071,
        player_name="Dani Olmo",
        available=False,
        grid_width=None,
        grid_height=None,
        grid=None,
        matches_with_heatmap=None,
        heatmap_point_count=None,
        weighted_mean_x=None,
        weighted_mean_y=None,
        peak_cell_x=None,
        peak_cell_y=None,
        heatmap_entropy=None,
    )

    similarity = HeatmapSimilarityResult(
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

    result = HeatmapComparisonResult(
        target=target,
        candidate=candidate,
        similarity=similarity,
    )

    payload = result.to_dict()

    assert payload["target"]["available"] is True
    assert payload["target"]["grid"] == [
        [0.1, 0.2],
        [0.3, 0.4],
    ]

    assert payload["candidate"]["available"] is False
    assert payload["candidate"]["grid"] is None

    assert payload["similarity"]["available"] is False

    json.dumps(
        payload,
        allow_nan=False,
    )


def _comparison_catalog(
    *,
    heatmap_similarity: pd.DataFrame | None = None,
    include_candidate_grid: bool = True,
) -> TransferDataCatalog:
    players = pd.DataFrame(
        [
            {
                "player_id": 10,
                "player_name": "Target Player",
            },
            {
                "player_id": 20,
                "player_name": "Candidate Player",
            },
        ]
    )

    profiles = pd.DataFrame(
        [
            {
                "player_id": 10,
                "matches_with_heatmap": 6,
                "heatmap_point_count": 200,
                "weighted_mean_x": 60.0,
                "weighted_mean_y": 40.0,
                "peak_cell_x": 62.5,
                "peak_cell_y": 37.5,
                "heatmap_entropy": 0.94,
            },
            {
                "player_id": 20,
                "matches_with_heatmap": 4,
                "heatmap_point_count": 100,
                "weighted_mean_x": 55.0,
                "weighted_mean_y": 45.0,
                "peak_cell_x": 57.5,
                "peak_cell_y": 42.5,
                "heatmap_entropy": 0.90,
            },
        ]
    )

    grids = {
        10: np.array(
            [
                [0.25, 0.25],
                [0.25, 0.25],
            ],
            dtype=np.float32,
        ),
    }

    if include_candidate_grid:
        grids[20] = np.array(
            [
                [0.125, 0.125],
                [0.25, 0.5],
            ],
            dtype=np.float32,
        )

    if heatmap_similarity is None:
        heatmap_similarity = pd.DataFrame(
            [
                {
                    "target_player_id": 10,
                    "candidate_player_id": 20,
                    "heatmap_similarity_score_pct": 84.0,
                    "heatmap_cosine_similarity_pct": 88.0,
                    "occupation_overlap_pct": 79.0,
                    "peak_zone_similarity_pct": 92.0,
                    "peak_zone_distance": 1.5,
                    "entropy_similarity_pct": 96.0,
                    "target_matches_with_heatmap": 6,
                    "candidate_matches_with_heatmap": 4,
                    "target_heatmap_points": 200,
                    "candidate_heatmap_points": 100,
                }
            ]
        )

    return TransferDataCatalog(
        players=players,
        similarity=pd.DataFrame(),
        heatmap_similarity=heatmap_similarity,
        heatmap_profiles=profiles,
        heatmap_grids=grids,
    )


def test_heatmap_comparison_builds_measured_result() -> None:
    catalog = _comparison_catalog()

    result = get_heatmap_comparison_from_catalog(
        HeatmapComparisonRequest(
            target_player_id=10,
            candidate_player_id=20,
        ),
        catalog,
    )

    assert result.target.player_name == "Target Player"
    assert result.target.available is True
    assert result.target.grid_width == 2
    assert result.target.grid_height == 2
    assert result.target.matches_with_heatmap == 6
    assert result.target.heatmap_point_count == 200

    assert result.candidate.player_name == "Candidate Player"
    assert result.candidate.available is True
    assert result.candidate.grid == (
        (0.125, 0.125),
        (0.25, 0.5),
    )

    assert result.similarity.available is True
    assert result.similarity.heatmap_similarity_score_pct == 84.0
    assert result.similarity.heatmap_cosine_similarity_pct == 88.0
    assert result.similarity.occupation_overlap_pct == 79.0
    assert result.similarity.peak_zone_similarity_pct == 92.0
    assert result.similarity.peak_zone_distance == 1.5
    assert result.similarity.entropy_similarity_pct == 96.0
    assert result.similarity.target_matches_with_heatmap == 6
    assert result.similarity.candidate_matches_with_heatmap == 4
    assert result.similarity.target_heatmap_points == 200
    assert result.similarity.candidate_heatmap_points == 100

    payload = result.to_dict()

    assert "effective_heatmap_score_pct" not in payload["similarity"]


def test_heatmap_comparison_orients_reverse_pair_sample_evidence() -> None:
    heatmap_similarity = pd.DataFrame(
        [
            {
                "target_player_id": 20,
                "candidate_player_id": 10,
                "heatmap_similarity_score_pct": 84.0,
                "heatmap_cosine_similarity_pct": 88.0,
                "occupation_overlap_pct": 79.0,
                "peak_zone_similarity_pct": 92.0,
                "peak_zone_distance": 1.5,
                "entropy_similarity_pct": 96.0,
                "target_matches_with_heatmap": 4,
                "candidate_matches_with_heatmap": 6,
                "target_heatmap_points": 100,
                "candidate_heatmap_points": 200,
            }
        ]
    )

    result = get_heatmap_comparison_from_catalog(
        HeatmapComparisonRequest(
            target_player_id=10,
            candidate_player_id=20,
        ),
        _comparison_catalog(
            heatmap_similarity=heatmap_similarity,
        ),
    )

    assert result.similarity.available is True
    assert result.similarity.target_matches_with_heatmap == 6
    assert result.similarity.candidate_matches_with_heatmap == 4
    assert result.similarity.target_heatmap_points == 200
    assert result.similarity.candidate_heatmap_points == 100


def test_heatmap_comparison_keeps_missing_grid_explicit() -> None:
    result = get_heatmap_comparison_from_catalog(
        HeatmapComparisonRequest(
            target_player_id=10,
            candidate_player_id=20,
        ),
        _comparison_catalog(
            include_candidate_grid=False,
        ),
    )

    assert result.target.available is True

    assert result.candidate.available is False
    assert result.candidate.grid is None
    assert result.candidate.grid_width is None
    assert result.candidate.grid_height is None

    # Profile evidence is still genuine and may remain available
    # independently from the visualization grid artifact.
    assert result.candidate.matches_with_heatmap == 4
    assert result.candidate.heatmap_point_count == 100


def test_heatmap_comparison_keeps_missing_similarity_explicit() -> None:
    empty_similarity = pd.DataFrame(
        columns=[
            "target_player_id",
            "candidate_player_id",
            "heatmap_similarity_score_pct",
        ]
    )

    result = get_heatmap_comparison_from_catalog(
        HeatmapComparisonRequest(
            target_player_id=10,
            candidate_player_id=20,
        ),
        _comparison_catalog(
            heatmap_similarity=empty_similarity,
        ),
    )

    assert result.similarity.available is False
    assert result.similarity.heatmap_similarity_score_pct is None
    assert result.similarity.occupation_overlap_pct is None

    payload = result.to_dict()

    assert "effective_heatmap_score_pct" not in payload["similarity"]


def test_heatmap_comparison_rejects_same_player() -> None:
    with pytest.raises(
        InvalidTransferAnalysisRequestError,
        match="two different players",
    ):
        get_heatmap_comparison_from_catalog(
            HeatmapComparisonRequest(
                target_player_id=10,
                candidate_player_id=10,
            ),
            _comparison_catalog(),
        )


def test_heatmap_comparison_rejects_non_positive_player_id() -> None:
    with pytest.raises(
        InvalidTransferAnalysisRequestError,
        match="positive integers",
    ):
        get_heatmap_comparison_from_catalog(
            HeatmapComparisonRequest(
                target_player_id=0,
                candidate_player_id=20,
            ),
            _comparison_catalog(),
        )


def test_heatmap_comparison_preserves_player_not_found_error() -> None:
    with pytest.raises(
        PlayerNotFoundError,
        match="999",
    ):
        get_heatmap_comparison_from_catalog(
            HeatmapComparisonRequest(
                target_player_id=10,
                candidate_player_id=999,
            ),
            _comparison_catalog(),
        )
