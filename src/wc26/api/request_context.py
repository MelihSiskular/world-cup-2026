"""HTTP request context and observability middleware."""

from __future__ import annotations

import logging
import re
from contextvars import ContextVar
from time import perf_counter
from uuid import uuid4

from starlette.datastructures import (
    Headers,
    MutableHeaders,
)
from starlette.types import (
    ASGIApp,
    Message,
    Receive,
    Scope,
    Send,
)

REQUEST_ID_HEADER = "X-Request-ID"

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_REQUEST_ID_CONTEXT: ContextVar[str | None] = ContextVar(
    "wc26_request_id",
    default=None,
)

logger = logging.getLogger("wc26.api.request")


def get_request_id() -> str | None:
    """Return the request ID bound to the current context."""

    return _REQUEST_ID_CONTEXT.get()


def resolve_request_id(
    supplied_request_id: str | None,
) -> str:
    """Validate a supplied request ID or generate a new one."""

    if supplied_request_id is not None:
        normalized = supplied_request_id.strip()

        if _REQUEST_ID_PATTERN.fullmatch(normalized):
            return normalized

    return uuid4().hex


def _request_log_level(
    status_code: int,
) -> int:
    """Return the appropriate log level for one response."""

    if status_code >= 500:
        return logging.ERROR

    if status_code >= 400:
        return logging.WARNING

    return logging.INFO


def _duration_ms(
    started_at: float,
) -> float:
    """Return elapsed request time in milliseconds."""

    return round(
        (perf_counter() - started_at) * 1000,
        3,
    )


class RequestObservabilityMiddleware:
    """Attach request IDs and emit one completion log."""

    def __init__(
        self,
        app: ASGIApp,
    ) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(
                scope,
                receive,
                send,
            )
            return

        request_headers = Headers(scope=scope)
        request_id = resolve_request_id(request_headers.get(REQUEST_ID_HEADER))
        context_token = _REQUEST_ID_CONTEXT.set(request_id)

        method = str(
            scope.get(
                "method",
                "",
            )
        )
        path = str(
            scope.get(
                "path",
                "",
            )
        )
        started_at = perf_counter()
        status_code = 500

        async def send_with_request_id(
            message: Message,
        ) -> None:
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = int(message["status"])

                response_headers = MutableHeaders(raw=message["headers"])
                response_headers[REQUEST_ID_HEADER] = request_id
                message["headers"] = response_headers.raw

            await send(message)

        try:
            await self.app(
                scope,
                receive,
                send_with_request_id,
            )
        except Exception:
            logger.exception(
                "HTTP request failed",
                extra={
                    "event": ("http.request.failed"),
                    "request_id": request_id,
                    "http_method": method,
                    "http_path": path,
                    "status_code": 500,
                    "duration_ms": (_duration_ms(started_at)),
                },
            )
            raise
        else:
            logger.log(
                _request_log_level(status_code),
                "HTTP request completed",
                extra={
                    "event": ("http.request.completed"),
                    "request_id": request_id,
                    "http_method": method,
                    "http_path": path,
                    "status_code": (status_code),
                    "duration_ms": (_duration_ms(started_at)),
                },
            )
        finally:
            _REQUEST_ID_CONTEXT.reset(context_token)


__all__ = [
    "REQUEST_ID_HEADER",
    "RequestObservabilityMiddleware",
    "get_request_id",
    "resolve_request_id",
]
