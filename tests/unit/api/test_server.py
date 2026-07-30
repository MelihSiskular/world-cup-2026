"""Tests for the production API server launcher."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from wc26.api import server
from wc26.api.environment import RuntimeEnvironmentError
from wc26.api.settings import ApiSettings


def test_run_server_uses_explicit_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    uvicorn_run = Mock()
    settings = ApiSettings(
        host="0.0.0.0",
        port=9000,
    )
    validate_runtime_environment = Mock(return_value=settings)

    monkeypatch.setattr(server.uvicorn, "run", uvicorn_run)
    monkeypatch.setattr(
        server,
        "validate_runtime_environment",
        validate_runtime_environment,
    )

    server.run_server(settings)

    validate_runtime_environment.assert_called_once_with(settings)
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
    validated_settings: list[ApiSettings] = []

    def validate_runtime_environment(
        settings: ApiSettings,
    ) -> ApiSettings:
        validated_settings.append(settings)
        return settings

    monkeypatch.setattr(server.uvicorn, "run", uvicorn_run)
    monkeypatch.setattr(
        server,
        "validate_runtime_environment",
        validate_runtime_environment,
    )
    monkeypatch.setenv("WC26_API_HOST", "127.0.0.1")
    monkeypatch.setenv("WC26_API_PORT", "9100")

    server.run_server()

    assert len(validated_settings) == 1
    assert validated_settings[0].host == "127.0.0.1"
    assert validated_settings[0].port == 9100

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


def test_main_exits_when_runtime_environment_is_invalid(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run_server = Mock(
        side_effect=RuntimeEnvironmentError("missing runtime dataset")
    )

    monkeypatch.setattr(server, "run_server", run_server)

    with pytest.raises(SystemExit) as error:
        server.main()

    assert error.value.code == 1
    assert "WC26 API startup failed" in capsys.readouterr().err
