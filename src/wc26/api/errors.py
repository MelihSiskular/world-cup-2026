"""Application-level API errors."""

from __future__ import annotations


class TransferAnalysisExecutionError(RuntimeError):
    """Raised when transfer analysis fails unexpectedly."""


__all__ = [
    "TransferAnalysisExecutionError",
]
