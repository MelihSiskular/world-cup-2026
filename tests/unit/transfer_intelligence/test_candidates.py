from __future__ import annotations

from wc26.analytics.transfer_intelligence import candidates
from wc26.analytics.transfer_intelligence.matching import (
    attach_heatmap_profiles,
    attach_heatmap_similarity,
    attach_similarity,
)
from wc26.analytics.transfer_intelligence.scoring import (
    calculate_age_suitability,
    calculate_market_value_advantage,
    calculate_role_fit,
    calculate_spatial_similarity,
)


def test_candidate_pipeline_uses_matching_functions() -> None:
    assert candidates.attach_similarity is attach_similarity
    assert candidates.attach_heatmap_similarity is attach_heatmap_similarity
    assert candidates.attach_heatmap_profiles is attach_heatmap_profiles


def test_candidate_pipeline_uses_scoring_functions() -> None:
    assert candidates.calculate_role_fit is calculate_role_fit
    assert candidates.calculate_spatial_similarity is calculate_spatial_similarity
    assert candidates.calculate_market_value_advantage is calculate_market_value_advantage
    assert candidates.calculate_age_suitability is calculate_age_suitability
