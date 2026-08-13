from __future__ import annotations

import pandas as pd
import pytest

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

def _stub_candidate_pipeline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def attach_similarity_stub(
        frame: pd.DataFrame,
        target: pd.Series,
        similarity: pd.DataFrame,
    ) -> pd.DataFrame:
        del target, similarity

        result = frame.copy()
        result["statistical_similarity_pct"] = 80.0

        return result

    def attach_heatmap_similarity_stub(
        frame: pd.DataFrame,
        target: pd.Series,
        heatmap_similarity: pd.DataFrame,
        neutral_score: float,
    ) -> pd.DataFrame:
        del target, heatmap_similarity, neutral_score
        return frame.copy()

    def attach_heatmap_profiles_stub(
        frame: pd.DataFrame,
        target: pd.Series,
        heatmap_profiles: pd.DataFrame,
    ) -> tuple[pd.DataFrame, dict[str, float]]:
        del target, heatmap_profiles
        return frame.copy(), {}

    def constant_score(
        frame: pd.DataFrame,
        target: pd.Series,
    ) -> pd.Series:
        del target

        return pd.Series(
            80.0,
            index=frame.index,
            dtype=float,
        )

    monkeypatch.setattr(
        candidates,
        "attach_similarity",
        attach_similarity_stub,
    )

    monkeypatch.setattr(
        candidates,
        "attach_heatmap_similarity",
        attach_heatmap_similarity_stub,
    )

    monkeypatch.setattr(
        candidates,
        "attach_heatmap_profiles",
        attach_heatmap_profiles_stub,
    )

    for function_name in (
        "calculate_role_fit",
        "calculate_spatial_similarity",
        "calculate_market_value_advantage",
        "calculate_age_suitability",
    ):
        monkeypatch.setattr(
            candidates,
            function_name,
            constant_score,
        )


def _candidate_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "player_id": 1,
                "position": "M",
                "minutes": None,
                "appearances": None,
                "role_confidence_score": 90.0,
                "final_role": "Creator",
                "archetype": "Playmaker",
            },
            {
                "player_id": 2,
                "position": "M",
                "minutes": 0,
                "appearances": 0,
                "role_confidence_score": 90.0,
                "final_role": "Creator",
                "archetype": "Playmaker",
            },
            {
                "player_id": 3,
                "position": "M",
                "minutes": None,
                "appearances": 0,
                "role_confidence_score": 90.0,
                "final_role": "Creator",
                "archetype": "Playmaker",
            },
            {
                "player_id": 4,
                "position": "M",
                "minutes": 149,
                "appearances": None,
                "role_confidence_score": 90.0,
                "final_role": "Creator",
                "archetype": "Playmaker",
            },
            {
                "player_id": 5,
                "position": "M",
                "minutes": 150,
                "appearances": 0,
                "role_confidence_score": 90.0,
                "final_role": "Creator",
                "archetype": "Playmaker",
            },
            {
                "player_id": 6,
                "position": "M",
                "minutes": 300,
                "appearances": None,
                "role_confidence_score": 90.0,
                "final_role": "Creator",
                "archetype": "Playmaker",
            },
        ],
    )


def test_candidate_minimum_minutes_excludes_low_and_missing_samples(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_candidate_pipeline(monkeypatch)

    players = _candidate_fixture()
    target = players.iloc[0]

    result, target_heatmap_profile = (
        candidates.prepare_candidate_base(
            players=players,
            similarity=pd.DataFrame(),
            heatmap_similarity=pd.DataFrame(),
            heatmap_profiles=pd.DataFrame(),
            target=target,
            minimum_minutes=150.0,
            minimum_role_confidence=0.0,
            maximum_market_value=None,
            neutral_heatmap_score=70.0,
        )
    )

    assert result["player_id"].tolist() == [
        5,
        6,
    ]

    assert target_heatmap_profile == {}


def test_candidate_minutes_zero_remains_distinct_from_missing_minutes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_candidate_pipeline(monkeypatch)

    players = _candidate_fixture()
    target = players.iloc[0]

    result, _ = candidates.prepare_candidate_base(
        players=players,
        similarity=pd.DataFrame(),
        heatmap_similarity=pd.DataFrame(),
        heatmap_profiles=pd.DataFrame(),
        target=target,
        minimum_minutes=0.0,
        minimum_role_confidence=0.0,
        maximum_market_value=None,
        neutral_heatmap_score=70.0,
    )

    candidate_ids = set(
        result["player_id"].tolist(),
    )

    assert 2 in candidate_ids
    assert 3 not in candidate_ids

    assert candidate_ids == {
        2,
        4,
        5,
        6,
    }

def test_target_zero_minutes_does_not_apply_candidate_threshold_to_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_candidate_pipeline(monkeypatch)

    players = _candidate_fixture()

    target = players.loc[
        players["player_id"].eq(2)
    ].iloc[0]

    result, _ = candidates.prepare_candidate_base(
        players=players,
        similarity=pd.DataFrame(),
        heatmap_similarity=pd.DataFrame(),
        heatmap_profiles=pd.DataFrame(),
        target=target,
        minimum_minutes=150.0,
        minimum_role_confidence=0.0,
        maximum_market_value=None,
        neutral_heatmap_score=70.0,
    )

    assert target["minutes"] == 0

    assert result["player_id"].tolist() == [
        5,
        6,
    ]