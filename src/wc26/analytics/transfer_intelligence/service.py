"""Application service for transfer intelligence analysis."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd

from wc26.analytics.transfer_intelligence.candidates import (
    prepare_candidate_base,
)
from wc26.analytics.transfer_intelligence.catalog import (
    TransferDataCatalog,
    load_transfer_data_catalog,
)
from wc26.analytics.transfer_intelligence.config import (
    MODE_CONFIG,
)
from wc26.analytics.transfer_intelligence.matching import (
    resolve_transfer_target,
)
from wc26.analytics.transfer_intelligence.models import (
    JsonObject,
    JsonValue,
    TransferAnalysisRequest,
    TransferAnalysisResult,
    TransferModeResult,
    TransferRecommendation,
)
from wc26.analytics.transfer_intelligence.recommendations import (
    generate_mode_results,
)


def _to_json_value(value: object) -> JsonValue:
    """Convert an analytical value into a JSON-compatible value."""

    if value is None or value is pd.NA or value is pd.NaT:
        return None

    if isinstance(value, np.generic):
        return _to_json_value(value.item())

    if isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            return None

        return value

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, Mapping):
        return {str(key): _to_json_value(item) for key, item in value.items()}

    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return [_to_json_value(item) for item in value]

    raise TypeError(f"Unsupported transfer analysis value: {type(value).__name__}")


def _to_json_object(
    values: Mapping[object, object],
) -> JsonObject:
    """Convert a mapping into a JSON-compatible object."""

    return {str(key): _to_json_value(value) for key, value in values.items()}


def _build_analysis_result(
    target: pd.Series[Any],
    results: Mapping[str, pd.DataFrame],
) -> TransferAnalysisResult:
    """Build the public result contract from pandas objects."""

    target_values = cast(
        dict[object, object],
        target.to_dict(),
    )

    mode_results: list[TransferModeResult] = []

    for mode, frame in results.items():
        records = cast(
            list[dict[object, object]],
            frame.to_dict(orient="records"),
        )

        recommendations = tuple(
            TransferRecommendation(
                data=_to_json_object(record),
            )
            for record in records
        )

        mode_results.append(
            TransferModeResult(
                mode=mode,
                recommendations=recommendations,
            )
        )

    return TransferAnalysisResult(
        target=_to_json_object(target_values),
        modes=tuple(mode_results),
    )


def run_transfer_analysis_from_catalog(
    request: TransferAnalysisRequest,
    catalog: TransferDataCatalog,
) -> TransferAnalysisResult:
    """Run transfer analysis using already loaded datasets."""

    players = catalog.players.copy()

    players["player_id"] = pd.to_numeric(
        players["player_id"],
        errors="coerce",
    )

    target = resolve_transfer_target(
        players,
        player=request.player,
        player_id=request.player_id,
    )

    (
        base_candidates,
        target_heatmap_profile,
    ) = prepare_candidate_base(
        players=players,
        similarity=catalog.similarity,
        heatmap_similarity=catalog.heatmap_similarity,
        heatmap_profiles=catalog.heatmap_profiles,
        target=target,
        minimum_minutes=request.minimum_minutes,
        minimum_role_confidence=(request.minimum_role_confidence),
        maximum_market_value=request.maximum_market_value,
        neutral_heatmap_score=request.neutral_heatmap_score,
    )

    results = {
        mode: generate_mode_results(
            base_candidates,
            mode,
            target_heatmap_profile,
        )
        for mode in MODE_CONFIG
    }

    return _build_analysis_result(
        target,
        results,
    )


def run_transfer_analysis(
    request: TransferAnalysisRequest,
) -> TransferAnalysisResult:
    """Load configured datasets and run transfer analysis."""

    catalog = load_transfer_data_catalog(
        features=request.features,
        similarity=request.similarity,
        heatmap_similarity=request.heatmap_similarity,
        heatmap_profiles=request.heatmap_profiles,
    )

    return run_transfer_analysis_from_catalog(
        request,
        catalog,
    )


__all__ = [
    "TransferAnalysisRequest",
    "run_transfer_analysis",
    "run_transfer_analysis_from_catalog",
]
