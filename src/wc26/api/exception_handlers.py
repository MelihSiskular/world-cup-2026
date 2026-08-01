"""Central exception handlers for the WC26 API."""

from __future__ import annotations

import logging
from typing import Literal

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
from wc26.api.request_context import (
    get_request_id,
)
from wc26.api.schemas.errors import (
    ApiErrorCode,
    ApiErrorDetail,
    ApiErrorResponse,
)

type ApiErrorEvent = Literal[
    "api.error.client",
    "api.error.dependency",
    "api.error.internal",
]


logger = logging.getLogger("wc26.api.error")


def _error_log_fields(
    *,
    request: Request,
    exception: Exception,
    status_code: int,
    error_code: ApiErrorCode,
) -> dict[str, object]:
    """Return shared structured API error fields."""

    return {
        "request_id": get_request_id(),
        "http_method": request.method,
        "http_path": request.url.path,
        "status_code": status_code,
        "error_code": error_code,
        "exception_type": (type(exception).__name__),
    }


def _log_api_error(
    *,
    request: Request,
    exception: Exception,
    status_code: int,
    error_code: ApiErrorCode,
    event: ApiErrorEvent,
    level: int,
) -> None:
    """Emit one normalized API error log."""

    log_fields = _error_log_fields(
        request=request,
        exception=exception,
        status_code=status_code,
        error_code=error_code,
    )

    if event == "api.error.internal":
        cause = exception.__cause__ if exception.__cause__ is not None else exception

        logger.log(
            level,
            "Internal API request failure",
            extra={
                "event": event,
                **log_fields,
                "cause_type": (type(cause).__name__),
            },
            exc_info=cause,
        )
        return

    message = {
        "api.error.client": ("Client request rejected"),
        "api.error.dependency": ("API dependency unavailable"),
    }[event]

    logger.log(
        level,
        message,
        extra={
            "event": event,
            **log_fields,
        },
    )


def _error_response(
    *,
    request: Request,
    exception: Exception,
    status_code: int,
    code: ApiErrorCode,
    message: str,
    event: ApiErrorEvent,
    log_level: int,
) -> JSONResponse:
    """Log and build the standard API error response."""

    _log_api_error(
        request=request,
        exception=exception,
        status_code=status_code,
        error_code=code,
        event=event,
        level=log_level,
    )

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


async def handle_invalid_transfer_analysis_request(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Convert an invalid transfer target into HTTP 400."""

    return _error_response(
        request=request,
        exception=exception,
        status_code=(status.HTTP_400_BAD_REQUEST),
        code=("invalid_transfer_analysis_request"),
        message=str(exception),
        event="api.error.client",
        log_level=logging.WARNING,
    )


async def handle_invalid_player_profile(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Convert invalid player-profile parameters into HTTP 400."""

    return _error_response(
        request=request,
        exception=exception,
        status_code=(status.HTTP_400_BAD_REQUEST),
        code="invalid_player_profile",
        message=str(exception),
        event="api.error.client",
        log_level=logging.WARNING,
    )


async def handle_player_profile_execution_error(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Convert an unexpected player-profile failure into HTTP 500."""

    return _error_response(
        request=request,
        exception=exception,
        status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
        code="player_profile_failed",
        message=("Player profile could not be retrieved."),
        event="api.error.internal",
        log_level=logging.ERROR,
    )


async def handle_invalid_player_search(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Convert invalid player-search parameters into HTTP 400."""

    return _error_response(
        request=request,
        exception=exception,
        status_code=(status.HTTP_400_BAD_REQUEST),
        code="invalid_player_search",
        message=str(exception),
        event="api.error.client",
        log_level=logging.WARNING,
    )


async def handle_player_search_execution_error(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Convert an unexpected player-search failure into HTTP 500."""

    return _error_response(
        request=request,
        exception=exception,
        status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
        code="player_search_failed",
        message=("Player search could not be completed."),
        event="api.error.internal",
        log_level=logging.ERROR,
    )


async def handle_player_not_found(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Convert an unresolved player query into HTTP 404."""

    return _error_response(
        request=request,
        exception=exception,
        status_code=(status.HTTP_404_NOT_FOUND),
        code="player_not_found",
        message=str(exception),
        event="api.error.client",
        log_level=logging.WARNING,
    )


async def handle_ambiguous_player(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Convert an ambiguous player query into HTTP 409."""

    return _error_response(
        request=request,
        exception=exception,
        status_code=(status.HTTP_409_CONFLICT),
        code="ambiguous_player",
        message=str(exception),
        event="api.error.client",
        log_level=logging.WARNING,
    )


async def handle_dataset_not_found(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Convert an unavailable analytics dataset into HTTP 503."""

    return _error_response(
        request=request,
        exception=exception,
        status_code=(status.HTTP_503_SERVICE_UNAVAILABLE),
        code="dataset_unavailable",
        message=("A required transfer dataset is unavailable."),
        event="api.error.dependency",
        log_level=logging.ERROR,
    )


async def handle_invalid_dataset(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Convert an invalid analytics dataset into HTTP 503."""

    return _error_response(
        request=request,
        exception=exception,
        status_code=(status.HTTP_503_SERVICE_UNAVAILABLE),
        code="invalid_dataset",
        message=("A transfer dataset does not satisfy the required data contract."),
        event="api.error.dependency",
        log_level=logging.ERROR,
    )


async def handle_analysis_execution_error(
    request: Request,
    exception: Exception,
) -> JSONResponse:
    """Convert an unexpected analysis failure into HTTP 500."""

    return _error_response(
        request=request,
        exception=exception,
        status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
        code="analysis_failed",
        message=("Transfer analysis could not be completed."),
        event="api.error.internal",
        log_level=logging.ERROR,
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
