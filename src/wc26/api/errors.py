"""Application-level API errors."""

from __future__ import annotations


class TransferAnalysisExecutionError(RuntimeError):
    """Raised when transfer analysis fails unexpectedly."""


class PlayerSearchExecutionError(RuntimeError):
    """Raised when player search fails unexpectedly."""


class PlayerProfileExecutionError(RuntimeError):
    """Raised when player-profile retrieval fails unexpectedly."""


__all__ = [
    "PlayerProfileExecutionError",
    "PlayerSearchExecutionError",
    "TransferAnalysisExecutionError",
]
