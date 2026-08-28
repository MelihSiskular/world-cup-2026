"""Domain service for generic multi-player comparisons."""

from __future__ import annotations

import math
from typing import Any, cast

import pandas as pd

from wc26.analytics.transfer_intelligence.catalog import (
    TransferDataCatalog,
    load_transfer_data_catalog,
)
from wc26.analytics.transfer_intelligence.errors import (
    InvalidDatasetError,
    InvalidMultiPlayerComparisonRequestError,
)
from wc26.analytics.transfer_intelligence.matching import (
    attach_heatmap_similarity,
    attach_similarity,
    resolve_player_by_id,
)
from wc26.analytics.transfer_intelligence.models import (
    MultiPlayerComparisonCandidateResult,
    MultiPlayerComparisonEvidenceResult,
    MultiPlayerComparisonRequest,
    MultiPlayerComparisonResult,
    MultiPlayerComparisonRoleMetricGroupResult,
    MultiPlayerComparisonRoleMetricResult,
    MultiPlayerComparisonRoleMetricValueResult,
    PlayerSearchItem,
)
from wc26.analytics.transfer_intelligence.role_metrics import (
    resolve_role_metric_groups,
)
from wc26.analytics.transfer_intelligence.scoring import (
    calculate_market_value_advantage,
    calculate_role_fit,
    calculate_spatial_similarity,
)

MAX_MULTI_COMPARISON_CANDIDATES = 3

ROLE_EVIDENCE_COLUMNS = (
    "final_role",
    "archetype",
    "spatial_role",
    "lateral_profile",
    "vertical_profile",
    "mobility_profile",
)

SPATIAL_EVIDENCE_COLUMNS = (
    "weighted_mean_x",
    "weighted_mean_y",
    "spatial_spread",
    "attacking_third_match_share",
    "middle_third_match_share",
    "defensive_third_match_share",
    "wide_lane_match_share",
    "half_space_match_share",
    "central_lane_match_share",
)


def _is_positive_integer(
    value: object,
) -> bool:
    """Return whether a value is a supported player identifier."""

    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _validate_request(
    request: MultiPlayerComparisonRequest,
) -> None:
    """Validate identifiers before reading analytical datasets."""

    if not _is_positive_integer(
        request.target_player_id,
    ):
        raise InvalidMultiPlayerComparisonRequestError(
            "Target player ID must be a positive integer."
        )

    candidate_count = len(
        request.candidate_player_ids,
    )

    if candidate_count < 1 or candidate_count > MAX_MULTI_COMPARISON_CANDIDATES:
        raise InvalidMultiPlayerComparisonRequestError(
            "Provide between one and three candidate player IDs."
        )

    if not all(_is_positive_integer(player_id) for player_id in request.candidate_player_ids):
        raise InvalidMultiPlayerComparisonRequestError(
            "Candidate player IDs must be positive integers."
        )

    all_player_ids = (
        request.target_player_id,
        *request.candidate_player_ids,
    )

    if len(set(all_player_ids)) != len(
        all_player_ids,
    ):
        raise InvalidMultiPlayerComparisonRequestError(
            "Target and candidate player IDs must be unique."
        )


def _optional_float(
    value: object,
) -> float | None:
    """Return one finite numeric value when evidence exists."""

    numeric = pd.to_numeric(
        pd.Series(
            [value],
            dtype="object",
        ),
        errors="coerce",
    ).iloc[0]

    if pd.isna(numeric):
        return None

    result = float(numeric)

    if not math.isfinite(result):
        return None

    return result


def _optional_text(
    value: object,
) -> str | None:
    """Return one normalized optional text value."""

    if value is None or value is pd.NA or value is pd.NaT:
        return None

    if bool(
        pd.Series(
            [value],
            dtype="object",
        )
        .isna()
        .iloc[0]
    ):
        return None

    normalized = str(value).strip()

    return normalized or None


def _build_player_result(
    row: pd.Series[Any],
) -> PlayerSearchItem:
    """Build the shared lightweight player representation."""

    player_id_value = _optional_float(
        row.get("player_id"),
    )

    if player_id_value is None:
        raise InvalidDatasetError("Comparison player is missing a valid player ID.")

    player_name = _optional_text(
        row.get("player_name"),
    )

    if player_name is None:
        raise InvalidDatasetError(
            f"Comparison player {int(player_id_value)} is missing a player name."
        )

    return PlayerSearchItem(
        player_id=int(player_id_value),
        player_name=player_name,
        national_team_name=_optional_text(
            row.get("national_team_name"),
        ),
        country_name=_optional_text(
            row.get("country_name"),
        ),
        country_alpha3=_optional_text(
            row.get("country_alpha3"),
        ),
        position=_optional_text(
            row.get("position"),
        ),
        final_role=_optional_text(
            row.get("final_role"),
        ),
        archetype=_optional_text(
            row.get("archetype"),
        ),
        spatial_role=_optional_text(
            row.get("spatial_role"),
        ),
        age=_optional_float(
            row.get("age"),
        ),
        market_value=_optional_float(
            row.get("market_value"),
        ),
        market_value_currency=_optional_text(
            row.get("market_value_currency"),
        ),
        minutes=_optional_float(
            row.get("minutes"),
        ),
        role_confidence_pct=_optional_float(
            row.get(
                "role_confidence_pct",
                row.get(
                    "role_confidence_score",
                ),
            ),
        ),
        data_reliability_score=_optional_float(
            row.get("data_reliability_score"),
        ),
        player_quality_score=_optional_float(
            row.get("player_quality_score"),
        ),
    )


