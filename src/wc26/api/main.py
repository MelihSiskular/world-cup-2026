"""ASGI entry point for the WC26 API."""

from wc26.analytics.transfer_intelligence.catalog import (
    load_transfer_data_catalog,
)
from wc26.api.app import create_app

app = create_app(
    catalog_loader=load_transfer_data_catalog,
)


__all__ = [
    "app",
]
