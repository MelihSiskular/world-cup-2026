"""HTTP routes for searching the player catalogue."""

from __future__ import annotations

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Path,
    Query,
    status,
)

from wc26.analytics.transfer_intelligence.errors import (
    DatasetNotFoundError,
    InvalidDatasetError,
    InvalidPlayerProfileError,
    InvalidPlayerSearchError,
    PlayerNotFoundError,
)
from wc26.analytics.transfer_intelligence.models import (
    PlayerProfileRequest,
    PlayerSearchFiltersRequest,
    PlayerSearchRequest,
)
from wc26.api.dependencies import (
    PlayerProfileRunner,
    PlayerSearchFiltersRunner,
    PlayerSearchRunner,
    TransferDatasetPaths,
    get_player_profile_runner,
    get_player_search_filters_runner,
    get_player_search_runner,
    get_transfer_dataset_paths,
)
from wc26.api.errors import (
    PlayerProfileExecutionError,
    PlayerSearchExecutionError,
)
from wc26.api.schemas.errors import ApiErrorResponse
from wc26.api.schemas.players import (
    PlayerProfileResponse,
    PlayerSearchFiltersResponse,
    PlayerSearchResponse,
)

router = APIRouter(
    prefix="/api/v1/players",
    tags=["players"],
)


@router.get(
    "/search",
    response_model=PlayerSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Discover and filter the player catalogue",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ApiErrorResponse,
            "description": ("The player-discovery parameters are invalid."),
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ApiErrorResponse,
            "description": ("The player profile datasets are missing or invalid."),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ApiErrorResponse,
            "description": ("Player discovery failed unexpectedly."),
        },
    },
)
def search_player_catalogue(
    dataset_paths: Annotated[
        TransferDatasetPaths,
        Depends(get_transfer_dataset_paths),
    ],
    player_search_runner: Annotated[
        PlayerSearchRunner,
        Depends(get_player_search_runner),
    ],
    q: Annotated[
        str | None,
        Query(
            min_length=2,
            max_length=100,
            description=("Optional case- and diacritic-insensitive player-name query."),
            examples=["olise"],
        ),
    ] = None,
    position: Annotated[
        list[str] | None,
        Query(
            description=("Position values. Repeat the parameter to select multiple positions."),
        ),
    ] = None,
    final_role: Annotated[
        list[str] | None,
        Query(
            description=("Final-role values. Repeat the parameter to select multiple roles."),
        ),
    ] = None,
    archetype: Annotated[
        list[str] | None,
        Query(
            description=("Archetype values. Repeat the parameter to select multiple archetypes."),
        ),
    ] = None,
    country: Annotated[
        list[str] | None,
        Query(
            description=("Nationality values. Repeat the parameter to select multiple countries."),
        ),
    ] = None,
    min_age: Annotated[
        float | None,
        Query(
            ge=0,
            description="Inclusive minimum player age.",
        ),
    ] = None,
    max_age: Annotated[
        float | None,
        Query(
            ge=0,
            description="Inclusive maximum player age.",
        ),
    ] = None,
    min_market_value: Annotated[
        float | None,
        Query(
            ge=0,
            description=("Inclusive minimum market value in the reported currency."),
        ),
    ] = None,
    max_market_value: Annotated[
        float | None,
        Query(
            ge=0,
            description=("Inclusive maximum market value in the reported currency."),
        ),
    ] = None,
    min_minutes: Annotated[
        float | None,
        Query(
            ge=0,
            description=("Inclusive minimum tournament minutes."),
        ),
    ] = None,
    min_role_confidence: Annotated[
        float | None,
        Query(
            ge=0,
            le=100,
            description=("Inclusive minimum role-confidence percentage."),
        ),
    ] = None,
    min_data_reliability: Annotated[
        float | None,
        Query(
            ge=0,
            le=100,
            description=("Inclusive minimum data-reliability score."),
        ),
    ] = None,
    sort_by: Annotated[
        str | None,
        Query(
            description=(
                "Optional sorting field. Supported values are "
                "relevance, player_name, age, market_value, "
                "minutes, role_confidence, data_reliability, "
                "and player_quality."
            ),
        ),
    ] = None,
    sort_direction: Annotated[
        str | None,
        Query(
            description=("Optional sorting direction: asc or desc."),
        ),
    ] = None,
    offset: Annotated[
        int,
        Query(
            ge=0,
            description=("Number of filtered players to skip."),
        ),
    ] = 0,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=25,
            description=("Maximum number of players in the current page."),
        ),
    ] = 10,
) -> PlayerSearchResponse:
    """Return players matching the supplied discovery criteria."""

    request = PlayerSearchRequest(
        query=q,
        features=dataset_paths.features,
        limit=limit,
        offset=offset,
        positions=tuple(position or ()),
        final_roles=tuple(final_role or ()),
        archetypes=tuple(archetype or ()),
        countries=tuple(country or ()),
        minimum_age=min_age,
        maximum_age=max_age,
        minimum_market_value=min_market_value,
        maximum_market_value=max_market_value,
        minimum_minutes=min_minutes,
        minimum_role_confidence=min_role_confidence,
        minimum_data_reliability=min_data_reliability,
        sort_by=sort_by,
        sort_direction=sort_direction,
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
        raise PlayerSearchExecutionError("Player search execution failed.") from exception


@router.get(
    "/search/filters",
    response_model=PlayerSearchFiltersResponse,
    status_code=status.HTTP_200_OK,
    summary="Get player-discovery filter metadata",
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ApiErrorResponse,
            "description": ("The player datasets are missing or invalid."),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ApiErrorResponse,
            "description": ("Player filter metadata failed unexpectedly."),
        },
    },
)
def get_player_search_filters_metadata(
    dataset_paths: Annotated[
        TransferDatasetPaths,
        Depends(get_transfer_dataset_paths),
    ],
    player_search_filters_runner: Annotated[
        PlayerSearchFiltersRunner,
        Depends(get_player_search_filters_runner),
    ],
) -> PlayerSearchFiltersResponse:
    """Return dataset-backed advanced-filter metadata."""

    request = PlayerSearchFiltersRequest(
        features=dataset_paths.features,
        player_tournament_summary=(dataset_paths.player_tournament_summary),
    )

    try:
        result = player_search_filters_runner(request)

        return PlayerSearchFiltersResponse.model_validate(result.to_dict())
    except (
        DatasetNotFoundError,
        InvalidDatasetError,
    ):
        raise
    except Exception as exception:
        raise PlayerSearchExecutionError(
            "Player search filter metadata execution failed."
        ) from exception


