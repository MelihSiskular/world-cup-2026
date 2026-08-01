"""Production server launcher for the WC26 API."""

from __future__ import annotations

import os
import sys

import uvicorn

from wc26.api.environment import (
    RuntimeEnvironmentError,
    validate_runtime_environment,
)
from wc26.api.logging_config import (
    LogConfigurationError,
    configure_logging,
)
from wc26.api.settings import (
    ApiSettings,
    ApiSettingsError,
)

LOG_LEVEL_ENVIRONMENT_VARIABLE = "WC26_LOG_LEVEL"
DEFAULT_LOG_LEVEL = "INFO"


def run_server(
    settings: ApiSettings | None = None,
) -> None:
    """Run Uvicorn using validated runtime settings."""

    configured_settings = settings or ApiSettings.from_environment()
    runtime_settings = validate_runtime_environment(configured_settings)

    configure_logging(
        environment=(runtime_settings.environment),
        level=os.environ.get(
            LOG_LEVEL_ENVIRONMENT_VARIABLE,
            DEFAULT_LOG_LEVEL,
        ),
    )

    uvicorn.run(
        "wc26.api.main:app",
        host=runtime_settings.host,
        port=runtime_settings.port,
        reload=False,
        workers=1,
        access_log=False,
        log_config=None,
    )


def main() -> None:
    """Launch the production WC26 API server."""

    try:
        run_server()
    except (
        ApiSettingsError,
        LogConfigurationError,
        RuntimeEnvironmentError,
    ) as exc:
        print(
            f"WC26 API startup failed:\n{exc}",
            file=sys.stderr,
        )
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()


__all__ = [
    "DEFAULT_LOG_LEVEL",
    "LOG_LEVEL_ENVIRONMENT_VARIABLE",
    "main",
    "run_server",
]
