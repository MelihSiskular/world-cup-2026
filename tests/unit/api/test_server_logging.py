"""Tests for production server logging integration."""

from __future__ import annotations

import pytest

from wc26.api import server
from wc26.api.logging_config import (
    LogConfigurationError,
)
from wc26.api.settings import ApiSettings


def test_run_server_configures_logging_before_uvicorn(
    monkeypatch,
) -> None:
    settings = ApiSettings(
        environment="production",
        host="0.0.0.0",
        port=8123,
    )

    configured_logging: list[tuple[str, str | int]] = []
    uvicorn_calls: list[tuple[str, dict[str, object]]] = []

    def fake_validate(
        supplied_settings: ApiSettings,
    ) -> ApiSettings:
        return supplied_settings

    def fake_configure_logging(
        *,
        environment: str,
        level: str | int,
    ) -> None:
        configured_logging.append(
            (
                environment,
                level,
            )
        )

    def fake_uvicorn_run(
        application: str,
        **kwargs: object,
    ) -> None:
        uvicorn_calls.append(
            (
                application,
                kwargs,
            )
        )

    monkeypatch.setenv(
        "WC26_LOG_LEVEL",
        "WARNING",
    )
    monkeypatch.setattr(
        server,
        "validate_runtime_environment",
        fake_validate,
    )
    monkeypatch.setattr(
        server,
        "configure_logging",
        fake_configure_logging,
    )
    monkeypatch.setattr(
        server.uvicorn,
        "run",
        fake_uvicorn_run,
    )

    server.run_server(settings)

    assert configured_logging == [
        (
            "production",
            "WARNING",
        )
    ]

    assert uvicorn_calls == [
        (
            "wc26.api.main:app",
            {
                "host": "0.0.0.0",
                "port": 8123,
                "reload": False,
                "workers": 1,
                "access_log": False,
                "log_config": None,
            },
        )
    ]


def test_main_exits_for_invalid_logging_configuration(
    monkeypatch,
    capsys,
) -> None:
    def fail_run_server() -> None:
        raise LogConfigurationError("Unsupported logging level")

    monkeypatch.setattr(
        server,
        "run_server",
        fail_run_server,
    )

    with pytest.raises(SystemExit) as exception_info:
        server.main()

    assert exception_info.value.code == 1

    captured = capsys.readouterr()

    assert "WC26 API startup failed" in captured.err
    assert "Unsupported logging level" in captured.err
