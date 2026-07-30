"""Tests for the production API server launcher."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from wc26.api import server
from wc26.api.settings import ApiSettings


def test_run_server_uses_explicit_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    uvicorn_run = Mock()

    monkeypatch.setattr(server.uvicorn, "run", uvicorn_run)

    settings = ApiSettings(
        host="0.0.0.0",
        port=9000,
    )

    server.run_server(settings)

    uvicorn_run.assert_called_once_with(
        "wc26.api.main:app",
        host="0.0.0.0",
        port=9000,
        reload=False,
        workers=1,
    )


def test_run_server_reads_environment_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    uvicorn_run = Mock()

    monkeypatch.setattr(server.uvicorn, "run", uvicorn_run)
    monkeypatch.setenv("WC26_API_HOST", "127.0.0.1")
    monkeypatch.setenv("WC26_API_PORT", "9100")

    server.run_server()

    uvicorn_run.assert_called_once_with(
        "wc26.api.main:app",
        host="127.0.0.1",
        port=9100,
        reload=False,
        workers=1,
    )


def test_main_delegates_to_run_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run_server = Mock()

    monkeypatch.setattr(server, "run_server", run_server)

    server.main()

    run_server.assert_called_once_with()
