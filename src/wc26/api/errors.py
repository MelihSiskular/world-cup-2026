"""Application-level API errors."""

from __future__ import annotations


class TransferAnalysisExecutionError(RuntimeError):
    """Raised when transfer analysis fails unexpectedly."""


class PlayerSearchExecutionError(RuntimeError):
    """Raised when player search fails unexpectedly."""


__all__ = [
    "PlayerSearchExecutionError",
    "TransferAnalysisExecutionError",
]
