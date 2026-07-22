"""Project path discovery and local data directory definitions."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT_ENV = "WC26_PROJECT_ROOT"


class ProjectRootNotFoundError(RuntimeError):
    """Raised when the WC26 project root cannot be discovered."""


def find_project_root(start: str | Path | None = None) -> Path:
    """Find the nearest parent directory containing pyproject.toml.

    Resolution order:
    1. Explicit ``start`` argument
    2. WC26_PROJECT_ROOT environment variable
    3. Current working directory
    """
    configured_root = start or os.getenv(PROJECT_ROOT_ENV)
    search_start = (
        Path(configured_root).expanduser().resolve() if configured_root else Path.cwd().resolve()
    )

    if search_start.is_file():
        search_start = search_start.parent

    for candidate in (search_start, *search_start.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate

    raise ProjectRootNotFoundError(
        "WC26 project root could not be found. "
        f"Set {PROJECT_ROOT_ENV} or run the command inside the repository."
    )


@dataclass(frozen=True, slots=True)
class ProjectPaths:
    """Important local filesystem paths used by the analytics project."""

    root: Path
    data: Path
    raw_data: Path
    processed_data: Path
    docs: Path
    artifacts: Path

    @classmethod
    def discover(cls, root: str | Path | None = None) -> ProjectPaths:
        project_root = find_project_root(root)

        return cls(
            root=project_root,
            data=project_root / "data",
            raw_data=project_root / "data" / "raw",
            processed_data=project_root / "data" / "processed",
            docs=project_root / "docs",
            artifacts=project_root / "artifacts",
        )
