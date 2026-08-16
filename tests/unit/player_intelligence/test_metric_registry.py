"""Tests for the player-intelligence metric registry."""

from __future__ import annotations

from wc26.analytics.player_intelligence.metric_registry import (
    METRIC_REGISTRY,
    MetricGroup,
    PositionGroup,
    get_metric_definition,
    metrics_for_group,
    metrics_for_position_group,
)


def test_registry_has_unique_public_keys() -> None:
    keys = [metric.key for metric in METRIC_REGISTRY]

    assert len(keys) == len(set(keys))


def test_registry_has_unique_source_columns() -> None:
    source_columns = [metric.source_column for metric in METRIC_REGISTRY]

    assert len(source_columns) == len(set(source_columns))


def test_midfield_registry_contains_creation_and_progression() -> None:
    metric_keys = {metric.key for metric in metrics_for_position_group(PositionGroup.MIDFIELDER)}

    assert "expected_assists_per90" in metric_keys
    assert "key_passes_per90" in metric_keys
    assert "total_progression_per90" in metric_keys
    assert "progressive_carries_per90" in metric_keys


def test_goalkeeper_registry_is_position_specific() -> None:
    metric_keys = {metric.key for metric in metrics_for_position_group(PositionGroup.GOALKEEPER)}

    assert "saves_per90" in metric_keys
    assert "goals_prevented_per90" in metric_keys

    assert "expected_assists_per90" not in metric_keys
    assert "expected_goals_per90" not in metric_keys


def test_possession_lost_uses_inverse_performance_direction() -> None:
    metric = get_metric_definition("possession_lost_per90")

    assert metric.higher_is_better is False


def test_creation_group_respects_position_context() -> None:
    midfielder_metrics = metrics_for_group(
        MetricGroup.CREATION,
        position_group=PositionGroup.MIDFIELDER,
    )

    goalkeeper_metrics = metrics_for_group(
        MetricGroup.CREATION,
        position_group=PositionGroup.GOALKEEPER,
    )

    assert midfielder_metrics
    assert goalkeeper_metrics == ()


def test_registry_order_is_deterministic() -> None:
    first_result = [metric.key for metric in metrics_for_position_group(PositionGroup.MIDFIELDER)]

    second_result = [metric.key for metric in metrics_for_position_group(PositionGroup.MIDFIELDER)]

    assert first_result == second_result
