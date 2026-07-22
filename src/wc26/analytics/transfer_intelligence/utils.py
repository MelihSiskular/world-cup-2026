"""General-purpose utilities for transfer intelligence."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

import pandas as pd


def slugify(text: str) -> str:
    """Convert text into a filesystem-safe lowercase slug."""
    normalized = unicodedata.normalize(
        "NFKD",
        str(text),
    )

    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")

    return (
        re.sub(
            r"[^a-zA-Z0-9]+",
            "_",
            ascii_text,
        )
        .strip("_")
        .lower()
    )


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:
    """Convert a value to float or return the configured default."""
    try:
        if value is None or pd.isna(value):
            return default

        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_text(value: Any) -> str:
    """Normalize nullable text for case-insensitive comparisons."""
    if value is None or pd.isna(value):
        return ""

    return str(value).strip().casefold()


__all__ = [
    "format_market_value",
    "format_optional_score",
    "normalize_text",
    "safe_float",
    "slugify",
]


def format_optional_score(
    value: Any,
) -> str:
    if value is None or pd.isna(value):
        return "N/A"

    return f"{float(value):.2f}"


def format_market_value(
    value: Any,
) -> str:
    if pd.isna(value):
        return "-"

    value = float(value)
    euro = "\u20ac"

    if value >= 1_000_000:
        return f"{euro}{value / 1_000_000:.1f}M"

    if value >= 1_000:
        return f"{euro}{value / 1_000:.0f}K"

    return f"{euro}{value:.0f}"
