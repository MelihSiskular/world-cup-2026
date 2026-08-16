"""HTTP routes for Transfer Intelligence analysis."""

from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
)

from wc26.analytics.transfer_intelligence.errors import (
    AmbiguousPlayerError,
    DatasetNotFoundError,
    InvalidDatasetError,
    InvalidTransferAnalysisRequestError,
    PlayerNotFoundError,
)
from wc26.analytics.transfer_intelligence.models import (
    HeatmapComparisonRequest,
    RadarComparisonRequest,
    TransferAnalysisRequest,
)
from wc26.api.dependencies import (
    HeatmapComparisonRunner,
    RadarComparisonRunner,
    TransferAnalysisRunner,
    TransferDatasetPaths,
    get_heatmap_comparison_runner,
    get_radar_comparison_runner,
    get_transfer_analysis_runner,
    get_transfer_dataset_paths,
)
from wc26.api.errors import TransferAnalysisExecutionError
from wc26.api.schemas.errors import ApiErrorResponse
from wc26.api.schemas.transfer_intelligence import (
    HeatmapComparisonResponse,
    RadarComparisonResponse,
    TransferAnalysisPayload,
    TransferAnalysisResponse,
)

router = APIRouter(
    prefix="/api/v1/transfer-intelligence",
    tags=["transfer-intelligence"],
)


@router.get(
    "/heatmap-comparison/{target_player_id}/{candidate_player_id}",
    response_model=HeatmapComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare measured player heatmaps",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ApiErrorResponse,
            "description": ("The heatmap comparison request is invalid."),
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ApiErrorResponse,
            "description": ("One of the requested players was not found."),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ApiErrorResponse,
            "description": ("Required heatmap analytics data is unavailable."),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ApiErrorResponse,
            "description": ("Heatmap comparison failed unexpectedly."),
        },
    },
)
def compare_player_heatmaps(
    target_player_id: int,
    candidate_player_id: int,
    comparison_runner: Annotated[
        HeatmapComparisonRunner,
        Depends(get_heatmap_comparison_runner),
    ],
) -> HeatmapComparisonResponse:
    """Return measured tournament heatmap evidence for two players."""

    request = HeatmapComparisonRequest(
        target_player_id=target_player_id,
        candidate_player_id=candidate_player_id,
    )

    result = comparison_runner(request)

    return HeatmapComparisonResponse.model_validate(result.to_dict())


@router.get(
    "/radar-comparison/{target_player_id}/{candidate_player_id}",
    response_model=RadarComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare position-relative player style profiles",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ApiErrorResponse,
            "description": ("The radar comparison request is invalid."),
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ApiErrorResponse,
            "description": ("One of the requested players was not found."),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ApiErrorResponse,
            "description": ("Required radar analytics data is unavailable."),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ApiErrorResponse,
            "description": ("Radar comparison failed unexpectedly."),
        },
    },
)
def compare_player_radars(
    target_player_id: int,
    candidate_player_id: int,
    comparison_runner: Annotated[
        RadarComparisonRunner,
        Depends(get_radar_comparison_runner),
    ],
) -> RadarComparisonResponse:
    """Return position-relative playing-style profiles for two players."""

    request = RadarComparisonRequest(
        target_player_id=target_player_id,
        candidate_player_id=candidate_player_id,
    )

    result = comparison_runner(request)

    return RadarComparisonResponse.model_validate(result.to_dict())


@router.post(
    "/analyze",
    response_model=TransferAnalysisResponse,
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    summary="Analyze transfer alternatives",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ApiErrorResponse,
            "description": ("The transfer-analysis target is invalid."),
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ApiErrorResponse,
            "description": "The target player was not found.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ApiErrorResponse,
            "description": ("The supplied player query matched multiple players."),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ApiErrorResponse,
            "description": ("A required analytics dataset is missing or invalid."),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ApiErrorResponse,
            "description": ("Transfer analysis failed unexpectedly."),
        },
    },
)
def analyze_transfer_alternatives(
    payload: TransferAnalysisPayload,
    dataset_paths: Annotated[
        TransferDatasetPaths,
        Depends(get_transfer_dataset_paths),
    ],
    analysis_runner: Annotated[
        TransferAnalysisRunner,
        Depends(get_transfer_analysis_runner),
    ],
) -> TransferAnalysisResponse:
    """Run Transfer Intelligence analysis for one target player."""

    request = TransferAnalysisRequest(
        player=payload.player,
        player_id=payload.player_id,
        features=dataset_paths.features,
        similarity=dataset_paths.similarity,
        heatmap_similarity=dataset_paths.heatmap_similarity,
        heatmap_profiles=dataset_paths.heatmap_profiles,
        minimum_minutes=payload.minimum_minutes,
        minimum_role_confidence=payload.minimum_role_confidence,
        maximum_market_value=payload.maximum_market_value,
        neutral_heatmap_score=payload.neutral_heatmap_score,
    )

    try:
        result = analysis_runner(request)

        return TransferAnalysisResponse.model_validate(result.to_dict())
    except (
        PlayerNotFoundError,
        AmbiguousPlayerError,
        DatasetNotFoundError,
        InvalidDatasetError,
        InvalidTransferAnalysisRequestError,
    ):
        raise

    except Exception as exception:
        raise TransferAnalysisExecutionError("Transfer analysis execution failed.") from exception


__all__ = [
    "router",
]
