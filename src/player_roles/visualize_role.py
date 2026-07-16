# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


"""
RUN

python -m src.player_roles.visualize_role \
  --role "Advanced Central Playmaker"

"""

DEFAULT_ROLES = Path(
    "data/processed/player_roles/player_roles.csv"
)

DEFAULT_ARCHETYPES = Path(
    "data/processed/player_archetypes/player_archetypes.csv"
)

DEFAULT_OUTPUT_DIR = Path(
    "docs/images/player_roles/role_radars"
)


def slugify(text: str) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        str(text),
    )
    ascii_text = normalized.encode(
        "ascii",
        "ignore",
    ).decode("ascii")

    return (
        re.sub(r"[^a-zA-Z0-9]+", "_", ascii_text)
        .strip("_")
        .lower()
    )


def resolve_role_name(
    values: pd.Series,
    query: str,
) -> str:
    roles = (
        values.dropna()
        .astype(str)
        .drop_duplicates()
    )

    exact = roles[
        roles.str.casefold().eq(
            query.casefold()
        )
    ]

    if len(exact) == 1:
        return str(exact.iloc[0])

    partial = roles[
        roles.str.contains(
            query,
            case=False,
            regex=False,
        )
    ]

    if len(partial) == 1:
        return str(partial.iloc[0])

    if partial.empty:
        raise ValueError(
            f"Rol bulunamadÄ±: {query}"
        )

    raise ValueError(
        "Birden fazla rol eÅleÅti: "
        + ", ".join(partial.head(20).tolist())
    )


def pretty_feature_name(column: str) -> str:
    return (
        column.removeprefix(
            "archetype_score_"
        )
        .replace("_", " ")
        .title()
    )


def percentile_rank(
    value: float,
    population: pd.Series,
) -> float:
    population = pd.to_numeric(
        population,
        errors="coerce",
    ).dropna()

    if population.empty or pd.isna(value):
        return np.nan

    return float(
        (population.le(value).mean()) * 100
    )


