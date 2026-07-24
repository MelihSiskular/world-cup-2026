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


@dataclass(frozen=True, slots=True)
class PlayerSearchRequest:
    """Input parameters required to search for players."""

    query: str
    features: Path
    limit: int


@dataclass(frozen=True, slots=True)
class PlayerSearchItem:
    """One lightweight player-search result."""

    player_id: int
    player_name: str
    national_team_name: str | None
    position: str | None
    final_role: str | None
    archetype: str | None
    age: float | None
    market_value: float | None
    market_value_currency: str | None

    def to_dict(self) -> JsonObject:
        """Return a JSON-compatible player representation."""

        return {
            "player_id": self.player_id,
            "player_name": self.player_name,
            "national_team_name": self.national_team_name,
            "position": self.position,
            "final_role": self.final_role,
            "archetype": self.archetype,
            "age": self.age,
            "market_value": self.market_value,
            "market_value_currency": self.market_value_currency,
        }


@dataclass(frozen=True, slots=True)
class PlayerSearchResult:
    """Structured result returned by a player search."""

    query: str
    players: tuple[PlayerSearchItem, ...]

    @property
    def count(self) -> int:
        """Return the number of players included in the result."""

        return len(self.players)

    def to_dict(self) -> JsonObject:
        """Return a JSON-compatible search result."""

        player_values: list[JsonValue] = [player.to_dict() for player in self.players]

        return {
            "query": self.query,
            "count": self.count,
            "players": player_values,
        }


__all__ = [
    "JsonObject",
    "JsonScalar",
    "JsonValue",
    "PlayerSearchItem",
    "PlayerSearchRequest",
    "PlayerSearchResult",
    "TransferAnalysisRequest",
    "TransferAnalysisResult",
    "TransferModeResult",
    "TransferRecommendation",
]
