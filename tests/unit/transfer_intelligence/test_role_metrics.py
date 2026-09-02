"""Tests for target final-role metric selection."""

from itertools import permutations

from wc26.analytics.transfer_intelligence.role_metrics import (
    SUPPORTED_FINAL_ROLES,
    resolve_combined_role_metric_groups,
    resolve_role_metric_groups,
)

CURRENT_FINAL_ROLES = {
    "Aerial-Dominant Centre-Back",
    "Left Aerial Full-Back",
    "Right Aerial Full-Back",
    "Central Attacking Full-Back",
    "Left Attacking Full-Back",
    "Left Inverted Attacking Full-Back",
    "Left Overlapping Full-Back",
    "Right Attacking Full-Back",
    "Right Inverted Attacking Full-Back",
    "Right Overlapping Full-Back",
    "Ball-Carrying Centre-Back",
    "Central Wide Centre-Back",
    "Left Progressive Full-Back",
    "Left Wide Centre-Back",
    "Right Wide Centre-Back",
    "Aggressive Stopper Centre-Back",
    "Left Defensive Full-Back",
    "Right Defensive Full-Back",
    "Central Possession Full-Back",
    "Left Possession Full-Back",
    "Right Possession Full-Back",
    "Safe Ball-Playing Centre-Back",
    "High-Volume Shooter",
    "Link Forward",
    "Poacher",
    "Central Target Forward",
    "Deep Target Forward",
    "Right Wide Target Forward",
    "Ball-Playing Goalkeeper",
    "Commanding Goalkeeper",
    "Commanding Shot Stopper",
    "Advanced Goal-Threat Midfielder",
    "Box-to-Box Goal-Threat Midfielder",
    "Central Goal-Threat Number 8",
    "Left Goal-Threat Number 8",
    "Left Goal-Threat Wide Midfielder",
    "Right Goal-Threat Number 8",
    "Right Goal-Threat Wide Midfielder",
    "Possession-Secure Midfielder - Defensive Work",
    "Possession-Secure Midfielder - Passing Volume",
    "Advanced Central Playmaker",
    "Central Half-Space Creator",
    "Creative Central Midfielder",
    "Left Half-Space Creator",
    "Left Touchline Creator",
    "Right Half-Space Creator",
    "Right Touchline Creator",
}


def _metric_keys(
    final_role: str,
    archetype: str,
) -> tuple[str, ...]:
    return tuple(
        metric.key
        for group in resolve_role_metric_groups(
            final_role=final_role,
            archetype=archetype,
        )
        for metric in group.metrics
    )


def test_covers_every_final_role_in_the_runtime_feature_catalog() -> None:
    assert CURRENT_FINAL_ROLES <= SUPPORTED_FINAL_ROLES


def test_uses_half_space_creator_duties_for_the_target() -> None:
    groups = resolve_role_metric_groups(
        final_role="Central Half-Space Creator",
        archetype="Wide Creator",
    )

    assert tuple(group.key for group in groups) == (
        "creativity",
        "progression",
    )

    assert _metric_keys(
        "Central Half-Space Creator",
        "Wide Creator",
    ) == (
        "goalAssist",
        "expectedAssists",
        "keyPass",
        "bigChanceCreated",
        "totalProgression",
        "progressiveBallCarriesCount",
        "ballCarriesCount",
        "totalBallCarriesDistance",
    )


def test_touchline_and_half_space_creators_do_not_share_blindly() -> None:
    touchline_metrics = _metric_keys(
        "Left Touchline Creator",
        "Wide Creator",
    )
    half_space_metrics = _metric_keys(
        "Left Half-Space Creator",
        "Wide Creator",
    )

    assert "totalCross" in touchline_metrics
    assert "totalCross" not in half_space_metrics
    assert "totalProgression" in half_space_metrics
    assert "totalProgression" not in touchline_metrics


def test_final_role_takes_priority_over_the_archetype_fallback() -> None:
    assert tuple(
        group.key
        for group in resolve_role_metric_groups(
            final_role="Creative Central Midfielder",
            archetype="Wide Creator",
        )
    ) == (
        "creativity",
        "passing_volume",
    )


def test_builds_real_tournament_total_and_per90_column_pairs() -> None:
    groups = resolve_role_metric_groups(
        final_role="Poacher",
        archetype="Poacher",
    )

    goals = next(metric for group in groups for metric in group.metrics if metric.key == "goals")

    assert goals.total_column == "stat_goals"
    assert goals.per90_column == "stat_goals_per90"


def test_removes_metrics_repeated_across_role_duties() -> None:
    keys = _metric_keys(
        "Left Touchline Creator",
        "Wide Creator",
    )

    assert len(keys) == len(set(keys))
    assert keys.count("expectedAssists") == 1
    assert keys.count("keyPass") == 1


def test_falls_back_to_archetype_only_for_an_unknown_final_role() -> None:
    groups = resolve_role_metric_groups(
        final_role="Future Half-Space Role",
        archetype="Wide Creator",
    )

    assert tuple(group.key for group in groups) == (
        "creativity",
        "wide_creation",
    )


def test_returns_no_metrics_when_role_identity_is_unavailable() -> None:
    assert (
        resolve_role_metric_groups(
            final_role=None,
            archetype=None,
        )
        == ()
    )


def test_combines_target_and_candidate_role_metrics_without_duplicates() -> None:
    groups = resolve_combined_role_metric_groups(
        role_identities=(
            (
                "Central Half-Space Creator",
                "Wide Creator",
            ),
            (
                "Creative Central Midfielder",
                "Wide Creator",
            ),
        ),
    )

    assert tuple(group.key for group in groups) == (
        "creativity",
        "passing_volume",
        "progression",
    )

    metric_keys = tuple(metric.key for group in groups for metric in group.metrics)

    assert len(metric_keys) == len(set(metric_keys))

    assert metric_keys.count("goalAssist") == 1

    assert metric_keys.count("totalPass") == 1


def test_combined_role_metrics_are_independent_of_player_order() -> None:
    role_identities = (
        (
            "Central Half-Space Creator",
            "Wide Creator",
        ),
        (
            "Creative Central Midfielder",
            "Wide Creator",
        ),
        (
            "Advanced Central Playmaker",
            "Wide Creator",
        ),
    )

    signatures = {
        tuple(
            (
                group.key,
                tuple(metric.key for metric in group.metrics),
            )
            for group in resolve_combined_role_metric_groups(
                role_identities=tuple(
                    ordered_identities,
                ),
            )
        )
        for ordered_identities in permutations(
            role_identities,
        )
    }

    assert len(signatures) == 1

    assert signatures == {
        (
            (
                "creativity",
                (
                    "goalAssist",
                    "expectedAssists",
                    "keyPass",
                    "bigChanceCreated",
                ),
            ),
            (
                "passing_volume",
                (
                    "totalPass",
                    "accuratePass",
                    "totalLongBalls",
                    "accurateLongBalls",
                ),
            ),
            (
                "progression",
                (
                    "totalProgression",
                    "progressiveBallCarriesCount",
                    "ballCarriesCount",
                    "totalBallCarriesDistance",
                ),
            ),
        )
    }


def test_combining_the_same_role_does_not_repeat_groups() -> None:
    groups = resolve_combined_role_metric_groups(
        role_identities=(
            (
                "Central Half-Space Creator",
                "Wide Creator",
            ),
            (
                "Central Half-Space Creator",
                "Wide Creator",
            ),
        ),
    )

    assert tuple(group.key for group in groups) == (
        "creativity",
        "progression",
    )