def _attach_comparison_evidence(
    cohort: pd.DataFrame,
    target: pd.Series[Any],
    catalog: TransferDataCatalog,
) -> pd.DataFrame:
    """
    Calculate evidence over the complete same-position cohort.

    Selected candidates are intentionally not used as the normalization
    population for spatial similarity.
    """

    result = attach_similarity(
        cohort,
        target,
        catalog.similarity,
    )

    result = attach_heatmap_similarity(
        result,
        target,
        catalog.heatmap_similarity,
        neutral_score=0.0,
    )

    result["role_fit_pct"] = calculate_role_fit(
        result,
        target,
    )

    role_evidence_available = pd.Series(
        False,
        index=result.index,
        dtype=bool,
    )

    for column in ROLE_EVIDENCE_COLUMNS:
        if (
            column in result.columns
            and _optional_text(
                target.get(column),
            )
            is not None
        ):
            role_evidence_available |= result[column].map(_optional_text).notna()

    result["_role_evidence_available"] = role_evidence_available

    result["spatial_similarity_pct"] = calculate_spatial_similarity(
        result,
        target,
    )

    usable_spatial_columns = [
        column
        for column in SPATIAL_EVIDENCE_COLUMNS
        if (
            column in result.columns
            and _optional_float(
                target.get(column),
            )
            is not None
        )
    ]

    if len(usable_spatial_columns) < 3:
        spatial_evidence_available = pd.Series(
            False,
            index=result.index,
            dtype=bool,
        )
    else:
        spatial_values = result[usable_spatial_columns].apply(
            pd.to_numeric,
            errors="coerce",
        )

        spatial_evidence_available = spatial_values.notna().sum(axis=1).ge(3)

    result["_spatial_evidence_available"] = spatial_evidence_available

    result["market_value_advantage_pct"] = calculate_market_value_advantage(
        result,
        target,
    )

    target_market_value = _optional_float(
        target.get("market_value"),
    )

    candidate_market_values = pd.to_numeric(
        result["market_value"],
        errors="coerce",
    )

    market_evidence_available = candidate_market_values.notna() & candidate_market_values.ge(0)

    if target_market_value is None or target_market_value <= 0:
        market_evidence_available = pd.Series(
            False,
            index=result.index,
            dtype=bool,
        )

    result["_market_evidence_available"] = market_evidence_available

    return result


def _build_candidate_result(
    row: pd.Series[Any],
) -> MultiPlayerComparisonCandidateResult:
    """Build one ordered candidate response."""

    role_fit_pct = (
        _optional_float(
            row.get("role_fit_pct"),
        )
        if bool(
            row.get(
                "_role_evidence_available",
                False,
            )
        )
        else None
    )

    spatial_similarity_pct = (
        _optional_float(
            row.get(
                "spatial_similarity_pct",
            ),
        )
        if bool(
            row.get(
                "_spatial_evidence_available",
                False,
            )
        )
        else None
    )

    market_value_advantage_pct = (
        _optional_float(
            row.get(
                "market_value_advantage_pct",
            ),
        )
        if bool(
            row.get(
                "_market_evidence_available",
                False,
            )
        )
        else None
    )

    return MultiPlayerComparisonCandidateResult(
        player=_build_player_result(
            row,
        ),
        evidence=(
            MultiPlayerComparisonEvidenceResult(
                statistical_similarity_pct=(
                    _optional_float(
                        row.get(
                            "statistical_similarity_pct",
                        ),
                    )
                ),
                spatial_similarity_pct=(spatial_similarity_pct),
                heatmap_similarity_score_pct=(
                    _optional_float(
                        row.get(
                            "heatmap_similarity_score_pct",
                        ),
                    )
                ),
                role_fit_pct=role_fit_pct,
                market_value_advantage_pct=(market_value_advantage_pct),
            )
        ),
    )


