"""Tests for dataset-backed player-discovery filters."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from wc26.analytics.transfer_intelligence.errors import (
    InvalidDatasetError,
)
from wc26.analytics.transfer_intelligence.models import (
    PlayerSearchFiltersRequest,
)
from wc26.analytics.transfer_intelligence.player_search import (
    get_player_search_filters,
    get_player_search_filters_from_dataframe,
)


def _features() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "player_id": 1,
                "player_name": "Alpha Defender",
                "national_team_name": "France",
                "country_name": "France",
                "position": "D",
                "final_role": "Left Wide Centre-Back",
                "archetype": "Ball-Carrying Defender",
                "spatial_role": "Left Centre-Back Lane",
                "age": 21.0,
                "market_value": 10_000_000.0,
                "market_value_currency": "EUR",
                "minutes": 300.0,
                "role_confidence_pct": 70.0,
                "data_reliability_score": 60.0,
                "player_quality_score": 75.0,
            },
            {
                "player_id": 2,
                "player_name": "Beta Defender",
                "national_team_name": "Spain",
                "country_name": "Spain",
                "position": "D",
                "final_role": "Safe Ball-Playing Centre-Back",
                "archetype": "Safe-Possession Defender",
                "spatial_role": "Central Build-Up Zone",
                "age": 24.0,
                "market_value": 30_000_000.0,
                "market_value_currency": "EUR",
                "minutes": 500.0,
                "role_confidence_pct": 85.0,
                "data_reliability_score": 80.0,
                "player_quality_score": 82.0,
            },
            {
                "player_id": 3,
                "player_name": "Gamma Forward",
                "national_team_name": "France",
                "country_name": "France",
                "position": "F",
                "final_role": "Poacher",
                "archetype": "Poacher",
                "spatial_role": "Central Striker Zone",
                "age": 29.0,
                "market_value": 50_000_000.0,
                "market_value_currency": "EUR",
                "minutes": 700.0,
                "role_confidence_pct": 90.0,
                "data_reliability_score": 88.0,
                "player_quality_score": 90.0,
            },
            {
                "player_id": 3,
                "player_name": "Gamma Forward",
                "national_team_name": "France",
                "country_name": "France",
                "position": "F",
                "final_role": "Poacher",
                "archetype": "Poacher",
                "spatial_role": "Central Striker Zone",
                "age": 29.0,
                "market_value": 50_000_000.0,
                "market_value_currency": "EUR",
                "minutes": 700.0,
                "role_confidence_pct": 90.0,
                "data_reliability_score": 88.0,
                "player_quality_score": 90.0,
            },
        ]
    )


def _summary() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "player_id": [
                1,
                2,
                3,
            ],
            "country_alpha3": [
                "FRA",
                "ESP",
                "FRA",
            ],
            "matches_played": [
                4,
                5,
                6,
            ],
            "starts": [
                3,
                5,
                6,
            ],
            "substitute_appearances": [
                1,
                0,
                0,
            ],
            "captain_appearances": [
                0,
                0,
                1,
            ],
            "total_minutes": [
                300.0,
                500.0,
                700.0,
            ],
            "formations_used": [
                1,
                1,
                2,
            ],
            "primary_formation": [
                "4-3-3",
                "4-2-3-1",
                "4-3-3",
            ],
            "primary_lineup_position": [
                "D",
                "D",
                "F",
            ],
            "player_primary_position": [
                "D",
                "D",
                "F",
            ],
        }
    )


def test_filter_metadata_uses_distinct_players_and_dataset_values() -> None:
    dataframe = _features()
    original = dataframe.copy(deep=True)

    result = get_player_search_filters_from_dataframe(
        dataframe,
        _summary(),
    )

    assert result.player_count == 3

    assert [
        (
            option.value,
            option.label,
            option.count,
        )
        for option in result.positions
    ] == [
        (
            "D",
            "Defender",
            2,
        ),
        (
            "F",
            "Forward",
            1,
        ),
    ]

    assert [
        (
            option.value,
            option.count,
        )
        for option in result.countries
    ] == [
        (
            "France",
            2,
        ),
        (
            "Spain",
            1,
        ),
    ]

    country_codes = {option.value: option.country_alpha3 for option in result.countries}

    assert country_codes == {
        "France": "FRA",
        "Spain": "ESP",
    }

    assert [option.value for option in result.archetypes] == [
        "Ball-Carrying Defender",
        "Poacher",
        "Safe-Possession Defender",
    ]

    assert [option.value for option in result.final_roles] == [
        "Left Wide Centre-Back",
        "Poacher",
        "Safe Ball-Playing Centre-Back",
    ]

    assert result.age.minimum == 21.0
    assert result.age.maximum == 29.0

    assert result.market_value.minimum == 10_000_000.0
    assert result.market_value.maximum == 50_000_000.0

    assert result.minutes.minimum == 300.0
    assert result.minutes.maximum == 700.0

    assert result.role_confidence.minimum == 70.0
    assert result.role_confidence.maximum == 90.0

    assert result.data_reliability.minimum == 60.0
    assert result.data_reliability.maximum == 88.0

    assert result.market_value_currency == "EUR"

    pd.testing.assert_frame_equal(
        dataframe,
        original,
    )


def test_filter_metadata_serializes_complete_contract() -> None:
    result = get_player_search_filters_from_dataframe(
        _features(),
        _summary(),
    )

    payload = result.to_dict()

    assert payload["player_count"] == 3
    assert payload["market_value_currency"] == "EUR"

    assert payload["age"] == {
        "minimum": 21.0,
        "maximum": 29.0,
    }

    assert payload["countries"] == [
        {
            "value": "France",
            "label": "France",
            "count": 2,
            "country_alpha3": "FRA",
        },
        {
            "value": "Spain",
            "label": "Spain",
            "count": 1,
            "country_alpha3": "ESP",
        },
    ]


def test_filter_metadata_loads_configured_datasets(
    tmp_path: Path,
) -> None:
    features_path = tmp_path / "features.csv"
    summary_path = tmp_path / "summary.csv"

    _features().to_csv(
        features_path,
        index=False,
    )
    _summary().to_csv(
        summary_path,
        index=False,
    )

    result = get_player_search_filters(
        PlayerSearchFiltersRequest(
            features=features_path,
            player_tournament_summary=summary_path,
        )
    )

    assert result.player_count == 3

    assert {option.country_alpha3 for option in result.countries} == {
        "FRA",
        "ESP",
    }


def test_filter_metadata_rejects_mixed_market_value_currencies() -> None:
    dataframe = _features()
    dataframe.loc[
        dataframe["player_id"] == 2,
        "market_value_currency",
    ] = "USD"

    with pytest.raises(
        InvalidDatasetError,
        match="one shared currency",
    ):
        get_player_search_filters_from_dataframe(dataframe)
