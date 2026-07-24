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


class InvalidPlayerSearchError(ValueError):
    """Raised when player-search parameters are invalid."""


class InvalidPlayerProfileError(ValueError):
    """Raised when player-profile parameters are invalid."""


class InvalidTransferAnalysisRequestError(ValueError):
    """Raised when transfer-analysis target parameters are invalid."""


__all__ = [
    "AmbiguousPlayerError",
    "DatasetNotFoundError",
    "InvalidDatasetError",
    "InvalidPlayerProfileError",
    "InvalidPlayerSearchError",
    "InvalidTransferAnalysisRequestError",
    "PlayerNotFoundError",
]
