"""Transfer Intelligence API request and response schemas."""

from __future__ import annotations

from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    model_validator,
)


class TransferAnalysisPayload(BaseModel):
    """Client-provided parameters for transfer analysis."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    player: str | None = Field(
        default=None,
        min_length=1,
        description=("Name of the target player. Provide exactly one of player or player_id."),
        examples=["Michael Olise"],
    )
    player_id: int | None = Field(
        default=None,
        gt=0,
        description=(
            "Stable identifier of the target player. Provide exactly one of player or player_id."
        ),
        examples=[978838],
    )
    minimum_minutes: float = Field(
        default=150.0,
        ge=0.0,
        description="Minimum tournament minutes required for candidates.",
    )
    minimum_role_confidence: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="Minimum role-confidence percentage.",
    )
    maximum_market_value: float | None = Field(
        default=None,
        ge=0.0,
        description="Optional maximum candidate market value.",
    )
    neutral_heatmap_score: float = Field(
        default=70.0,
        ge=0.0,
        le=100.0,
        description="Fallback heatmap score when spatial data is unavailable.",
    )

    @model_validator(mode="after")
    def validate_target_identifier(self) -> Self:
        """Require exactly one supported player identifier."""

        identifier_count = sum(
            identifier is not None
            for identifier in (
                self.player,
                self.player_id,
            )
        )

        if identifier_count != 1:
            raise ValueError("Provide exactly one of player or player_id.")

        return self


class TransferModeResponse(BaseModel):
    """Recommendations produced for one recruitment scenario."""

    model_config = ConfigDict(extra="forbid")

    mode: str
    recommendations: list[dict[str, JsonValue]]


class TransferAnalysisResponse(BaseModel):
    """Structured transfer analysis API response."""

    model_config = ConfigDict(extra="forbid")

    target: dict[str, JsonValue]
    modes: dict[str, TransferModeResponse]


__all__ = [
    "TransferAnalysisPayload",
    "TransferAnalysisResponse",
    "TransferModeResponse",
]
