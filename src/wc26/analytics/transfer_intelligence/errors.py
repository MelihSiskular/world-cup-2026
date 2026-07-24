"""Domain-specific errors for Transfer Intelligence."""

from __future__ import annotations


class PlayerNotFoundError(ValueError):
    """Raised when no player matches the supplied query."""


class AmbiguousPlayerError(ValueError):
    """Raised when a player query matches multiple players."""


class DatasetNotFoundError(FileNotFoundError):
    """Raised when a required analytics dataset is unavailable."""


class InvalidDatasetError(ValueError):
    """Raised when a dataset does not satisfy its required contract."""


__all__ = [
    "AmbiguousPlayerError",
    "DatasetNotFoundError",
    "InvalidDatasetError",
    "PlayerNotFoundError",
]
