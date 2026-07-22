from __future__ import annotations

from pathlib import Path

import pytest
from src.transfer_intelligence import find_replacements as legacy

from wc26.analytics.transfer_intelligence.config import (
    DEFAULT_FEATURES,
    HEATMAP_METRIC_COLUMNS,
    MODE_CONFIG,
)
from wc26.analytics.transfer_intelligence.datasets import (
    load_heatmap_profiles,
    load_heatmap_similarity,
    load_similarity,
)
from wc26.analytics.transfer_intelligence.matching import (
    attach_heatmap_profiles,
    attach_heatmap_similarity,
    attach_similarity,
    resolve_player,
)
from wc26.analytics.transfer_intelligence.scoring import (
    calculate_age_suitability,
    calculate_market_value_advantage,
    calculate_mode_score,
    calculate_role_fit,
    calculate_spatial_similarity,
    same_value_score,
)
from wc26.analytics.transfer_intelligence.utils import (
    format_market_value,
    format_optional_score,
    normalize_text,
    safe_float,
    slugify,
)


def test_legacy_module_reexports_scoring_functions() -> None:
    assert legacy.same_value_score is same_value_score
    assert legacy.calculate_role_fit is calculate_role_fit
    assert legacy.calculate_spatial_similarity is calculate_spatial_similarity
    assert legacy.calculate_market_value_advantage is calculate_market_value_advantage
    assert legacy.calculate_age_suitability is calculate_age_suitability
    assert legacy.calculate_mode_score is calculate_mode_score


def test_legacy_module_reexports_matching_functions() -> None:
    assert legacy.resolve_player is resolve_player
    assert legacy.attach_similarity is attach_similarity
    assert legacy.attach_heatmap_similarity is attach_heatmap_similarity
    assert legacy.attach_heatmap_profiles is attach_heatmap_profiles


def test_legacy_module_reexports_dataset_loaders() -> None:
    assert legacy.load_similarity is load_similarity
    assert legacy.load_heatmap_similarity is load_heatmap_similarity
    assert legacy.load_heatmap_profiles is load_heatmap_profiles


def test_legacy_module_reexports_utility_functions() -> None:
    assert legacy.slugify is slugify
    assert legacy.safe_float is safe_float
    assert legacy.normalize_text is normalize_text
    assert legacy.format_optional_score is format_optional_score
    assert legacy.format_market_value is format_market_value


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
