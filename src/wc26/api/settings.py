"""Central runtime settings for the WC26 API."""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from wc26.analytics.transfer_intelligence.config import (
    DEFAULT_FEATURES,
    DEFAULT_HEATMAP_GRIDS,
    DEFAULT_HEATMAP_PROFILES,
    DEFAULT_HEATMAP_SIMILARITY,
    DEFAULT_PLAYER_TOURNAMENT_SUMMARY,
    DEFAULT_SIMILARITY,
)

type ApiEnvironment = str


class ApiSettingsError(ValueError):
    """Raised when API runtime settings are invalid."""


@dataclass(frozen=True, slots=True)
class TransferDatasetPaths:
    """Server-managed paths for transfer intelligence datasets."""

    features: Path = DEFAULT_FEATURES
    player_tournament_summary: Path = DEFAULT_PLAYER_TOURNAMENT_SUMMARY
    similarity: Path = DEFAULT_SIMILARITY
    heatmap_similarity: Path = DEFAULT_HEATMAP_SIMILARITY
    heatmap_profiles: Path = DEFAULT_HEATMAP_PROFILES
    heatmap_grids: Path = DEFAULT_HEATMAP_GRIDS


def _require_non_empty(
    value: str,
    *,
    setting_name: str,
) -> str:
    """Return stripped text or reject an empty setting."""

    result = value.strip()

    if not result:
        raise ApiSettingsError(f"{setting_name} must not be empty.")

    return result


def _parse_environment(
    value: str,
) -> ApiEnvironment:
    """Parse and validate the application environment."""

    normalized = value.strip().casefold()

    if normalized not in {
        "development",
        "test",
        "production",
    }:
        raise ApiSettingsError("WC26_ENVIRONMENT must be one of: development, test, production.")

    return normalized


def _parse_port(
    value: str,
    *,
    setting_name: str,
) -> int:
    """Parse and validate one configured server port."""

    try:
        port = int(value.strip())
    except ValueError as exception:
        raise ApiSettingsError(f"{setting_name} must be an integer.") from exception

    if not 1 <= port <= 65_535:
        raise ApiSettingsError(f"{setting_name} must be between 1 and 65535.")

    return port


def _parse_path(
    value: str,
    *,
    setting_name: str,
) -> Path:
    """Parse one configured filesystem path."""

    text = _require_non_empty(
        value,
        setting_name=setting_name,
    )

    return Path(text).expanduser()


def _normalize_cors_origin(
    value: str,
) -> str:
    """Validate and normalize one HTTP CORS origin."""

    origin = value.strip()

    if not origin:
        raise ApiSettingsError("CORS origins must not contain empty values.")

    parsed = urlsplit(origin)

    if parsed.scheme not in {
        "http",
        "https",
    }:
        raise ApiSettingsError("CORS origins must use http or https.")

    if not parsed.netloc:
        raise ApiSettingsError("CORS origins must include a hostname.")

    if parsed.path not in {
        "",
        "/",
    }:
        raise ApiSettingsError("CORS origins must not include a path.")

    if parsed.query or parsed.fragment:
        raise ApiSettingsError("CORS origins must not include query strings or fragments.")

    return f"{parsed.scheme.casefold()}://{parsed.netloc.rstrip('/')}"


def _normalize_cors_origins(
    values: Iterable[str],
) -> tuple[str, ...]:
    """Normalize and deduplicate CORS origins."""

    origins: list[str] = []
    seen: set[str] = set()

    for value in values:
        if not value.strip():
            continue

        origin = _normalize_cors_origin(value)

        if origin in seen:
            continue

        seen.add(origin)
        origins.append(origin)

    return tuple(origins)


def _read_text(
    environment: Mapping[str, str],
    key: str,
    default: str,
) -> str:
    """Read one non-empty text environment variable."""

    value = environment.get(key)

    if value is None:
        return default

    return _require_non_empty(
        value,
        setting_name=key,
    )