def _build_role_metric_groups(
    *,
    target: pd.Series[Any],
    player_ids: tuple[int, ...],
    tournament_summary: pd.DataFrame,
) -> tuple[MultiPlayerComparisonRoleMetricGroupResult, ...]:
    """Compare selected players using duties defined by the target's role."""

    definitions = resolve_role_metric_groups(
        final_role=_optional_text(
            target.get("final_role"),
        ),
        archetype=_optional_text(
            target.get("archetype"),
        ),
    )

    if not definitions or tournament_summary.empty:
        return ()

    required_columns = {
        "player_id",
        *(
            column
            for group in definitions
            for metric in group.metrics
            for column in (
                metric.total_column,
                metric.per90_column,
            )
        ),
    }

    missing_columns = required_columns.difference(
        tournament_summary.columns,
    )

    if missing_columns:
        raise InvalidDatasetError(
            "Missing role comparison columns: "
            + ", ".join(
                sorted(missing_columns),
            )
        )

    records = cast(
        "list[dict[str, Any]]",
        tournament_summary[list(required_columns)].to_dict(
            orient="records",
        ),
    )

    records_by_player_id: dict[
        int,
        dict[str, Any],
    ] = {}

    for record in records:
        numeric_player_id = _optional_float(
            record.get("player_id"),
        )

        if numeric_player_id is None or not numeric_player_id.is_integer():
            raise InvalidDatasetError("Player tournament summary contains an invalid player ID.")

        player_id = int(numeric_player_id)

        if player_id in records_by_player_id:
            raise InvalidDatasetError("Player tournament summary contains duplicate player IDs.")

        records_by_player_id[player_id] = record

    return tuple(
        MultiPlayerComparisonRoleMetricGroupResult(
            key=group.key,
            label=group.label,
            metrics=tuple(
                MultiPlayerComparisonRoleMetricResult(
                    key=metric.key,
                    label=metric.label,
                    values=tuple(
                        MultiPlayerComparisonRoleMetricValueResult(
                            player_id=player_id,
                            total=_optional_float(
                                records_by_player_id.get(
                                    player_id,
                                    {},
                                ).get(metric.total_column),
                            ),
                            per90=_optional_float(
                                records_by_player_id.get(
                                    player_id,
                                    {},
                                ).get(metric.per90_column),
                            ),
                        )
                        for player_id in player_ids
                    ),
                )
                for metric in group.metrics
            ),
        )
        for group in definitions
    )


def run_multi_player_comparison_from_catalog(
    request: MultiPlayerComparisonRequest,
    catalog: TransferDataCatalog,
) -> MultiPlayerComparisonResult:
    """Compare selected players using an already-loaded data catalog."""

    _validate_request(
        request,
    )

    players = catalog.players.copy()

    players["player_id"] = pd.to_numeric(
        players["player_id"],
        errors="coerce",
    )

    target = resolve_player_by_id(
        players,
        request.target_player_id,
    )

    target_position = _optional_text(
        target.get("position"),
    )

    if target_position is None:
        raise InvalidMultiPlayerComparisonRequestError("Target player position is unavailable.")

    selected_players = [
        resolve_player_by_id(
            players,
            candidate_player_id,
        )
        for candidate_player_id in request.candidate_player_ids
    ]

    for candidate in selected_players:
        candidate_position = _optional_text(
            candidate.get("position"),
        )

        if candidate_position != target_position:
            raise InvalidMultiPlayerComparisonRequestError(
                "All comparison candidates must share the target player's position."
            )

    same_position_cohort = players.loc[
        players["position"].eq(
            target["position"],
        )
        & ~players["player_id"].eq(
            target["player_id"],
        )
    ].copy()

    comparison_cohort = _attach_comparison_evidence(
        same_position_cohort,
        target,
        catalog,
    )

    indexed_cohort = comparison_cohort.set_index(
        "player_id",
        drop=False,
    )

    candidates = tuple(
        _build_candidate_result(
            cast(
                "pd.Series[Any]",
                indexed_cohort.loc[candidate_player_id],
            ),
        )
        for candidate_player_id in request.candidate_player_ids
    )

    role_metrics = _build_role_metric_groups(
        target=target,
        player_ids=(
            request.target_player_id,
            *request.candidate_player_ids,
        ),
        tournament_summary=(catalog.player_tournament_summary),
    )

    return MultiPlayerComparisonResult(
        target=_build_player_result(
            target,
        ),
        candidates=candidates,
        role_metrics=role_metrics,
    )


def run_multi_player_comparison(
    request: MultiPlayerComparisonRequest,
) -> MultiPlayerComparisonResult:
    """Load configured datasets and compare selected players."""

    catalog = load_transfer_data_catalog(
        features=request.features,
        similarity=request.similarity,
        heatmap_similarity=(request.heatmap_similarity),
        heatmap_profiles=(request.heatmap_profiles),
        player_tournament_summary=(request.player_tournament_summary),
    )

    return run_multi_player_comparison_from_catalog(
        request,
        catalog,
    )


__all__ = [
    "MAX_MULTI_COMPARISON_CANDIDATES",
    "run_multi_player_comparison",
    "run_multi_player_comparison_from_catalog",
]
