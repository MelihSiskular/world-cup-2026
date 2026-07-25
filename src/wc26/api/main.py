"""ASGI entry point for the WC26 API."""

from fastapi import FastAPI

from wc26.analytics.transfer_intelligence.catalog import (
    load_transfer_data_catalog,
)
from wc26.api.app import create_app
from wc26.api.settings import ApiSettings


def create_production_app() -> FastAPI:
    """Create the API using process environment settings."""

    settings = ApiSettings.from_environment()

    return create_app(
        settings=settings,
        catalog_loader=load_transfer_data_catalog,
    )


app = create_production_app()


__all__ = [
    "app",
    "create_production_app",
]
