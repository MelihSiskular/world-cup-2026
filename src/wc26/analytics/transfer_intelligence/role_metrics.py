"""Canonical target-role metric definitions for multi-player comparisons."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RoleMetricDefinition:
    """One tournament-total and per-90 metric pair."""

    key: str
    label: str
    total_column: str
    per90_column: str


@dataclass(frozen=True, slots=True)
class RoleMetricGroupDefinition:
    """One football-duty group selected by the target's final role."""

    key: str
    label: str
    metrics: tuple[RoleMetricDefinition, ...]


def _metric(
    key: str,
    label: str,
) -> RoleMetricDefinition:
    return RoleMetricDefinition(
        key=key,
        label=label,
        total_column=f"stat_{key}",
        per90_column=f"stat_{key}_per90",
    )


METRICS = {
    metric.key: metric
    for metric in (
        _metric("saves", "Saves"),
        _metric("goalsPrevented", "Goals prevented"),
        _metric("keeperSaveValue", "Keeper save value"),
        _metric("savedShotsFromInsideTheBox", "Inside-box saves"),
        _metric("goodHighClaim", "High claims"),
        _metric("punches", "Punches"),
        _metric("totalPass", "Passes"),
        _metric("accuratePass", "Accurate passes"),
        _metric("totalLongBalls", "Long balls"),
        _metric("accurateLongBalls", "Accurate long balls"),
        _metric("totalTackle", "Tackles"),
        _metric("wonTackle", "Tackles won"),
        _metric("interceptionWon", "Interceptions"),
        _metric("totalClearance", "Clearances"),
        _metric("outfielderBlock", "Blocks"),
        _metric("ballRecovery", "Ball recoveries"),
        _metric("duelWon", "Duels won"),
        _metric("aerialWon", "Aerial duels won"),
        _metric("totalProgression", "Progression distance"),
        _metric("progressiveBallCarriesCount", "Progressive carries"),
        _metric("ballCarriesCount", "Carries"),
        _metric("totalBallCarriesDistance", "Carry distance"),
        _metric("totalCross", "Crosses"),
        _metric("accurateCross", "Accurate crosses"),
        _metric("keyPass", "Key passes"),
        _metric("expectedAssists", "Expected assists"),
        _metric("possessionLostCtrl", "Possessions lost"),
        _metric("errorLeadToAShot", "Errors leading to a shot"),
        _metric("errorLeadToAGoal", "Errors leading to a goal"),
        _metric("goalAssist", "Assists"),
        _metric("bigChanceCreated", "Big chances created"),
        _metric("goals", "Goals"),
        _metric("expectedGoals", "Expected goals"),
        _metric("totalShots", "Shots"),
        _metric("onTargetScoringAttempt", "Shots on target"),
        _metric("dispossessed", "Times dispossessed"),
        _metric("unsuccessfulTouch", "Unsuccessful touches"),
        _metric("bigChanceMissed", "Big chances missed"),
        _metric("touches", "Touches"),
    )
}


CATEGORY_LABELS = {
    "shot_stopping": "Shot stopping",
    "box_command": "Box command",
    "short_distribution": "Short distribution",
    "defending": "Defending",
    "duels": "Ground duels",
    "aerial": "Aerial defending",
    "passing": "Passing",
    "progression": "Progression",
    "wide_attack": "Wide attacking output",
    "security": "Possession security",
    "passing_volume": "Passing volume",
    "creativity": "Chance creation",
    "defensive_work": "Defensive work",
    "scoring_threat": "Scoring threat",
    "wide_creation": "Wide creation",
    "ball_security": "Ball security",
    "finishing": "Finishing",
    "shooting_volume": "Shooting volume",
    "link_play": "Link play",
    "aerial_presence": "Aerial presence",
}


