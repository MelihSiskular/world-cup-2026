"""Production server launcher for the WC26 API."""

from __future__ import annotations

import sys

import uvicorn

from wc26.api.environment import (
    RuntimeEnvironmentError,
    validate_runtime_environment,
)
from wc26.api.settings import ApiSettings, ApiSettingsError


def run_server(settings: ApiSettings | None = None) -> None:
    """Run the production ASGI server using validated runtime settings."""

    configured_settings = settings or ApiSettings.from_environment()
    runtime_settings = validate_runtime_environment(configured_settings)

    uvicorn.run(
        "wc26.api.main:app",
        host=runtime_settings.host,
        port=runtime_settings.port,
        reload=False,
        workers=1,
    )


def main() -> None:
    """Launch the production WC26 API server."""

    try:
        run_server()
    except (ApiSettingsError, RuntimeEnvironmentError) as exc:
        print(f"WC26 API startup failed:\n{exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()


__all__ = [
    "main",
    "run_server",
]
