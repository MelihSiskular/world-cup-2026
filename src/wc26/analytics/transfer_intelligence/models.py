"""Application contract models for transfer intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class TransferAnalysisRequest:
    """Input parameters required to run transfer analysis."""

    player: str
    features: Path
    similarity: Path
    heatmap_similarity: Path
    heatmap_profiles: Path
    minimum_minutes: float
    minimum_role_confidence: float
    maximum_market_value: float | None
    neutral_heatmap_score: float


@dataclass(frozen=True, slots=True)
class TransferRecommendation:
    """One JSON-compatible transfer recommendation."""

    data: JsonObject

    def to_dict(self) -> JsonObject:
        """Return a detached dictionary representation."""

        return dict(self.data)


@dataclass(frozen=True, slots=True)
class TransferModeResult:
    """Recommendations produced for one recruitment mode."""

    mode: str
    recommendations: tuple[TransferRecommendation, ...]

    def to_dict(self) -> JsonObject:
        """Return a JSON-compatible dictionary representation."""

        recommendation_values: list[JsonValue] = [
            recommendation.to_dict() for recommendation in self.recommendations
        ]

        return {
            "mode": self.mode,
            "recommendations": recommendation_values,
        }


@dataclass(frozen=True, slots=True)
class TransferAnalysisResult:
    """Complete structured result of a transfer analysis."""

    target: JsonObject
    modes: tuple[TransferModeResult, ...]

    def to_dict(self) -> JsonObject:
        """Return a JSON-compatible dictionary representation."""

        mode_values: dict[str, JsonValue] = {mode.mode: mode.to_dict() for mode in self.modes}

        return {
            "target": dict(self.target),
            "modes": mode_values,
        }


__all__ = [
    "JsonObject",
    "JsonScalar",
    "JsonValue",
    "TransferAnalysisRequest",
    "TransferAnalysisResult",
    "TransferModeResult",
    "TransferRecommendation",
]
