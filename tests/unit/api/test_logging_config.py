"""Tests for WC26 API logging configuration."""

from __future__ import annotations

import json
import logging
import sys
from io import StringIO
from typing import Any

import pytest

from wc26.api.logging_config import (
    JsonLogFormatter,
    LogConfigurationError,
    build_log_handler,
    configure_logging,
)


def _log_document(
    stream: StringIO,
) -> dict[str, Any]:
    """Read one structured log line."""

    return json.loads(stream.getvalue().strip())


def test_json_formatter_renders_structured_fields() -> None:
    record = logging.LogRecord(
        name="wc26.api.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Catalog loaded for %s",
        args=("production",),
        exc_info=None,
    )

    record.event = "catalog.loaded"
    record.player_count = 1248

    document = json.loads(JsonLogFormatter().format(record))

    assert document["level"] == "INFO"
    assert document["logger"] == "wc26.api.test"
    assert document["message"] == "Catalog loaded for production"
    assert document["event"] == "catalog.loaded"
    assert document["player_count"] == 1248
    assert document["timestamp"].endswith("Z")

    assert "args" not in document
    assert "pathname" not in document
    assert "lineno" not in document


def test_json_formatter_renders_exception() -> None:
    try:
        raise RuntimeError("catalog failure")
    except RuntimeError:
        record = logging.LogRecord(
            name="wc26.api.test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=20,
            msg="Catalog loading failed",
            args=(),
            exc_info=sys.exc_info(),
        )

    document = json.loads(JsonLogFormatter().format(record))

    assert document["level"] == "ERROR"
    assert document["message"] == "Catalog loading failed"
    assert "RuntimeError: catalog failure" in document["exception"]


def test_production_handler_outputs_json() -> None:
    stream = StringIO()
    handler = build_log_handler(
        environment="production",
        stream=stream,
    )

    logger = logging.Logger(
        "wc26.api.production-test",
        level=logging.INFO,
    )
    logger.addHandler(handler)
    logger.propagate = False

    logger.info(
        "Production log",
        extra={
            "event": "test.production",
        },
    )

    document = _log_document(stream)

    assert document["level"] == "INFO"
    assert document["event"] == "test.production"


def test_development_handler_outputs_console_text() -> None:
    stream = StringIO()
    handler = build_log_handler(
        environment="development",
        stream=stream,
    )

    logger = logging.Logger(
        "wc26.api.development-test",
        level=logging.INFO,
    )
    logger.addHandler(handler)
    logger.propagate = False

    logger.info("Development log")

    output = stream.getvalue()

    assert "INFO" in output
    assert "wc26.api.development-test" in output
    assert "Development log" in output
    assert not output.lstrip().startswith("{")


def test_configure_logging_sets_structured_root_logger() -> None:
    stream = StringIO()
    root_logger = logging.getLogger()

    original_handlers = list(root_logger.handlers)
    original_level = root_logger.level

    logger_names = (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "wc26.api.configuration-test",
    )
    logger_states = {
        name: (
            list(logging.getLogger(name).handlers),
            logging.getLogger(name).level,
            logging.getLogger(name).propagate,
        )
        for name in logger_names
    }

    try:
        configure_logging(
            environment="production",
            level="WARNING",
            stream=stream,
        )

        logger = logging.getLogger("wc26.api.configuration-test")
        logger.warning(
            "Configured warning",
            extra={
                "event": ("logging.configured"),
            },
        )
    finally:
        root_logger.handlers.clear()
        root_logger.handlers.extend(original_handlers)
        root_logger.setLevel(original_level)

        for (
            logger_name,
            state,
        ) in logger_states.items():
            logger = logging.getLogger(logger_name)
            handlers, level, propagate = state

            logger.handlers.clear()
            logger.handlers.extend(handlers)
            logger.setLevel(level)
            logger.propagate = propagate

    document = _log_document(stream)

    assert document["level"] == "WARNING"
    assert document["event"] == "logging.configured"


@pytest.mark.parametrize(
    "level",
    [
        "",
        "verbose",
        -1,
    ],
)
def test_configure_logging_rejects_invalid_level(
    level: str | int,
) -> None:
    with pytest.raises(LogConfigurationError):
        configure_logging(
            environment="production",
            level=level,
        )
