"""Typed runtime state for the WC26 API."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import Request

from wc26.analytics.transfer_intelligence.catalog import (
    TransferDataCatalog,
)
from wc26.api.settings import (
    ApiSettings,
    TransferDatasetPaths,
)


@dataclass(slots=True)
class ApiRuntimeState:
    """Mutable lifecycle state shared by API components."""

    settings: ApiSettings
    started_at: datetime | None = None
    catalog_loaded_at: datetime | None = None
    transfer_data_catalog: TransferDataCatalog | None = None

    @property
    def dataset_paths(self) -> TransferDatasetPaths:
        """Return the configured transfer dataset paths."""

        return self.settings.dataset_paths

    @property
    def is_ready(self) -> bool:
        """Return whether the runtime catalog is available."""

        return self.transfer_data_catalog is not None

    def mark_started(
        self,
        *,
        timestamp: datetime | None = None,
    ) -> None:
        """Record the current application startup time."""

        self.started_at = timestamp if timestamp is not None else datetime.now(UTC)

    def attach_catalog(
        self,
        catalog: TransferDataCatalog,
        *,
        timestamp: datetime | None = None,
    ) -> None:
        """Attach a loaded transfer catalog to the runtime."""

        self.transfer_data_catalog = catalog
        self.catalog_loaded_at = timestamp if timestamp is not None else datetime.now(UTC)

    def clear_catalog(self) -> None:
        """Release the loaded runtime catalog."""

        self.transfer_data_catalog = None
        self.catalog_loaded_at = None


def get_api_runtime_state(
    request: Request,
) -> ApiRuntimeState:
    """Return the initialized API runtime state."""

    runtime = getattr(
        request.app.state,
        "api_runtime",
        None,
    )

    if not isinstance(runtime, ApiRuntimeState):
        raise RuntimeError("WC26 API runtime state is not initialized.")

    return runtime


__all__ = [
    "ApiRuntimeState",
    "get_api_runtime_state",
]