def prepare_role_profile(
    roles: pd.DataFrame,
    archetypes: pd.DataFrame,
    role_name: str,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    str,
    list[str],
    pd.Series,
    pd.Series,
]:
    members = roles[
        roles["final_role"].eq(role_name)
    ].copy()

    if members.empty:
        raise ValueError(
            f"Rol iÃ§in oyuncu bulunamadÄ±: {role_name}"
        )

    position_values = (
        members["position"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    if len(position_values) != 1:
        raise ValueError(
            "Rol birden fazla pozisyon grubunda bulunuyor."
        )

    position = position_values[0]

    score_columns = [
        column
        for column in archetypes.columns
        if column.startswith(
            "archetype_score_"
        )
    ]

    if not score_columns:
        raise ValueError(
            "Archetype score kolonlarÄ± bulunamadÄ±."
        )

    member_ids = set(
        members["player_id"]
        .dropna()
        .tolist()
    )

    member_archetypes = archetypes[
        archetypes["player_id"].isin(
            member_ids
        )
    ].copy()

    position_population = archetypes[
        archetypes["position"].eq(position)
    ].copy()

    usable_columns = [
        column
        for column in score_columns
        if column in member_archetypes.columns
        and member_archetypes[column]
        .notna()
        .any()
        and position_population[column]
        .notna()
        .any()
    ]

    if len(usable_columns) < 3:
        raise ValueError(
            "Radar iÃ§in yeterli kategori bulunamadÄ±."
        )

    role_means = (
        member_archetypes[
            usable_columns
        ]
        .apply(
            pd.to_numeric,
            errors="coerce",
        )
        .mean()
    )

    role_percentiles = pd.Series(
        {
            column: percentile_rank(
                role_means[column],
                position_population[column],
            )
            for column in usable_columns
        }
    )

    role_percentiles = role_percentiles.sort_values(
        ascending=False
    )

    selected_columns = role_percentiles.index.tolist()

    return (
        members,
        member_archetypes,
        position,
        selected_columns,
        role_means[selected_columns],
        role_percentiles[selected_columns],
    )


def draw_radar(
    role_name: str,
    position: str,
    members: pd.DataFrame,
    role_means: pd.Series,
    role_percentiles: pd.Series,
    output_path: Path,
    max_features: int,
) -> None:
    selected = (
        role_percentiles
        .dropna()
        .sort_values(
            ascending=False
        )
        .head(max_features)
    )

    if len(selected) < 3:
        raise ValueError(
            "Radar iÃ§in en az Ã¼Ã§ geÃ§erli kategori gerekir."
        )

    selected_columns = selected.index.tolist()

    labels = [
        pretty_feature_name(column)
        for column in selected_columns
    ]

    values = selected.to_numpy(
        dtype=float
    )

    raw_values = (
        role_means[selected_columns]
        .to_numpy(dtype=float)
    )

    angles = np.linspace(
        0,
        2 * np.pi,
        len(labels),
        endpoint=False,
    )

    values_closed = np.concatenate(
        [values, [values[0]]]
    )

    angles_closed = np.concatenate(
        [angles, [angles[0]]]
    )

    figure = plt.figure(
        figsize=(12, 9),
        facecolor="#07150f",
    )

    axis = figure.add_subplot(
        111,
        polar=True,
    )

    axis.set_facecolor("#0c2419")
    axis.set_theta_offset(np.pi / 2)
    axis.set_theta_direction(-1)

    axis.plot(
        angles_closed,
        values_closed,
        linewidth=2.5,
    )

    axis.fill(
        angles_closed,
        values_closed,
        alpha=0.28,
    )

    axis.scatter(
        angles,
        values,
        s=60,
        zorder=5,
    )

    axis.set_ylim(0, 100)

    axis.set_yticks(
        [20, 40, 60, 80, 100]
    )

    axis.set_yticklabels(
        ["20", "40", "60", "80", "100"],
        color="#8daf9d",
        fontsize=8,
    )

    axis.set_xticks(angles)

    axis.set_xticklabels(
        labels,
        color="#e8fff3",
        fontsize=10,
        fontweight="bold",
    )

    axis.grid(
        alpha=0.25,
        linestyle="--",
    )

    axis.spines["polar"].set_color(
        "#3b6b52"
    )

    for angle, percentile, raw in zip(
        angles,
        values,
        raw_values,
    ):
        axis.text(
            angle,
            min(percentile + 8, 98),
            f"{percentile:.0f}",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color="white",
        )

        axis.text(
            angle,
            max(percentile - 10, 5),
            f"z={raw:.2f}",
            ha="center",
            va="center",
            fontsize=7,
            color="#9fc7b2",
        )

    average_age = pd.to_numeric(
        members["age"],
        errors="coerce",
    ).mean()

    average_rating = pd.to_numeric(
        members["weighted_rating"],
        errors="coerce",
    ).mean()

    average_confidence = pd.to_numeric(
        members["role_confidence_pct"],
        errors="coerce",
    ).mean()

    common_archetype = (
        members["archetype"]
        .dropna()
        .astype(str)
        .value_counts()
        .index[0]
    )

    figure.text(
        0.06,
        0.965,
        "PLAYER ROLE PROFILE",
        color="#7ee2ad",
        fontsize=12,
        fontweight="bold",
        va="top",
    )

    figure.text(
        0.06,
        0.925,
        role_name,
        color="white",
        fontsize=24,
        fontweight="bold",
        va="top",
    )

    figure.text(
        0.06,
        0.875,
        (
            f"Position: {position}  |  "
            f"Players: {len(members)}  |  "
            f"Common archetype: {common_archetype}"
        ),
        color="#b8d6c5",
        fontsize=10,
    )

    figure.text(
        0.06,
        0.855,
        (
            f"Avg age: {average_age:.1f}  |  "
            f"Avg rating: {average_rating:.2f}  |  "
            f"Avg role confidence: {average_confidence:.1f}%"
        ),
        color="#8eaf9e",
        fontsize=9,
    )

    figure.text(
        0.5,
        0.025,
        (
            "Radar values are percentile ranks within the same "
            "position group. z values show the role's mean "
            "standardized archetype score."
        ),
        ha="center",
        color="#7fa08f",
        fontsize=8.5,
    )

    figure.tight_layout(
        rect=[0.03, 0.06, 0.97, 0.82]
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
        facecolor=figure.get_facecolor(),
    )

    plt.close(figure)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--role",
        required=True,
    )

    parser.add_argument(
        "--roles",
        type=Path,
        default=DEFAULT_ROLES,
    )

    parser.add_argument(
        "--archetypes",
        type=Path,
        default=DEFAULT_ARCHETYPES,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )

    parser.add_argument(
        "--max-features",
        type=int,
        default=8,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    roles = pd.read_csv(
        args.roles,
        low_memory=False,
    )

    archetypes = pd.read_csv(
        args.archetypes,
        low_memory=False,
    )

    role_name = resolve_role_name(
        roles["final_role"],
        args.role,
    )

    (
        members,
        _member_archetypes,
        position,
        _selected_columns,
        role_means,
        role_percentiles,
    ) = prepare_role_profile(
        roles=roles,
        archetypes=archetypes,
        role_name=role_name,
    )

    output_path = (
        args.output_dir
        / f"{slugify(role_name)}_radar.png"
    )

    draw_radar(
        role_name=role_name,
        position=position,
        members=members,
        role_means=role_means,
        role_percentiles=role_percentiles,
        output_path=output_path,
        max_features=args.max_features,
    )

    print(
        f"Role radar oluÅturuldu: {output_path}"
    )


if __name__ == "__main__":
    main()