def _read_port(
    environment: Mapping[str, str],
    default: int,
) -> int:
    """Resolve the explicit WC26 port or a platform-provided port."""

    wc26_port = environment.get("WC26_API_PORT")

    if wc26_port is not None:
        return _parse_port(
            wc26_port,
            setting_name="WC26_API_PORT",
        )

    platform_port = environment.get("PORT")

    if platform_port is not None:
        return _parse_port(
            platform_port,
            setting_name="PORT",
        )

    return default


def _read_path(
    environment: Mapping[str, str],
    key: str,
    default: Path,
) -> Path:
    """Read one filesystem path environment variable."""

    value = environment.get(key)

    if value is None:
        return default

    return _parse_path(
        value,
        setting_name=key,
    )


@dataclass(frozen=True, slots=True)
class ApiSettings:
    """Validated runtime configuration for the WC26 API."""

    environment: ApiEnvironment = "development"
    host: str = "127.0.0.1"
    port: int = 8000

    title: str = "WC26 Transfer Intelligence API"
    summary: str = "Football recruitment intelligence powered by World Cup data."
    service_name: str = "wc26-transfer-intelligence"

    dataset_paths: TransferDatasetPaths = field(default_factory=TransferDatasetPaths)

    cors_origins: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate directly constructed settings."""

        object.__setattr__(
            self,
            "environment",
            _parse_environment(self.environment),
        )

        object.__setattr__(
            self,
            "host",
            _require_non_empty(
                self.host,
                setting_name="API host",
            ),
        )

        object.__setattr__(
            self,
            "title",
            _require_non_empty(
                self.title,
                setting_name="API title",
            ),
        )

        object.__setattr__(
            self,
            "summary",
            _require_non_empty(
                self.summary,
                setting_name="API summary",
            ),
        )

        object.__setattr__(
            self,
            "service_name",
            _require_non_empty(
                self.service_name,
                setting_name="service name",
            ),
        )

        if not 1 <= self.port <= 65_535:
            raise ApiSettingsError("API port must be between 1 and 65535.")

        object.__setattr__(
            self,
            "cors_origins",
            _normalize_cors_origins(self.cors_origins),
        )

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str] | None = None,
    ) -> ApiSettings:
        """Create settings from WC26 environment variables."""

        source = os.environ if environment is None else environment

        defaults = cls()

        environment_name = _parse_environment(
            _read_text(
                source,
                "WC26_ENVIRONMENT",
                defaults.environment,
            )
        )

        port = _read_port(
            source,
            defaults.port,
        )

        cors_value = source.get(
            "WC26_CORS_ORIGINS",
            "",
        )

        return cls(
            environment=environment_name,
            host=_read_text(
                source,
                "WC26_API_HOST",
                defaults.host,
            ),
            port=port,
            title=_read_text(
                source,
                "WC26_API_TITLE",
                defaults.title,
            ),
            summary=_read_text(
                source,
                "WC26_API_SUMMARY",
                defaults.summary,
            ),
            service_name=_read_text(
                source,
                "WC26_SERVICE_NAME",
                defaults.service_name,
            ),
            dataset_paths=TransferDatasetPaths(
                features=_read_path(
                    source,
                    "WC26_FEATURES_PATH",
                    defaults.dataset_paths.features,
                ),
                player_tournament_summary=_read_path(
                    source,
                    "WC26_PLAYER_TOURNAMENT_SUMMARY_PATH",
                    (defaults.dataset_paths.player_tournament_summary),
                ),
                similarity=_read_path(
                    source,
                    "WC26_SIMILARITY_PATH",
                    defaults.dataset_paths.similarity,
                ),
                heatmap_similarity=_read_path(
                    source,
                    "WC26_HEATMAP_SIMILARITY_PATH",
                    defaults.dataset_paths.heatmap_similarity,
                ),
                heatmap_profiles=_read_path(
                    source,
                    "WC26_HEATMAP_PROFILES_PATH",
                    defaults.dataset_paths.heatmap_profiles,
                ),
                heatmap_grids=_read_path(
                    source,
                    "WC26_HEATMAP_GRIDS_PATH",
                    defaults.dataset_paths.heatmap_grids,
                ),
            ),
            cors_origins=tuple(cors_value.split(",")),
        )


__all__ = [
    "ApiEnvironment",
    "ApiSettings",
    "ApiSettingsError",
    "TransferDatasetPaths",
]
