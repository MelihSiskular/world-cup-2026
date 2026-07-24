"""Player resolution and dataset matching utilities."""

from __future__ import annotations

from typing import cast

import numpy as np
import pandas as pd

from wc26.analytics.transfer_intelligence.errors import (
    AmbiguousPlayerError,
    PlayerNotFoundError,
)


def resolve_player(
    players: pd.DataFrame,
    query: str,
) -> pd.Series:
    exact = players[players["player_name"].astype(str).str.casefold().eq(query.casefold())]

    if len(exact) == 1:
        return exact.iloc[0]

    partial = players[
        players["player_name"]
        .astype(str)
        .str.contains(
            query,
            case=False,
            regex=False,
            na=False,
        )
    ]

    if len(partial) == 1:
        return partial.iloc[0]

    if partial.empty:
        raise PlayerNotFoundError(f"Player not found: {query}")

    matches = partial["player_name"].drop_duplicates().head(20).tolist()

    raise AmbiguousPlayerError("Multiple players matched: " + ", ".join(matches))


def attach_similarity(
    candidates: pd.DataFrame,
    target: pd.Series,
    similarity: pd.DataFrame,
) -> pd.DataFrame:
    direct = similarity[similarity["source_player_id"].eq(target["player_id"])][
        [
            "target_player_id",
            "overall_similarity_pct",
        ]
    ].rename(
        columns={
            "target_player_id": "player_id",
            "overall_similarity_pct": ("statistical_similarity_pct"),
        }
    )

    reverse = similarity[similarity["target_player_id"].eq(target["player_id"])][
        [
            "source_player_id",
            "overall_similarity_pct",
        ]
    ].rename(
        columns={
            "source_player_id": "player_id",
            "overall_similarity_pct": ("statistical_similarity_pct"),
        }
    )

    pairwise = (
        pd.concat(
            [direct, reverse],
            ignore_index=True,
        )
        .sort_values(
            "statistical_similarity_pct",
            ascending=False,
        )
        .drop_duplicates(
            "player_id",
            keep="first",
        )
    )

    return candidates.merge(
        pairwise,
        on="player_id",
        how="left",
    )


def attach_heatmap_similarity(
    candidates: pd.DataFrame,
    target: pd.Series,
    heatmap_similarity: pd.DataFrame,
    neutral_score: float,
) -> pd.DataFrame:
    """
    Attach genuine target-to-candidate heatmap metrics.

    heatmap_similarity_score_pct:
        Real measured heatmap similarity. Remains NaN when unavailable.

    effective_heatmap_score_pct:
        Score used by the decision engine. Missing values receive the
        configured neutral score.
    """
    target_id = int(target["player_id"])

    direct = heatmap_similarity[heatmap_similarity["target_player_id"].eq(target_id)].copy()

    if not direct.empty:
        direct = direct.rename(
            columns={
                "candidate_player_id": "player_id",
            }
        )

        direct = direct.drop(
            columns=["target_player_id"],
            errors="ignore",
        )

    reverse = heatmap_similarity[heatmap_similarity["candidate_player_id"].eq(target_id)].copy()

    if not reverse.empty:
        reverse = reverse.rename(
            columns={
                "target_player_id": "player_id",
                "candidate_matches_with_heatmap": ("target_matches_with_heatmap"),
                "target_matches_with_heatmap": ("candidate_matches_with_heatmap"),
                "candidate_heatmap_points": ("target_heatmap_points"),
                "target_heatmap_points": ("candidate_heatmap_points"),
            }
        )

        reverse = reverse.drop(
            columns=["candidate_player_id"],
            errors="ignore",
        )

    pairwise = pd.concat(
        [direct, reverse],
        ignore_index=True,
    )

    if not pairwise.empty:
        pairwise = pairwise.sort_values(
            "heatmap_similarity_score_pct",
            ascending=False,
        ).drop_duplicates(
            "player_id",
            keep="first",
        )

    result = candidates.merge(
        pairwise,
        on="player_id",
        how="left",
    )

    real_metric_columns = [
        "heatmap_cosine_similarity_pct",
        "occupation_overlap_pct",
        "lateral_profile_similarity_pct",
        "vertical_profile_similarity_pct",
        "peak_zone_similarity_pct",
        "entropy_similarity_pct",
        "heatmap_similarity_score_pct",
    ]

    for column in real_metric_columns:
        if column not in result.columns:
            result[column] = np.nan

        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    result["has_heatmap_similarity"] = result["heatmap_similarity_score_pct"].notna()

    result["effective_heatmap_score_pct"] = result["heatmap_similarity_score_pct"].fillna(
        neutral_score
    )

    if "peak_zone_distance" not in result.columns:
        result["peak_zone_distance"] = np.nan

    result["peak_zone_distance"] = pd.to_numeric(
        result["peak_zone_distance"],
        errors="coerce",
    )

    for column in [
        "target_matches_with_heatmap",
        "candidate_matches_with_heatmap",
        "target_heatmap_points",
        "candidate_heatmap_points",
    ]:
        if column not in result.columns:
            result[column] = np.nan

        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    return result


def attach_heatmap_profiles(
    candidates: pd.DataFrame,
    target: pd.Series,
    heatmap_profiles: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """
    Add candidate heatmap zone shares and return the target heatmap profile.
    """
    if heatmap_profiles.empty:
        return candidates, {}

    target_row = heatmap_profiles[heatmap_profiles["player_id"].eq(target["player_id"])]

    if target_row.empty:
        target_profile: dict[str, float] = {}
    else:
        target_profile = cast(
            dict[str, float],
            target_row.iloc[0].to_dict(),
        )
    candidate_profiles = heatmap_profiles.rename(
        columns={
            column: f"heatmap_{column}"
            for column in heatmap_profiles.columns
            if column != "player_id"
        }
    )

    result = candidates.merge(
        candidate_profiles,
        on="player_id",
        how="left",
    )

    return result, target_profile


__all__ = [
    "attach_heatmap_profiles",
    "attach_heatmap_similarity",
    "attach_similarity",
    "resolve_player",
]
