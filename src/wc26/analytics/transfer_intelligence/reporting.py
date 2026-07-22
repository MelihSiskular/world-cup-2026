"""Console reporting for transfer intelligence results."""

from __future__ import annotations

import pandas as pd

from wc26.analytics.transfer_intelligence.utils import (
    format_market_value,
    format_optional_score,
)


def print_report(
    target: pd.Series,
    results: dict[str, pd.DataFrame],
    top_n: int,
) -> None:
    print("=" * 120)
    print("FOOTBALL SCOUTING DECISION ENGINE V4")
    print("=" * 120)
    print()
    print(f"Target Player:  {target['player_name']}")
    print(f"Position:       {target['position']}")
    print(f"Archetype:      {target['archetype']}")
    print(f"Final Role:     {target['final_role']}")
    print(f"Age:            {target['age']}")
    print(f"Market Value:   {format_market_value(target['market_value'])}")

    titles = {
        "immediate": ("IMMEDIATE REPLACEMENTS"),
        "development": ("DEVELOPMENT PROSPECTS"),
        "value": ("BEST VALUE OPTIONS"),
        "short_term": ("SHORT-TERM EXPERIENCED OPTIONS"),
    }

    for mode, title in titles.items():
        print()
        print(title)
        print("-" * 120)

        result = results[mode]

        if result.empty:
            print("No eligible candidates.")
            continue

        columns = [
            f"{mode}_rank",
            "player_name",
            "national_team_name",
            "age",
            "market_value",
            "final_role",
            "statistical_similarity_pct",
            "role_fit_pct",
            "spatial_similarity_pct",
            "heatmap_similarity_score_pct",
            "occupation_overlap_pct",
            f"{mode}_score",
            "recommendation_type",
            "why_recommended",
        ]

        display = result.head(top_n)[columns].rename(
            columns={
                "national_team_name": "team",
                "statistical_similarity_pct": ("stat_sim"),
                "spatial_similarity_pct": ("spatial_sim"),
                "heatmap_similarity_score_pct": "heatmap_sim",
                "occupation_overlap_pct": ("heatmap_overlap"),
                f"{mode}_score": ("decision_score"),
            }
        )

        formatters = {
            "age": lambda value: f"{value:.1f}",
            "market_value": format_market_value,
            "stat_sim": format_optional_score,
            "role_fit_pct": format_optional_score,
            "spatial_sim": format_optional_score,
            "heatmap_sim": format_optional_score,
            "heatmap_overlap": format_optional_score,
            "decision_score": format_optional_score,
        }

        print(
            display.to_string(
                index=False,
                formatters=formatters,
            )
        )


__all__ = [
    "print_report",
]
