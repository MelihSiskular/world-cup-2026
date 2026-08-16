"""Tests for player-position normalization."""

from wc26.analytics.player_intelligence.metric_registry import (
    PositionGroup,
)
from wc26.analytics.player_intelligence.positions import (
    normalize_position_group,
)


def test_normalizes_enriched_dataset_position_codes() -> None:
    assert normalize_position_group("G") == PositionGroup.GOALKEEPER
    assert normalize_position_group("D") == PositionGroup.DEFENDER
    assert normalize_position_group("M") == PositionGroup.MIDFIELDER
    assert normalize_position_group("F") == PositionGroup.FORWARD


def test_position_normalization_is_case_and_whitespace_safe() -> None:
    assert normalize_position_group(" midfielder ") == PositionGroup.MIDFIELDER


def test_unknown_position_returns_none() -> None:
    assert normalize_position_group("UNKNOWN") is None