@router.get(
    "/{player_id}",
    response_model=PlayerProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get one player profile",
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ApiErrorResponse,
            "description": "The player identifier is invalid.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ApiErrorResponse,
            "description": "The player was not found.",
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ApiErrorResponse,
            "description": ("The player feature dataset is missing or invalid."),
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ApiErrorResponse,
            "description": ("Player profile retrieval failed unexpectedly."),
        },
    },
)
def get_player_profile_by_id(
    player_id: Annotated[
        int,
        Path(
            gt=0,
            description="Stable player identifier.",
            examples=[978838],
        ),
    ],
    dataset_paths: Annotated[
        TransferDatasetPaths,
        Depends(get_transfer_dataset_paths),
    ],
    player_profile_runner: Annotated[
        PlayerProfileRunner,
        Depends(get_player_profile_runner),
    ],
) -> PlayerProfileResponse:
    """Return the detailed profile for one player ID."""

    request = PlayerProfileRequest(
        player_id=player_id,
        features=dataset_paths.features,
        player_tournament_summary=(dataset_paths.player_tournament_summary),
    )

    try:
        result = player_profile_runner(request)

        return PlayerProfileResponse.model_validate(result.to_dict())
    except (
        InvalidPlayerProfileError,
        PlayerNotFoundError,
        DatasetNotFoundError,
        InvalidDatasetError,
    ):
        raise
    except Exception as exception:
        raise PlayerProfileExecutionError("Player profile execution failed.") from exception


__all__ = [
    "router",
]
