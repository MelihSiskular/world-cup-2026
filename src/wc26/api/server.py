"""Production server launcher for the WC26 API."""

from __future__ import annotations

import uvicorn

from wc26.api.settings import ApiSettings


def run_server(settings: ApiSettings | None = None) -> None:
    """Run the production ASGI server using validated runtime settings."""

    runtime_settings = settings or ApiSettings.from_environment()

    uvicorn.run(
        "wc26.api.main:app",
        host=runtime_settings.host,
        port=runtime_settings.port,
        reload=False,
        workers=1,
    )


def main() -> None:
    """Launch the production WC26 API server."""

    run_server()


if __name__ == "__main__":
    main()


__all__ = [
    "main",
    "run_server",
]
