"""Position normalization for player-intelligence analytics."""

from __future__ import annotations

from typing import Final

from wc26.analytics.player_intelligence.metric_registry import (
    PositionGroup,
)

POSITION_GROUP_ALIASES: Final[dict[str, PositionGroup]] = {
    "G": PositionGroup.GOALKEEPER,
    "GK": PositionGroup.GOALKEEPER,
    "GOALKEEPER": PositionGroup.GOALKEEPER,
    "D": PositionGroup.DEFENDER,
    "DEF": PositionGroup.DEFENDER,
    "DEFENDER": PositionGroup.DEFENDER,
    "M": PositionGroup.MIDFIELDER,
    "MID": PositionGroup.MIDFIELDER,
    "MIDFIELDER": PositionGroup.MIDFIELDER,
    "F": PositionGroup.FORWARD,
    "FW": PositionGroup.FORWARD,
    "FORWARD": PositionGroup.FORWARD,
}


def normalize_position_group(
    value: object,
) -> PositionGroup | None:
    """Normalize one dataset position into a semantic position group."""

    if value is None:
        return None

    normalized = str(value).strip().upper()

    if not normalized:
        return None

    return POSITION_GROUP_ALIASES.get(normalized)


__all__ = [
    "POSITION_GROUP_ALIASES",
    "normalize_position_group",
]
