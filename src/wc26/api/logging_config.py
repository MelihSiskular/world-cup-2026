"""Logging configuration for the WC26 API."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Final, TextIO

from wc26.api.request_context import get_request_id

_LOG_RECORD_ATTRIBUTES: Final = frozenset(
    logging.LogRecord(
        name="",
        level=0,
        pathname="",
        lineno=0,
        msg="",
        args=(),
        exc_info=None,
    ).__dict__
) | frozenset(
    {
        "asctime",
        "message",
    }
)

_UVICORN_LOGGERS: Final = (
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
)


class LogConfigurationError(ValueError):
    """Raised when a logging setting is invalid."""


def _utc_timestamp(
    created_at: float,
) -> str:
    """Return an ISO-8601 UTC log timestamp."""

    return (
        datetime.fromtimestamp(
            created_at,
            tz=UTC,
        )
        .isoformat(timespec="milliseconds")
        .replace(
            "+00:00",
            "Z",
        )
    )


def _json_default(
    value: object,
) -> str:
    """Convert unsupported structured values to text."""

    return str(value)


def _normalize_log_level(
    level: str | int,
) -> int:
    """Return a validated numeric logging level."""

    if isinstance(level, int):
        if level < 0:
            raise LogConfigurationError("Logging level must not be negative.")

        return level

    normalized = level.strip().upper()

    if not normalized:
        raise LogConfigurationError("Logging level must not be empty.")

    numeric_level = logging.getLevelNamesMapping().get(normalized)

    if numeric_level is None:
        raise LogConfigurationError(f"Unsupported logging level: {level}")

    return numeric_level


class JsonLogFormatter(logging.Formatter):
    """Render one Python log record as JSON."""

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        """Return a structured JSON log line."""

        payload: dict[str, object] = {
            "timestamp": _utc_timestamp(record.created),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key in _LOG_RECORD_ATTRIBUTES or key.startswith("_") or value is None:
                continue

            payload[key] = value

        if "request_id" not in payload:
            request_id = get_request_id()

            if request_id is not None:
                payload["request_id"] = request_id

        if record.exc_info is not None:
            payload["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)

        return json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            default=_json_default,
        )


class ConsoleLogFormatter(logging.Formatter):
    """Render readable logs with optional request context."""

    def format(
        self,
        record: logging.LogRecord,
    ) -> str:
        """Return one console-oriented log line."""

        output = super().format(record)

        request_id = getattr(
            record,
            "request_id",
            None,
        )

        if request_id is None:
            request_id = get_request_id()

        if request_id is None:
            return output

        return f"{output} request_id={request_id}"


def build_log_handler(
    *,
    environment: str,
    stream: TextIO | None = None,
) -> logging.StreamHandler[TextIO]:
    """Create a handler for one runtime environment."""

    handler = logging.StreamHandler(stream)

    if environment.strip().casefold() == "production":
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(
            ConsoleLogFormatter(
                ("%(asctime)s %(levelname)s %(name)s %(message)s"),
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )

    return handler


def configure_logging(
    *,
    environment: str,
    level: str | int = "INFO",
    stream: TextIO | None = None,
) -> None:
    """Configure application and Uvicorn logging."""

    numeric_level = _normalize_log_level(level)
    handler = build_log_handler(
        environment=environment,
        stream=stream,
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(numeric_level)

    for logger_name in _UVICORN_LOGGERS:
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.setLevel(numeric_level)
        uvicorn_logger.propagate = True


__all__ = [
    "ConsoleLogFormatter",
    "JsonLogFormatter",
    "LogConfigurationError",
    "build_log_handler",
    "configure_logging",
]
