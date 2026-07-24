"""ASGI application entrypoint."""

from __future__ import annotations

from wc26.api.app import create_app

app = create_app()


__all__ = [
    "app",
]
