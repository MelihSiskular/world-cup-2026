"""Tests for API request context and observability."""

from __future__ import annotations

import json
import logging
import re
from io import StringIO

from fastapi import FastAPI
from fastapi.testclient import TestClient

from wc26.api import create_app
from wc26.api.logging_config import (
    build_log_handler,
)
from wc26.api.request_context import (
    REQUEST_ID_HEADER,
    RequestObservabilityMiddleware,
    get_request_id,
    resolve_request_id,
)


def test_resolve_request_id_preserves_valid_value() -> None:
    assert resolve_request_id("client-request-123") == "client-request-123"


def test_resolve_request_id_replaces_invalid_value() -> None:
    resolved = resolve_request_id("invalid request id")

    assert re.fullmatch(
        r"[0-9a-f]{32}",
        resolved,
    )


def test_middleware_returns_supplied_request_id() -> None:
    application = create_app()

    with TestClient(application) as client:
        response = client.get(
            "/health",
            headers={
                REQUEST_ID_HEADER: ("test-request-123"),
            },
        )

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] == "test-request-123"


def test_middleware_generates_request_id() -> None:
    application = create_app()

    with TestClient(application) as client:
        response = client.get("/health")

    request_id = response.headers[REQUEST_ID_HEADER]

    assert re.fullmatch(
        r"[0-9a-f]{32}",
        request_id,
    )


def test_middleware_emits_completion_log(
    caplog,
) -> None:
    application = create_app()

    with caplog.at_level(
        logging.INFO,
        logger="wc26.api.request",
    ):
        with TestClient(application) as client:
            response = client.get(
                "/health",
                headers={
                    REQUEST_ID_HEADER: ("observability-test"),
                },
            )

    assert response.status_code == 200

    request_record = next(
        record
        for record in caplog.records
        if getattr(
            record,
            "event",
            None,
        )
        == "http.request.completed"
    )

    assert request_record.request_id == "observability-test"
    assert request_record.http_method == "GET"
    assert request_record.http_path == "/health"
    assert request_record.status_code == 200
    assert request_record.duration_ms >= 0

    assert get_request_id() is None


def test_route_logs_inherit_request_id() -> None:
    stream = StringIO()
    handler = build_log_handler(
        environment="production",
        stream=stream,
    )

    route_logger = logging.Logger(
        "wc26.api.route-test",
        level=logging.INFO,
    )
    route_logger.addHandler(handler)
    route_logger.propagate = False

    application = FastAPI()
    application.add_middleware(RequestObservabilityMiddleware)

    @application.get("/route-log")
    def route_log() -> dict[str, bool]:
        route_logger.info(
            "Route log emitted",
            extra={
                "event": "route.logged",
            },
        )

        return {
            "ok": True,
        }

    with TestClient(application) as client:
        response = client.get(
            "/route-log",
            headers={
                REQUEST_ID_HEADER: ("route-request-456"),
            },
        )

    assert response.status_code == 200

    document = json.loads(stream.getvalue().strip())

    assert document["event"] == "route.logged"
    assert document["request_id"] == "route-request-456"
