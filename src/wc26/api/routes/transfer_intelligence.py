"""HTTP routes for Transfer Intelligence analysis."""

from __future__ import annotations

import logging
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
    TransferAnalysisRequest,
)
from wc26.api.dependencies import (
    TransferAnalysisRunner,
    TransferDatasetPaths,
    get_transfer_analysis_runner,
    get_transfer_dataset_paths,
)
from wc26.api.errors import TransferAnalysisExecutionError
from wc26.api.schemas.errors import ApiErrorResponse
from wc26.api.schemas.transfer_intelligence import (
    TransferAnalysisPayload,
    TransferAnalysisResponse,
)

router = APIRouter(
    prefix="/api/v1/transfer-intelligence",
    tags=["transfer-intelligence"],
)
logger = logging.getLogger(__name__)


@router.post(
    "/analyze",
    response_model=TransferAnalysisResponse,
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
        logger.exception(
            ("Unexpected transfer analysis failure for player=%r player_id=%r"),
            payload.player,
            payload.player_id,
        )

        raise TransferAnalysisExecutionError("Transfer analysis execution failed.") from exception


__all__ = [
    "router",
]
