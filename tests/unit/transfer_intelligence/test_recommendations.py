from __future__ import annotations

import pandas as pd
import pytest

from wc26.analytics.transfer_intelligence.config import (
    MODE_CONFIG,
)
from wc26.analytics.transfer_intelligence.recommendations import (
    filter_for_mode,
)


def candidate_row(
    player_id: int,
    *,
    age: float = 25.0,
    statistical_similarity_pct: float = 100.0,
    role_fit_pct: float = 100.0,
    player_quality_score: float = 100.0,
    data_reliability_score: float = 100.0,
) -> dict[str, float | int]:
    return {
        "player_id": player_id,
        "age": age,
        "statistical_similarity_pct": (statistical_similarity_pct),
        "role_fit_pct": role_fit_pct,
        "player_quality_score": player_quality_score,
        "data_reliability_score": data_reliability_score,
    }


@pytest.mark.parametrize(
    ("column", "threshold"),
    [
        (
            "statistical_similarity_pct",
            MODE_CONFIG["immediate"]["minimum_similarity"],
        ),
        (
            "role_fit_pct",
            MODE_CONFIG["immediate"]["minimum_role_fit"],
        ),
        (
            "player_quality_score",
            MODE_CONFIG["immediate"]["minimum_quality"],
        ),
        (
            "data_reliability_score",
            MODE_CONFIG["immediate"]["minimum_reliability"],
        ),
    ],
)
def test_filter_for_mode_rejects_scores_below_threshold(
    column: str,
    threshold: float,
) -> None:
    valid = candidate_row(
        1,
        age=25.0,
    )
    invalid = candidate_row(
        2,
        age=25.0,
    )
    invalid[column] = threshold - 0.01

    candidates = pd.DataFrame(
        [
            valid,
            invalid,
        ]
    )

    result = filter_for_mode(
        candidates,
        mode="immediate",
    )

    assert result["player_id"].tolist() == [1]


@pytest.mark.parametrize(
    "mode",
    [
        "immediate",
        "development",
    ],
)
def test_filter_for_mode_applies_maximum_age(
    mode: str,
) -> None:
    maximum_age = MODE_CONFIG[mode]["maximum_age"]

    assert maximum_age is not None

    candidates = pd.DataFrame(
        [
            candidate_row(
                1,
                age=maximum_age,
            ),
            candidate_row(
                2,
                age=maximum_age + 1,
            ),
        ]
    )

    result = filter_for_mode(
        candidates,
        mode=mode,
    )

    assert result["player_id"].tolist() == [1]


def test_filter_for_mode_applies_minimum_age() -> None:
    minimum_age = MODE_CONFIG["short_term"]["minimum_age"]

    assert minimum_age is not None

    candidates = pd.DataFrame(
        [
            candidate_row(
                1,
                age=minimum_age,
            ),
            candidate_row(
                2,
                age=minimum_age - 1,
            ),
        ]
    )

    result = filter_for_mode(
        candidates,
        mode="short_term",
    )

    assert result["player_id"].tolist() == [1]


def test_value_mode_does_not_filter_by_age() -> None:
    config = MODE_CONFIG["value"]

    assert config["minimum_age"] is None
    assert config["maximum_age"] is None

    candidates = pd.DataFrame(
        [
            candidate_row(
                1,
                age=18.0,
            ),
            candidate_row(
                2,
                age=40.0,
            ),
        ]
    )

    result = filter_for_mode(
        candidates,
        mode="value",
    )

    assert result["player_id"].tolist() == [1, 2]
