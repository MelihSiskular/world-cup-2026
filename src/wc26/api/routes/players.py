"""HTTP routes for searching the player catalogue."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
    status,
)

from wc26.analytics.transfer_intelligence.errors import (
    DatasetNotFoundError,
    InvalidDatasetError,
    InvalidPlayerSearchError,
)
from wc26.analytics.transfer_intelligence.models import (
    PlayerSearchRequest,
)
from wc26.api.dependencies import (
    PlayerSearchRunner,
    TransferDatasetPaths,
    get_player_search_runner,
    get_transfer_dataset_paths,
)
from wc26.api.errors import PlayerSearchExecutionError
from wc26.api.schemas.errors import ApiErrorResponse
from wc26.api.schemas.players import PlayerSearchResponse

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/api/v1/players",
    tags=["players"],
)


@router.get(
    "/search",
    response_model=PlayerSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search the player catalogue",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ApiErrorResponse,
            "description": ("The player-search parameters are invalid."),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ApiErrorResponse,
            "description": ("The player feature dataset is missing or invalid."),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ApiErrorResponse,
            "description": ("Player search failed unexpectedly."),
        },
    },
)
def search_player_catalogue(
    q: Annotated[
        str,
        Query(
            min_length=2,
            max_length=100,
            description=("Case- and diacritic-insensitive player-name query."),
            examples=["olise"],
        ),
    ],
    dataset_paths: Annotated[
        TransferDatasetPaths,
        Depends(get_transfer_dataset_paths),
    ],
    player_search_runner: Annotated[
        PlayerSearchRunner,
        Depends(get_player_search_runner),
    ],
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=25,
            description=("Maximum number of matching players."),
        ),
    ] = 10,
) -> PlayerSearchResponse:
    """Return lightweight players matching the supplied name query."""

    request = PlayerSearchRequest(
        query=q,
        features=dataset_paths.features,
        limit=limit,
    )

    try:
        result = player_search_runner(request)

        return PlayerSearchResponse.model_validate(result.to_dict())
    except (
        InvalidPlayerSearchError,
        DatasetNotFoundError,
        InvalidDatasetError,
    ):
        raise
    except Exception as exception:
        logger.exception(
            "Unexpected player-search failure for query %s",
            q,
        )

        raise PlayerSearchExecutionError("Player search execution failed.") from exception


__all__ = [
    "router",
]
