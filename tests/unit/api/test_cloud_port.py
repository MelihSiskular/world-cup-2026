"""Tests for cloud platform API port resolution."""

from __future__ import annotations

import pytest

from wc26.api.settings import (
    ApiSettings,
    ApiSettingsError,
)


def test_settings_use_default_port_when_no_port_is_configured() -> None:
    settings = ApiSettings.from_environment({})

    assert settings.port == 8000


def test_settings_use_platform_port_as_fallback() -> None:
    settings = ApiSettings.from_environment(
        {
            "PORT": "8123",
        }
    )

    assert settings.port == 8123


def test_wc26_api_port_takes_precedence_over_platform_port() -> None:
    settings = ApiSettings.from_environment(
        {
            "WC26_API_PORT": "9100",
            "PORT": "8123",
        }
    )

    assert settings.port == 9100


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (
            "not-a-number",
            "PORT must be an integer",
        ),
        (
            "0",
            "PORT must be between",
        ),
        (
            "65536",
            "PORT must be between",
        ),
    ],
)
def test_settings_reject_invalid_platform_port(
    value: str,
    message: str,
) -> None:
    with pytest.raises(
        ApiSettingsError,
        match=message,
    ):
        ApiSettings.from_environment(
            {
                "PORT": value,
            }
        )


def test_invalid_wc26_port_is_not_hidden_by_valid_platform_port() -> None:
    with pytest.raises(
        ApiSettingsError,
        match="WC26_API_PORT must be an integer",
    ):
        ApiSettings.from_environment(
            {
                "WC26_API_PORT": "invalid",
                "PORT": "8123",
            }
        )
