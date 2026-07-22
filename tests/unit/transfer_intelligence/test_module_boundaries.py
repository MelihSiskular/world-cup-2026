from __future__ import annotations

from pathlib import Path

import pytest
from src.transfer_intelligence import find_replacements as legacy

from wc26.analytics.transfer_intelligence.config import (
    DEFAULT_FEATURES,
    HEATMAP_METRIC_COLUMNS,
    MODE_CONFIG,
)
from wc26.analytics.transfer_intelligence.utils import (
    normalize_text,
    safe_float,
    slugify,
)


def test_legacy_module_reexports_utility_functions() -> None:
    assert legacy.slugify is slugify
    assert legacy.safe_float is safe_float
    assert legacy.normalize_text is normalize_text


def test_legacy_module_reexports_configuration() -> None:
    assert legacy.MODE_CONFIG is MODE_CONFIG
    assert legacy.DEFAULT_FEATURES is DEFAULT_FEATURES
    assert legacy.HEATMAP_METRIC_COLUMNS is HEATMAP_METRIC_COLUMNS


@pytest.mark.parametrize("mode", MODE_CONFIG)
def test_mode_weights_sum_to_one(mode: str) -> None:
    weights = MODE_CONFIG[mode]["weights"]

    assert isinstance(weights, dict)
    assert sum(weights.values()) == pytest.approx(1.0)


def test_default_features_is_a_relative_path() -> None:
    assert isinstance(DEFAULT_FEATURES, Path)
    assert not DEFAULT_FEATURES.is_absolute()
