"""Position-aware metric registry for player intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class PositionGroup(StrEnum):
    """Semantic player-position groups used by player intelligence."""

    GOALKEEPER = "goalkeeper"
    DEFENDER = "defender"
    MIDFIELDER = "midfielder"
    FORWARD = "forward"


class MetricGroup(StrEnum):
    """Analytical families used to organise player metrics."""

    CREATION = "creation"
    PROGRESSION = "progression"
    POSSESSION = "possession"
    DEFENDING = "defending"
    SCORING = "scoring"
    PHYSICAL = "physical"
    GOALKEEPING = "goalkeeping"


class MetricUnit(StrEnum):
    """Presentation unit associated with one analytical metric."""

    PER_90 = "per90"
    PERCENT = "percent"
    RAW = "raw"


@dataclass(frozen=True, slots=True)
class MetricDefinition:
    """Metadata describing one player-intelligence metric."""

    key: str
    source_column: str
    label: str
    short_label: str
    group: MetricGroup
    unit: MetricUnit
    position_groups: frozenset[PositionGroup]
    higher_is_better: bool = True
    decimal_places: int = 2


OUTFIELD_POSITIONS: Final[frozenset[PositionGroup]] = frozenset(
    {
        PositionGroup.DEFENDER,
        PositionGroup.MIDFIELDER,
        PositionGroup.FORWARD,
    }
)

CREATIVE_POSITIONS: Final[frozenset[PositionGroup]] = frozenset(
    {
        PositionGroup.DEFENDER,
        PositionGroup.MIDFIELDER,
        PositionGroup.FORWARD,
    }
)

ATTACKING_POSITIONS: Final[frozenset[PositionGroup]] = frozenset(
    {
        PositionGroup.MIDFIELDER,
        PositionGroup.FORWARD,
    }
)

DEFENSIVE_POSITIONS: Final[frozenset[PositionGroup]] = frozenset(
    {
        PositionGroup.DEFENDER,
        PositionGroup.MIDFIELDER,
    }
)

GOALKEEPER_ONLY: Final[frozenset[PositionGroup]] = frozenset(
    {
        PositionGroup.GOALKEEPER,
    }
)


METRIC_REGISTRY: Final[tuple[MetricDefinition, ...]] = (
    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------
    MetricDefinition(
        key="expected_assists_per90",
        source_column="stat_expectedAssists_per90",
        label="Expected assists per 90",
        short_label="xA / 90",
        group=MetricGroup.CREATION,
        unit=MetricUnit.PER_90,
        position_groups=CREATIVE_POSITIONS,
    ),
    MetricDefinition(
        key="key_passes_per90",
        source_column="stat_keyPass_per90",
        label="Key passes per 90",
        short_label="Key passes / 90",
        group=MetricGroup.CREATION,
        unit=MetricUnit.PER_90,
        position_groups=CREATIVE_POSITIONS,
    ),
    MetricDefinition(
        key="assists_per90",
        source_column="stat_goalAssist_per90",
        label="Assists per 90",
        short_label="Assists / 90",
        group=MetricGroup.CREATION,
        unit=MetricUnit.PER_90,
        position_groups=CREATIVE_POSITIONS,
    ),
    MetricDefinition(
        key="big_chances_created_per90",
        source_column="stat_bigChanceCreated_per90",
        label="Big chances created per 90",
        short_label="Big chances / 90",
        group=MetricGroup.CREATION,
        unit=MetricUnit.PER_90,
        position_groups=CREATIVE_POSITIONS,
    ),
    # ------------------------------------------------------------------
    # Progression
    # ------------------------------------------------------------------
    MetricDefinition(
        key="total_progression_per90",
        source_column="stat_totalProgression_per90",
        label="Total progression per 90",
        short_label="Progression / 90",
        group=MetricGroup.PROGRESSION,
        unit=MetricUnit.PER_90,
        position_groups=OUTFIELD_POSITIONS,
    ),
    MetricDefinition(
        key="progressive_carries_per90",
        source_column="stat_progressiveBallCarriesCount_per90",
        label="Progressive carries per 90",
        short_label="Prog. carries / 90",
        group=MetricGroup.PROGRESSION,
        unit=MetricUnit.PER_90,
        position_groups=OUTFIELD_POSITIONS,
    ),
    MetricDefinition(
        key="progressive_carry_distance_per90",
        source_column="stat_totalProgressiveBallCarriesDistance_per90",
        label="Progressive carry distance per 90",
        short_label="Prog. carry m / 90",
        group=MetricGroup.PROGRESSION,
        unit=MetricUnit.PER_90,
        position_groups=OUTFIELD_POSITIONS,
    ),
    MetricDefinition(
        key="ball_carries_per90",
        source_column="stat_ballCarriesCount_per90",
        label="Ball carries per 90",
        short_label="Carries / 90",
        group=MetricGroup.PROGRESSION,
        unit=MetricUnit.PER_90,
        position_groups=OUTFIELD_POSITIONS,
    ),
    # ------------------------------------------------------------------
    # Possession
    # ------------------------------------------------------------------
    MetricDefinition(
        key="passes_per90",
        source_column="stat_totalPass_per90",
        label="Passes per 90",
        short_label="Passes / 90",
        group=MetricGroup.POSSESSION,
        unit=MetricUnit.PER_90,
        position_groups=OUTFIELD_POSITIONS,
    ),
    MetricDefinition(
        key="pass_accuracy",
        source_column="pass_accuracy_pct",
        label="Pass accuracy",
        short_label="Pass accuracy",
        group=MetricGroup.POSSESSION,
        unit=MetricUnit.PERCENT,
        position_groups=OUTFIELD_POSITIONS,
        decimal_places=1,
    ),
    MetricDefinition(
        key="touches_per90",
        source_column="stat_touches_per90",
        label="Touches per 90",
        short_label="Touches / 90",
        group=MetricGroup.POSSESSION,
        unit=MetricUnit.PER_90,
        position_groups=OUTFIELD_POSITIONS,
    ),
    MetricDefinition(
        key="possession_lost_per90",
        source_column="stat_possessionLostCtrl_per90",
        label="Possession lost per 90",
        short_label="Poss. lost / 90",
        group=MetricGroup.POSSESSION,
        unit=MetricUnit.PER_90,
        position_groups=OUTFIELD_POSITIONS,
        higher_is_better=False,
    ),
    # ------------------------------------------------------------------
    # Defending
    # ------------------------------------------------------------------
    MetricDefinition(
        key="ball_recoveries_per90",
        source_column="stat_ballRecovery_per90",
        label="Ball recoveries per 90",
        short_label="Recoveries / 90",
        group=MetricGroup.DEFENDING,
        unit=MetricUnit.PER_90,
        position_groups=DEFENSIVE_POSITIONS,
    ),
    MetricDefinition(
        key="tackles_per90",
        source_column="stat_totalTackle_per90",
        label="Tackles per 90",
        short_label="Tackles / 90",
        group=MetricGroup.DEFENDING,
        unit=MetricUnit.PER_90,
        position_groups=DEFENSIVE_POSITIONS,
    ),
    MetricDefinition(
        key="tackles_won_per90",
        source_column="stat_wonTackle_per90",
        label="Tackles won per 90",
        short_label="Tackles won / 90",
        group=MetricGroup.DEFENDING,
        unit=MetricUnit.PER_90,
        position_groups=DEFENSIVE_POSITIONS,
    ),
    MetricDefinition(
        key="interceptions_per90",
        source_column="stat_interceptionWon_per90",
        label="Interceptions per 90",
        short_label="Interceptions / 90",
        group=MetricGroup.DEFENDING,
        unit=MetricUnit.PER_90,
        position_groups=DEFENSIVE_POSITIONS,
    ),
    MetricDefinition(
        key="clearances_per90",
        source_column="stat_totalClearance_per90",
        label="Clearances per 90",
        short_label="Clearances / 90",
        group=MetricGroup.DEFENDING,
        unit=MetricUnit.PER_90,
        position_groups=frozenset(
            {
                PositionGroup.DEFENDER,
            }
        ),
    ),
    MetricDefinition(
        key="duel_success",
        source_column="duel_success_pct",
        label="Duel success",
        short_label="Duel success",
        group=MetricGroup.DEFENDING,
        unit=MetricUnit.PERCENT,
        position_groups=DEFENSIVE_POSITIONS,
        decimal_places=1,
    ),
    MetricDefinition(
        key="aerial_duel_success",
        source_column="aerial_duel_success_pct",
        label="Aerial duel success",
        short_label="Aerial success",
        group=MetricGroup.DEFENDING,
        unit=MetricUnit.PERCENT,
        position_groups=frozenset(
            {
                PositionGroup.DEFENDER,
            }
        ),
        decimal_places=1,
    ),
    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------
    MetricDefinition(
        key="expected_goals_per90",
        source_column="stat_expectedGoals_per90",
        label="Expected goals per 90",
        short_label="xG / 90",
        group=MetricGroup.SCORING,
        unit=MetricUnit.PER_90,
        position_groups=ATTACKING_POSITIONS,
    ),
    MetricDefinition(
        key="shots_per90",
        source_column="stat_totalShots_per90",
        label="Shots per 90",
        short_label="Shots / 90",
        group=MetricGroup.SCORING,
        unit=MetricUnit.PER_90,
        position_groups=ATTACKING_POSITIONS,
    ),
    MetricDefinition(
        key="shots_on_target_per90",
        source_column="stat_onTargetScoringAttempt_per90",
        label="Shots on target per 90",
        short_label="SoT / 90",
        group=MetricGroup.SCORING,
        unit=MetricUnit.PER_90,
        position_groups=ATTACKING_POSITIONS,
    ),
    MetricDefinition(
        key="shot_on_target_percentage",
        source_column="shot_on_target_pct",
        label="Shots on target",
        short_label="SoT %",
        group=MetricGroup.SCORING,
        unit=MetricUnit.PERCENT,
        position_groups=ATTACKING_POSITIONS,
        decimal_places=1,
    ),
    MetricDefinition(
        key="goals_per90",
        source_column="stat_goals_per90",
        label="Goals per 90",
        short_label="Goals / 90",
        group=MetricGroup.SCORING,
        unit=MetricUnit.PER_90,
        position_groups=ATTACKING_POSITIONS,
    ),
    # ------------------------------------------------------------------
    # Physical
    # ------------------------------------------------------------------
    MetricDefinition(
        key="distance_covered_per90",
        source_column="stat_kilometersCovered_per90",
        label="Distance covered per 90",
        short_label="Distance / 90",
        group=MetricGroup.PHYSICAL,
        unit=MetricUnit.PER_90,
        position_groups=OUTFIELD_POSITIONS,
    ),
    MetricDefinition(
        key="sprints_per90",
        source_column="stat_numberOfSprints_per90",
        label="Sprints per 90",
        short_label="Sprints / 90",
        group=MetricGroup.PHYSICAL,
        unit=MetricUnit.PER_90,
        position_groups=OUTFIELD_POSITIONS,
    ),
    MetricDefinition(
        key="top_speed",
        source_column="stat_topSpeed_max",
        label="Top speed",
        short_label="Top speed",
        group=MetricGroup.PHYSICAL,
        unit=MetricUnit.RAW,
        position_groups=OUTFIELD_POSITIONS,
        decimal_places=1,
    ),
    # ------------------------------------------------------------------
    # Goalkeeping
    # ------------------------------------------------------------------
    MetricDefinition(
        key="saves_per90",
        source_column="stat_saves_per90",
        label="Saves per 90",
        short_label="Saves / 90",
        group=MetricGroup.GOALKEEPING,
        unit=MetricUnit.PER_90,
        position_groups=GOALKEEPER_ONLY,
    ),
    MetricDefinition(
        key="goals_prevented_per90",
        source_column="stat_goalsPrevented_per90",
        label="Goals prevented per 90",
        short_label="Goals prevented / 90",
        group=MetricGroup.GOALKEEPING,
        unit=MetricUnit.PER_90,
        position_groups=GOALKEEPER_ONLY,
    ),
    MetricDefinition(
        key="keeper_save_value_per90",
        source_column="stat_keeperSaveValue_per90",
        label="Keeper save value per 90",
        short_label="Save value / 90",
        group=MetricGroup.GOALKEEPING,
        unit=MetricUnit.PER_90,
        position_groups=GOALKEEPER_ONLY,
    ),
    MetricDefinition(
        key="keeper_sweeper_actions_per90",
        source_column="stat_totalKeeperSweeper_per90",
        label="Keeper sweeper actions per 90",
        short_label="Sweeper / 90",
        group=MetricGroup.GOALKEEPING,
        unit=MetricUnit.PER_90,
        position_groups=GOALKEEPER_ONLY,
    ),
    MetricDefinition(
        key="keeper_sweeper_accuracy",
        source_column="keeper_sweeper_accuracy_pct",
        label="Keeper sweeper accuracy",
        short_label="Sweeper accuracy",
        group=MetricGroup.GOALKEEPING,
        unit=MetricUnit.PERCENT,
        position_groups=GOALKEEPER_ONLY,
        decimal_places=1,
    ),
)


METRIC_BY_KEY: Final[dict[str, MetricDefinition]] = {
    metric.key: metric for metric in METRIC_REGISTRY
}


def get_metric_definition(
    key: str,
) -> MetricDefinition:
    """Return one registered metric by public metric key."""

    try:
        return METRIC_BY_KEY[key]
    except KeyError as error:
        raise KeyError(f"Unknown player-intelligence metric: {key}") from error


def metrics_for_position_group(
    position_group: PositionGroup,
) -> tuple[MetricDefinition, ...]:
    """Return registry metrics applicable to one semantic position group."""

    return tuple(metric for metric in METRIC_REGISTRY if position_group in metric.position_groups)


def metrics_for_group(
    metric_group: MetricGroup,
    *,
    position_group: PositionGroup | None = None,
) -> tuple[MetricDefinition, ...]:
    """Return metrics from one analytical group."""

    return tuple(
        metric
        for metric in METRIC_REGISTRY
        if metric.group == metric_group
        and (position_group is None or position_group in metric.position_groups)
    )


__all__ = [
    "METRIC_BY_KEY",
    "METRIC_REGISTRY",
    "MetricDefinition",
    "MetricGroup",
    "MetricUnit",
    "PositionGroup",
    "get_metric_definition",
    "metrics_for_group",
    "metrics_for_position_group",
]