CATEGORY_METRIC_KEYS = {
    "shot_stopping": (
        "saves",
        "goalsPrevented",
        "keeperSaveValue",
        "savedShotsFromInsideTheBox",
    ),
    "box_command": (
        "goodHighClaim",
        "punches",
        "ballRecovery",
    ),
    "short_distribution": (
        "totalPass",
        "accuratePass",
    ),
    "defending": (
        "totalTackle",
        "wonTackle",
        "interceptionWon",
        "totalClearance",
        "outfielderBlock",
        "ballRecovery",
    ),
    "duels": ("duelWon",),
    "aerial": ("aerialWon",),
    "passing": (
        "totalPass",
        "accuratePass",
        "totalLongBalls",
        "accurateLongBalls",
    ),
    "progression": (
        "totalProgression",
        "progressiveBallCarriesCount",
        "ballCarriesCount",
        "totalBallCarriesDistance",
    ),
    "wide_attack": (
        "totalCross",
        "accurateCross",
        "keyPass",
        "expectedAssists",
    ),
    "security": (
        "possessionLostCtrl",
        "errorLeadToAShot",
        "errorLeadToAGoal",
    ),
    "passing_volume": (
        "totalPass",
        "accuratePass",
        "totalLongBalls",
        "accurateLongBalls",
    ),
    "creativity": (
        "goalAssist",
        "expectedAssists",
        "keyPass",
        "bigChanceCreated",
    ),
    "defensive_work": (
        "ballRecovery",
        "totalTackle",
        "interceptionWon",
        "duelWon",
    ),
    "scoring_threat": (
        "goals",
        "expectedGoals",
        "totalShots",
        "onTargetScoringAttempt",
    ),
    "wide_creation": (
        "totalCross",
        "accurateCross",
        "expectedAssists",
        "keyPass",
    ),
    "ball_security": (
        "possessionLostCtrl",
        "dispossessed",
        "unsuccessfulTouch",
    ),
    "finishing": (
        "goals",
        "expectedGoals",
        "onTargetScoringAttempt",
        "bigChanceMissed",
    ),
    "shooting_volume": (
        "totalShots",
        "onTargetScoringAttempt",
    ),
    "link_play": (
        "totalPass",
        "accuratePass",
        "touches",
    ),
    "aerial_presence": ("aerialWon",),
}


def _roles(
    categories: tuple[str, ...],
    *roles: str,
) -> dict[str, tuple[str, ...]]:
    return {role: categories for role in roles}


FINAL_ROLE_CATEGORIES = {
    **_roles(("short_distribution",), "Ball-Playing Goalkeeper"),
    **_roles(("box_command",), "Commanding Goalkeeper"),
    **_roles(("shot_stopping", "box_command"), "Commanding Shot Stopper"),
    **_roles(("aerial", "defending"), "Aerial-Dominant Centre-Back"),
    **_roles(("aerial", "duels"), "Left Aerial Full-Back", "Right Aerial Full-Back"),
    **_roles(
        ("wide_attack", "progression"),
        "Central Attacking Full-Back",
        "Left Attacking Full-Back",
        "Right Attacking Full-Back",
        "Left Overlapping Full-Back",
        "Right Overlapping Full-Back",
        "Left Progressive Full-Back",
        "Right Progressive Full-Back",
    ),
    **_roles(
        ("progression", "passing"),
        "Left Inverted Attacking Full-Back",
        "Right Inverted Attacking Full-Back",
        "Ball-Carrying Centre-Back",
        "Central Wide Centre-Back",
        "Left Wide Centre-Back",
        "Right Wide Centre-Back",
    ),
    **_roles(
        ("defending", "duels"),
        "Aggressive Stopper Centre-Back",
        "Left Defensive Full-Back",
        "Right Defensive Full-Back",
    ),
    **_roles(
        ("passing", "security"),
        "Central Possession Full-Back",
        "Left Possession Full-Back",
        "Right Possession Full-Back",
        "Safe Ball-Playing Centre-Back",
    ),
    **_roles(("shooting_volume", "finishing"), "High-Volume Shooter"),
    **_roles(("link_play", "creativity"), "Link Forward"),
    **_roles(("finishing", "shooting_volume"), "Poacher"),
    **_roles(
        ("aerial_presence", "link_play"),
        "Central Target Forward",
        "Deep Target Forward",
        "Left Wide Target Forward",
        "Right Wide Target Forward",
    ),
    **_roles(
        ("scoring_threat", "creativity"),
        "Advanced Goal-Threat Midfielder",
    ),
    **_roles(
        ("scoring_threat", "progression"),
        "Box-to-Box Goal-Threat Midfielder",
        "Central Goal-Threat Number 8",
        "Left Goal-Threat Number 8",
        "Right Goal-Threat Number 8",
    ),
    **_roles(
        ("scoring_threat", "wide_creation"),
        "Left Goal-Threat Wide Midfielder",
        "Right Goal-Threat Wide Midfielder",
    ),
    **_roles(
        ("ball_security", "defensive_work"),
        "Possession-Secure Midfielder - Defensive Work",
    ),
    **_roles(
        ("ball_security", "passing_volume"),
        "Possession-Secure Midfielder - Passing Volume",
    ),
    **_roles(
        ("creativity", "progression"),
        "Advanced Central Playmaker",
        "Central Half-Space Creator",
        "Left Half-Space Creator",
        "Right Half-Space Creator",
    ),
    **_roles(
        ("creativity", "passing_volume"),
        "Creative Central Midfielder",
    ),
    **_roles(
        ("creativity", "wide_creation"),
        "Left Touchline Creator",
        "Right Touchline Creator",
    ),
}


