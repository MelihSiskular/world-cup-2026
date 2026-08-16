"""Structured explainability for transfer recommendations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import pandas as pd

from wc26.analytics.transfer_intelligence.explanations import (
    RecommendationReasonItem,
    build_reason_items,
)
from wc26.analytics.transfer_intelligence.scoring import (
    ModeBonusContribution,
    ModeScoreBreakdown,
    ModeSignalContribution,
    build_mode_score_breakdown,
)


@dataclass(frozen=True, slots=True)
class RecommendationScoreExplanation:
    """Mathematical breakdown of one final recommendation score."""

    weighted_signal_total: float
    bonus_total: float
    pre_clip_score: float
    final_score: float
    was_clipped: bool

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible score explanation."""

        return {
            "weighted_signal_total": self.weighted_signal_total,
            "bonus_total": self.bonus_total,
            "pre_clip_score": self.pre_clip_score,
            "final_score": self.final_score,
            "was_clipped": self.was_clipped,
        }


@dataclass(frozen=True, slots=True)
class RecommendationSignalExplanation:
    """One weighted scoring signal with user-facing metadata."""

    key: str
    label: str
    description: str
    source_score: float | None
    input_score: float
    weight: float
    weighted_contribution: float
    evidence_status: str
    note: str | None

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible signal explanation."""

        return {
            "key": self.key,
            "label": self.label,
            "description": self.description,
            "source_score": self.source_score,
            "input_score": self.input_score,
            "weight": self.weight,
            "weighted_contribution": self.weighted_contribution,
            "evidence_status": self.evidence_status,
            "note": self.note,
        }


@dataclass(frozen=True, slots=True)
class RecommendationBonusExplanation:
    """One explicit mode-specific recommendation bonus."""

    key: str
    label: str
    configured_points: float
    applied: bool
    applied_points: float

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible bonus explanation."""

        return {
            "key": self.key,
            "label": self.label,
            "configured_points": self.configured_points,
            "applied": self.applied,
            "applied_points": self.applied_points,
        }


@dataclass(frozen=True, slots=True)
class RecommendationExplainability:
    """Complete structured explanation of one recommendation score."""

    mode: str
    score: RecommendationScoreExplanation
    signals: tuple[RecommendationSignalExplanation, ...]
    bonuses: tuple[RecommendationBonusExplanation, ...]
    reasons: tuple[RecommendationReasonItem, ...]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible explainability object."""

        return {
            "mode": self.mode,
            "score": self.score.to_dict(),
            "signals": [signal.to_dict() for signal in self.signals],
            "bonuses": [bonus.to_dict() for bonus in self.bonuses],
            "reasons": [
                {
                    "key": reason.key,
                    "group": reason.group,
                    "text": reason.text,
                }
                for reason in self.reasons
            ],
        }


SIGNAL_METADATA: Final[dict[str, tuple[str, str]]] = {
    "statistical_similarity_pct": (
        "Statistical similarity",
        ("Similarity between the target and candidate across the statistical player profile."),
    ),
    "role_fit_pct": (
        "Role fit",
        ("Alignment between the candidate and target across the tactical role model."),
    ),
    "spatial_similarity_pct": (
        "Spatial similarity",
        ("Similarity in average position, spatial spread, thirds and lane occupation."),
    ),
    "effective_heatmap_score_pct": (
        "Heatmap evidence",
        ("Heatmap occupation evidence used by the recruitment scoring model."),
    ),
    "player_quality_score": (
        "Player quality",
        ("Quality signal derived from the candidate's tournament performance profile."),
    ),
    "data_reliability_score": (
        "Data reliability",
        ("Reliability signal reflecting the strength of the available analytical sample."),
    ),
    "market_value_advantage_pct": (
        "Market advantage",
        ("Financial-value advantage relative to the target player."),
    ),
    "age_suitability_pct": (
        "Age suitability",
        ("Age-profile suitability for the selected recruitment scenario."),
    ),
}


BONUS_LABELS: Final[dict[str, str]] = {
    "same_final_role": "Same final role",
    "same_archetype": "Same statistical archetype",
}


def _signal_note(
    signal: ModeSignalContribution,
) -> str | None:
    """Explain exceptional evidence handling without changing scoring."""

    if signal.key == "effective_heatmap_score_pct":
        if signal.evidence_status == "fallback":
            return (
                "Direct heatmap evidence is unavailable; "
                "the configured neutral fallback is used "
                "for scoring."
            )

        if signal.evidence_status == "missing":
            return (
                "Heatmap scoring input is unavailable; the scorer contributes zero for this signal."
            )

    if signal.evidence_status == "missing":
        return "Source value is unavailable; the scorer contributes zero for this signal."

    return None


def _build_signal_explanation(
    signal: ModeSignalContribution,
) -> RecommendationSignalExplanation:
    """Attach stable user-facing metadata to one score signal."""

    metadata = SIGNAL_METADATA.get(signal.key)

    if metadata is None:
        raise ValueError(f"Missing explainability metadata for score signal: {signal.key}")

    label, description = metadata

    return RecommendationSignalExplanation(
        key=signal.key,
        label=label,
        description=description,
        source_score=signal.source_score,
        input_score=signal.input_score,
        weight=signal.weight,
        weighted_contribution=signal.weighted_contribution,
        evidence_status=signal.evidence_status,
        note=_signal_note(signal),
    )


def _build_bonus_explanation(
    bonus: ModeBonusContribution,
) -> RecommendationBonusExplanation:
    """Attach stable user-facing metadata to one score bonus."""

    label = BONUS_LABELS.get(bonus.key)

    if label is None:
        raise ValueError(f"Missing explainability metadata for score bonus: {bonus.key}")

    return RecommendationBonusExplanation(
        key=bonus.key,
        label=label,
        configured_points=bonus.configured_points,
        applied=bonus.applied,
        applied_points=bonus.applied_points,
    )


def _build_score_explanation(
    breakdown: ModeScoreBreakdown,
) -> RecommendationScoreExplanation:
    """Convert the scoring breakdown into the public domain shape."""

    return RecommendationScoreExplanation(
        weighted_signal_total=breakdown.weighted_signal_total,
        bonus_total=breakdown.bonus_total,
        pre_clip_score=breakdown.pre_clip_score,
        final_score=breakdown.final_score,
        was_clipped=breakdown.was_clipped,
    )


def build_recommendation_explainability(
    row: pd.Series,
    mode: str,
    target_heatmap_profile: dict[str, float],
) -> RecommendationExplainability:
    """Build the complete explanation for one recommendation."""

    breakdown = build_mode_score_breakdown(
        row,
        mode,
    )

    reasons = build_reason_items(
        row,
        mode,
        target_heatmap_profile,
    )

    return RecommendationExplainability(
        mode=mode,
        score=_build_score_explanation(breakdown),
        signals=tuple(_build_signal_explanation(signal) for signal in breakdown.signals),
        bonuses=tuple(_build_bonus_explanation(bonus) for bonus in breakdown.bonuses),
        reasons=reasons,
    )


__all__ = [
    "BONUS_LABELS",
    "SIGNAL_METADATA",
    "RecommendationBonusExplanation",
    "RecommendationExplainability",
    "RecommendationScoreExplanation",
    "RecommendationSignalExplanation",
    "build_recommendation_explainability",
]
