"""Tests for structured API error observability."""

from __future__ import annotations

import logging

import pytest
from fastapi.testclient import TestClient

from wc26.analytics.transfer_intelligence.errors import (
    DatasetNotFoundError,
    InvalidTransferAnalysisRequestError,
)
from wc26.analytics.transfer_intelligence.models import (
    TransferAnalysisRequest,
    TransferAnalysisResult,
)
from wc26.api import create_app
from wc26.api.dependencies import (
    TransferAnalysisRunner,
    get_transfer_analysis_runner,
)

REQUEST_PATH = "/api/v1/transfer-intelligence/analyze"


def _request_payload() -> dict[str, object]:
    """Return a valid transfer-analysis payload."""

    return {
        "player": "Michael Olise",
    }


def _error_records(
    caplog: pytest.LogCaptureFixture,
) -> list[logging.LogRecord]:
    """Return structured API error records."""

    return [record for record in caplog.records if record.name == "wc26.api.error"]


def _override_runner(
    application,
    error: Exception,
) -> None:
    """Configure an analysis runner that raises an error."""

    def failing_runner(
        request: TransferAnalysisRequest,
    ) -> TransferAnalysisResult:
        del request
        raise error

    def override_runner() -> TransferAnalysisRunner:
        return failing_runner

    application.dependency_overrides[get_transfer_analysis_runner] = override_runner


def test_client_error_log_contains_request_context(
    caplog: pytest.LogCaptureFixture,
) -> None:
    application = create_app()

    _override_runner(
        application,
        InvalidTransferAnalysisRequestError("Provide exactly one target."),
    )

    with caplog.at_level(
        logging.WARNING,
        logger="wc26.api.error",
    ):
        with TestClient(application) as client:
            response = client.post(
                REQUEST_PATH,
                json=_request_payload(),
                headers={
                    "X-Request-ID": ("client-error-001"),
                },
            )

    assert response.status_code == 400

    records = _error_records(caplog)
    assert len(records) == 1

    record = records[0]

    assert record.event == "api.error.client"
    assert record.request_id == "client-error-001"
    assert record.http_method == "POST"
    assert record.http_path == REQUEST_PATH
    assert record.status_code == 400
    assert record.error_code == ("invalid_transfer_analysis_request")
    assert record.exception_type == ("InvalidTransferAnalysisRequestError")
    assert record.levelno == logging.WARNING


def test_dependency_error_log_contains_request_context(
    caplog: pytest.LogCaptureFixture,
) -> None:
    application = create_app()

    _override_runner(
        application,
        DatasetNotFoundError("Private dataset path"),
    )

    with caplog.at_level(
        logging.ERROR,
        logger="wc26.api.error",
    ):
        with TestClient(application) as client:
            response = client.post(
                REQUEST_PATH,
                json=_request_payload(),
                headers={
                    "X-Request-ID": ("dependency-error-001"),
                },
            )

    assert response.status_code == 503
    assert "Private dataset path" not in response.text

    records = _error_records(caplog)
    assert len(records) == 1

    record = records[0]

    assert record.event == "api.error.dependency"
    assert record.request_id == "dependency-error-001"
    assert record.status_code == 503
    assert record.error_code == "dataset_unavailable"
    assert record.exception_type == "DatasetNotFoundError"
    assert record.levelno == logging.ERROR


def test_internal_error_log_uses_wrapped_cause(
    caplog: pytest.LogCaptureFixture,
) -> None:
    application = create_app()

    _override_runner(
        application,
        RuntimeError("sensitive internal failure"),
    )

    with caplog.at_level(
        logging.ERROR,
        logger="wc26.api.error",
    ):
        with TestClient(application) as client:
            response = client.post(
                REQUEST_PATH,
                json=_request_payload(),
                headers={
                    "X-Request-ID": ("internal-error-001"),
                },
            )

    assert response.status_code == 500
    assert "sensitive internal failure" not in response.text

    records = _error_records(caplog)
    assert len(records) == 1

    record = records[0]

    assert record.event == "api.error.internal"
    assert record.request_id == "internal-error-001"
    assert record.http_method == "POST"
    assert record.http_path == REQUEST_PATH
    assert record.status_code == 500
    assert record.error_code == "analysis_failed"
    assert record.exception_type == "TransferAnalysisExecutionError"
    assert record.cause_type == "RuntimeError"
    assert record.levelno == logging.ERROR
    assert record.exc_info is not None