ARCHETYPE_CATEGORIES = {
    "Ball-Playing Goalkeeper": ("short_distribution",),
    "Commanding Goalkeeper": ("box_command",),
    "Commanding Shot Stopper": ("shot_stopping", "box_command"),
    "Aerial Enforcer": ("aerial", "defending"),
    "Attacking Full-Back": ("wide_attack", "progression"),
    "Ball-Carrying Defender": ("progression", "passing"),
    "Defensive Stopper": ("defending", "duels"),
    "Safe-Possession Defender": ("passing", "security"),
    "High-Volume Shooter": ("shooting_volume", "finishing"),
    "Link Forward": ("link_play", "creativity"),
    "Poacher": ("finishing", "shooting_volume"),
    "Target Forward": ("aerial_presence", "link_play"),
    "Goal-Threat Midfielder": ("scoring_threat", "progression"),
    "Possession-Secure Midfielder - Defensive Work": (
        "ball_security",
        "defensive_work",
    ),
    "Possession-Secure Midfielder - Passing Volume": (
        "ball_security",
        "passing_volume",
    ),
    "Wide Creator": ("creativity", "wide_creation"),
}


SUPPORTED_FINAL_ROLES = frozenset(
    FINAL_ROLE_CATEGORIES,
)


def resolve_role_metric_groups(
    *,
    final_role: str | None,
    archetype: str | None,
) -> tuple[RoleMetricGroupDefinition, ...]:
    """Resolve target duties and de-duplicated metrics in display order."""

    categories = FINAL_ROLE_CATEGORIES.get(final_role) if final_role is not None else None

    if categories is None and archetype is not None:
        categories = ARCHETYPE_CATEGORIES.get(archetype)

    if categories is None:
        return ()

    seen_metrics: set[str] = set()
    groups: list[RoleMetricGroupDefinition] = []

    for category in categories:
        metrics = tuple(
            METRICS[key] for key in CATEGORY_METRIC_KEYS[category] if key not in seen_metrics
        )

        seen_metrics.update(metric.key for metric in metrics)

        if metrics:
            groups.append(
                RoleMetricGroupDefinition(
                    key=category,
                    label=CATEGORY_LABELS[category],
                    metrics=metrics,
                )
            )

    return tuple(groups)


__all__ = [
    "ARCHETYPE_CATEGORIES",
    "FINAL_ROLE_CATEGORIES",
    "RoleMetricDefinition",
    "RoleMetricGroupDefinition",
    "SUPPORTED_FINAL_ROLES",
    "resolve_role_metric_groups",
]
