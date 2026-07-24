"""HTTP routes for Transfer Intelligence analysis."""

from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    status,
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
from wc26.api.schemas.transfer_intelligence import (
    TransferAnalysisPayload,
    TransferAnalysisResponse,
)

router = APIRouter(
    prefix="/api/v1/transfer-intelligence",
    tags=["transfer-intelligence"],
)


@router.post(
    "/analyze",
    response_model=TransferAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze transfer alternatives",
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
        features=dataset_paths.features,
        similarity=dataset_paths.similarity,
        heatmap_similarity=dataset_paths.heatmap_similarity,
        heatmap_profiles=dataset_paths.heatmap_profiles,
        minimum_minutes=payload.minimum_minutes,
        minimum_role_confidence=payload.minimum_role_confidence,
        maximum_market_value=payload.maximum_market_value,
        neutral_heatmap_score=payload.neutral_heatmap_score,
    )

    result = analysis_runner(request)

    return TransferAnalysisResponse.model_validate(result.to_dict())


__all__ = [
    "router",
]
