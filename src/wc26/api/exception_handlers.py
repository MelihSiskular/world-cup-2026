"""Central exception handlers for the WC26 API."""

from __future__ import annotations

import logging

from fastapi import FastAPI, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from wc26.analytics.transfer_intelligence.errors import (
    AmbiguousPlayerError,
    DatasetNotFoundError,
    InvalidDatasetError,
    InvalidPlayerProfileError,
    InvalidPlayerSearchError,
    InvalidTransferAnalysisRequestError,
    PlayerNotFoundError,
)
from wc26.api.errors import (
    PlayerProfileExecutionError,
    PlayerSearchExecutionError,
    TransferAnalysisExecutionError,
)
from wc26.api.schemas.errors import (
    ApiErrorCode,
    ApiErrorDetail,
    ApiErrorResponse,
)

logger = logging.getLogger(__name__)


async def handle_invalid_transfer_analysis_request(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Convert an invalid transfer target into HTTP 400."""

    del request

    return _error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        code="invalid_transfer_analysis_request",
        message=str(exception),
    )


async def handle_invalid_player_profile(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Convert invalid player-profile parameters into HTTP 400."""

    del request

    return _error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        code="invalid_player_profile",
        message=str(exception),
    )


async def handle_player_profile_execution_error(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Convert an unexpected player-profile failure into HTTP 500."""

    del request

    logger.error(
        "Player profile retrieval failed: %s",
        exception,
    )

    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="player_profile_failed",
        message="Player profile could not be retrieved.",
    )


async def handle_invalid_player_search(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Convert invalid player-search parameters into HTTP 400."""

    del request

    return _error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        code="invalid_player_search",
        message=str(exception),
    )


async def handle_player_search_execution_error(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Convert an unexpected player-search failure into HTTP 500."""

    del request

    logger.error(
        "Player search failed: %s",
        exception,
    )

    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="player_search_failed",
        message="Player search could not be completed.",
    )


def _error_response(
    *,
    status_code: int,
    code: ApiErrorCode,
    message: str,
) -> JSONResponse:
    """Build the standard API error response."""

    payload = ApiErrorResponse(
        error=ApiErrorDetail(
            code=code,
            message=message,
        )
    )

    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
    )


async def handle_player_not_found(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Convert an unresolved player query into HTTP 404."""

    del request

    return _error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        code="player_not_found",
        message=str(exception),
    )


async def handle_ambiguous_player(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Convert an ambiguous player query into HTTP 409."""

    del request

    return _error_response(
        status_code=status.HTTP_409_CONFLICT,
        code="ambiguous_player",
        message=str(exception),
    )


async def handle_dataset_not_found(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Convert an unavailable analytics dataset into HTTP 503."""

    del request

    logger.error(
        "Transfer Intelligence dataset unavailable: %s",
        exception,
    )

    return _error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        code="dataset_unavailable",
        message="A required transfer dataset is unavailable.",
    )


async def handle_invalid_dataset(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Convert an invalid analytics dataset into HTTP 503."""

    del request

    logger.error(
        "Transfer Intelligence dataset is invalid: %s",
        exception,
    )

    return _error_response(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        code="invalid_dataset",
        message=("A transfer dataset does not satisfy the required data contract."),
    )


async def handle_analysis_execution_error(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Convert an unexpected analysis failure into HTTP 500."""

    del request

    logger.error(
        "Transfer Intelligence analysis failed: %s",
        exception,
    )

    return _error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        code="analysis_failed",
        message="Transfer analysis could not be completed.",
    )


def register_exception_handlers(
    application: FastAPI,
) -> None:
    """Register domain-to-HTTP exception mappings."""

    application.add_exception_handler(
        PlayerNotFoundError,
        handle_player_not_found,
    )
    application.add_exception_handler(
        AmbiguousPlayerError,
        handle_ambiguous_player,
    )
    application.add_exception_handler(
        DatasetNotFoundError,
        handle_dataset_not_found,
    )
    application.add_exception_handler(
        InvalidDatasetError,
        handle_invalid_dataset,
    )
    application.add_exception_handler(
        InvalidTransferAnalysisRequestError,
        handle_invalid_transfer_analysis_request,
    )
    application.add_exception_handler(
        TransferAnalysisExecutionError,
        handle_analysis_execution_error,
    )
    application.add_exception_handler(
        InvalidPlayerSearchError,
        handle_invalid_player_search,
    )
    application.add_exception_handler(
        PlayerSearchExecutionError,
        handle_player_search_execution_error,
    )
    application.add_exception_handler(
        InvalidPlayerProfileError,
        handle_invalid_player_profile,
    )
    application.add_exception_handler(
        PlayerProfileExecutionError,
        handle_player_profile_execution_error,
    )


__all__ = [
    "register_exception_handlers",
]
