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


def _as_utc(
    timestamp: datetime,
    *,
    field_name: str,
) -> datetime:
    """Validate and normalize a timezone-aware timestamp."""

    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware.")

    return timestamp.astimezone(UTC)


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

        return self.transfer_data_catalog is not None and self.catalog_loaded_at is not None

    def mark_started(
        self,
        *,
        timestamp: datetime | None = None,
    ) -> None:
        """Record the current application startup time."""

        current = timestamp if timestamp is not None else datetime.now(UTC)

        self.started_at = _as_utc(
            current,
            field_name="Startup timestamp",
        )

    def attach_catalog(
        self,
        catalog: TransferDataCatalog,
        *,
        timestamp: datetime | None = None,
    ) -> None:
        """Attach a loaded transfer catalog to the runtime."""

        current = timestamp if timestamp is not None else datetime.now(UTC)

        self.transfer_data_catalog = catalog
        self.catalog_loaded_at = _as_utc(
            current,
            field_name="Catalog load timestamp",
        )

    def clear_catalog(self) -> None:
        """Release the loaded runtime catalog."""

        self.transfer_data_catalog = None
        self.catalog_loaded_at = None

    def uptime_seconds(
        self,
        *,
        timestamp: datetime | None = None,
    ) -> float:
        """Return elapsed seconds since application startup."""

        if self.started_at is None:
            raise RuntimeError("WC26 API runtime has not started.")

        current = timestamp if timestamp is not None else datetime.now(UTC)

        current_utc = _as_utc(
            current,
            field_name="Uptime timestamp",
        )

        elapsed = (current_utc - self.started_at).total_seconds()

        return round(
            max(
                0.0,
                elapsed,
            ),
            3,
        )


def get_api_runtime_state(
    request: Request,
) -> ApiRuntimeState:
    """Return the initialized API runtime state."""

    runtime = getattr(
        request.app.state,
        "api_runtime",
        None,
    )

    if not isinstance(
        runtime,
        ApiRuntimeState,
    ):
        raise RuntimeError("WC26 API runtime state is not initialized.")

    return runtime


__all__ = [
    "ApiRuntimeState",
    "get_api_runtime_state",
]
