# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, Rectangle
import numpy as np
import pandas as pd

"""
Run

python -m src.player_roles.create_role_map \
  --position M
  
python -m src.player_roles.create_role_map \
  --position M \
  --index-player-count 1

"""

DEFAULT_ROLES = Path(
    "data/processed/player_roles/player_roles.csv"
)

DEFAULT_OUTPUT_DIR = Path(
    "docs/images/player_roles/role_maps"
)

PITCH_LENGTH = 105.0
PITCH_WIDTH = 68.0


def to_pitch_x(value):
    return (
        pd.to_numeric(value, errors="coerce")
        / 100.0
        * PITCH_LENGTH
    )


def to_pitch_y(value):
    return (
        pd.to_numeric(value, errors="coerce")
        / 100.0
        * PITCH_WIDTH
    )


def draw_pitch(axis) -> None:
    axis.set_xlim(-3, PITCH_LENGTH + 3)
    axis.set_ylim(-3, PITCH_WIDTH + 3)
    axis.set_aspect("equal")
    axis.set_facecolor("#0b632d")

    stripe_width = PITCH_LENGTH / 10

    for index in range(10):
        if index % 2 == 0:
            axis.add_patch(
                Rectangle(
                    (index * stripe_width, 0),
                    stripe_width,
                    PITCH_WIDTH,
                    facecolor="#0d6b31",
                    edgecolor="none",
                    alpha=0.65,
                    zorder=0,
                )
            )

    axis.add_patch(
        Rectangle(
            (0, 0),
            PITCH_LENGTH,
            PITCH_WIDTH,
            fill=False,
            linewidth=2.0,
            edgecolor="white",
            zorder=1,
        )
    )

    axis.plot(
        [PITCH_LENGTH / 2, PITCH_LENGTH / 2],
        [0, PITCH_WIDTH],
        linewidth=1.7,
        color="white",
        zorder=1,
    )

    axis.add_patch(
        Circle(
            (PITCH_LENGTH / 2, PITCH_WIDTH / 2),
            9.15,
            fill=False,
            linewidth=1.7,
            edgecolor="white",
            zorder=1,
        )
    )

    axis.add_patch(
        Circle(
            (PITCH_LENGTH / 2, PITCH_WIDTH / 2),
            0.35,
            color="white",
            zorder=1,
        )
    )

    penalty_area_width = 40.32
    penalty_y = (PITCH_WIDTH - penalty_area_width) / 2

    axis.add_patch(
        Rectangle(
            (0, penalty_y),
            16.5,
            penalty_area_width,
            fill=False,
            linewidth=1.7,
            edgecolor="white",
            zorder=1,
        )
    )

    axis.add_patch(
        Rectangle(
            (PITCH_LENGTH - 16.5, penalty_y),
            16.5,
            penalty_area_width,
            fill=False,
            linewidth=1.7,
            edgecolor="white",
            zorder=1,
        )
    )

    goal_area_width = 18.32
    goal_area_y = (PITCH_WIDTH - goal_area_width) / 2

    axis.add_patch(
        Rectangle(
            (0, goal_area_y),
            5.5,
            goal_area_width,
            fill=False,
            linewidth=1.7,
            edgecolor="white",
            zorder=1,
        )
    )

    axis.add_patch(
        Rectangle(
            (PITCH_LENGTH - 5.5, goal_area_y),
            5.5,
            goal_area_width,
            fill=False,
            linewidth=1.7,
            edgecolor="white",
            zorder=1,
        )
    )

    axis.add_patch(
        Circle(
            (11, PITCH_WIDTH / 2),
            0.30,
            color="white",
            zorder=1,
        )
    )

    axis.add_patch(
        Circle(
            (PITCH_LENGTH - 11, PITCH_WIDTH / 2),
            0.30,
            color="white",
            zorder=1,
        )
    )

    axis.add_patch(
        Arc(
            (11, PITCH_WIDTH / 2),
            18.3,
            18.3,
            theta1=310,
            theta2=50,
            linewidth=1.5,
            edgecolor="white",
            zorder=1,
        )
    )

    axis.add_patch(
        Arc(
            (PITCH_LENGTH - 11, PITCH_WIDTH / 2),
            18.3,
            18.3,
            theta1=130,
            theta2=230,
            linewidth=1.5,
            edgecolor="white",
            zorder=1,
        )
    )

    goal_width = 7.32
    goal_y = (PITCH_WIDTH - goal_width) / 2

    axis.add_patch(
        Rectangle(
            (-2, goal_y),
            2,
            goal_width,
            fill=False,
            linewidth=1.5,
            edgecolor="white",
            clip_on=False,
            zorder=1,
        )
    )

    axis.add_patch(
        Rectangle(
            (PITCH_LENGTH, goal_y),
            2,
            goal_width,
            fill=False,
            linewidth=1.5,
            edgecolor="white",
            clip_on=False,
            zorder=1,
        )
    )

    axis.set_xticks([])
    axis.set_yticks([])

    for spine in axis.spines.values():
        spine.set_visible(False)


def weighted_role_center(
    group: pd.DataFrame,
) -> tuple[float, float]:
    weights = pd.to_numeric(
        group["total_position_points"],
        errors="coerce",
    ).fillna(1.0)

    x = pd.to_numeric(
        group["plot_x"],
        errors="coerce",
    )

    y = pd.to_numeric(
        group["plot_y"],
        errors="coerce",
    )

    valid = (
        x.notna()
        & y.notna()
        & weights.gt(0)
    )

    if not valid.any():
        return np.nan, np.nan

    return (
        float(
            np.average(
                x[valid],
                weights=weights[valid],
            )
        ),
        float(
            np.average(
                y[valid],
                weights=weights[valid],
            )
        ),
    )


def player_label_score(
    dataframe: pd.DataFrame,
) -> pd.Series:
    confidence = pd.to_numeric(
        dataframe["role_confidence_pct"],
        errors="coerce",
    ).fillna(0)

    rating = pd.to_numeric(
        dataframe["weighted_rating"],
        errors="coerce",
    ).fillna(0)

    minutes = pd.to_numeric(
        dataframe["minutes"],
        errors="coerce",
    ).fillna(0)

    return (
        confidence * 0.50
        + rating.div(10).mul(100) * 0.30
        + minutes.div(600).clip(0, 1).mul(100) * 0.20
    )


def representative_names(
    group: pd.DataFrame,
    count: int,
) -> list[str]:
    if count <= 0 or group.empty:
        return []

    ranked = group.copy()
    ranked["representative_score"] = (
        player_label_score(ranked)
    )

    return (
        ranked.sort_values(
            [
                "representative_score",
                "weighted_rating",
                "minutes",
            ],
            ascending=[False, False, False],
        )
        .head(count)["player_name"]
        .astype(str)
        .tolist()
    )


def prepare_position_data(
    roles: pd.DataFrame,
    position: str,
    minimum_role_size: int,
    maximum_roles: int | None,
) -> pd.DataFrame:
    dataframe = roles[
        roles["position"].eq(position)
    ].copy()

    dataframe["plot_x"] = to_pitch_x(
        dataframe["weighted_mean_x"]
    )

    dataframe["plot_y"] = to_pitch_y(
        dataframe["weighted_mean_y"]
    )

    dataframe = dataframe[
        dataframe["plot_x"].notna()
        & dataframe["plot_y"].notna()
    ].copy()

    role_counts = (
        dataframe["final_role"]
        .value_counts()
    )

    valid_roles = role_counts[
        role_counts.ge(minimum_role_size)
    ]

    if maximum_roles is not None:
        valid_roles = valid_roles.head(
            maximum_roles
        )

    dataframe = dataframe[
        dataframe["final_role"].isin(
            valid_roles.index
        )
    ].copy()

    if dataframe.empty:
        raise ValueError(
            "Filtrelerden sonra Ã§izilecek oyuncu kalmadÄ±."
        )

    return dataframe


def create_role_codes(
    dataframe: pd.DataFrame,
    position: str,
) -> dict[str, str]:
    counts = (
        dataframe["final_role"]
        .value_counts()
        .sort_values(ascending=False)
    )

    return {
        role: f"{position}{index:02d}"
        for index, role in enumerate(
            counts.index,
            start=1,
        )
    }


def role_color_mapping(
    role_names: list[str],
) -> dict[str, tuple]:
    cmap = plt.get_cmap(
        "tab20",
        max(len(role_names), 1),
    )

    return {
        role: cmap(index)
        for index, role in enumerate(
            role_names
        )
    }


def draw_overview(
    roles: pd.DataFrame,
    position: str,
    output_path: Path,
    minimum_role_size: int,
    maximum_roles: int | None,
    labels_per_role: int,
    index_player_count: int,
) -> None:
    dataframe = prepare_position_data(
        roles=roles,
        position=position,
        minimum_role_size=minimum_role_size,
        maximum_roles=maximum_roles,
    )

    codes = create_role_codes(
        dataframe,
        position,
    )

    role_names = list(codes.keys())
    colors = role_color_mapping(role_names)

    # Yan panelde oyuncu gÃ¶sterilecekse paneli biraz geniÅlet.
    panel_ratio = 2.35 if index_player_count > 0 else 2.0

    figure = plt.figure(
        figsize=(22, 11),
        facecolor="#06160d",
    )

    grid = figure.add_gridspec(
        1,
        2,
        width_ratios=[5.3, panel_ratio],
        wspace=0.035,
    )

    pitch_axis = figure.add_subplot(
        grid[0, 0]
    )

    panel_axis = figure.add_subplot(
        grid[0, 1]
    )

    draw_pitch(pitch_axis)

    role_centers = []

    for role_name in role_names:
        group = dataframe[
            dataframe["final_role"].eq(
                role_name
            )
        ].copy()

        color = colors[role_name]

        pitch_axis.scatter(
            group["plot_x"],
            group["plot_y"],
            s=42,
            alpha=0.48,
            color=color,
            edgecolor="black",
            linewidth=0.25,
            zorder=3,
        )

        center_x, center_y = (
            weighted_role_center(group)
        )

        names = representative_names(
            group,
            index_player_count,
        )

        role_centers.append(
            {
                "role": role_name,
                "code": codes[role_name],
                "count": len(group),
                "x": center_x,
                "y": center_y,
                "color": color,
                "representatives": names,
            }
        )

        pitch_axis.scatter(
            [center_x],
            [center_y],
            s=230,
            marker="X",
            color=color,
            edgecolor="black",
            linewidth=1.35,
            zorder=7,
        )

        pitch_axis.text(
            center_x,
            center_y,
            codes[role_name],
            ha="center",
            va="center",
            fontsize=7.5,
            fontweight="bold",
            color="white",
            zorder=8,
        )

        if labels_per_role > 0:
            group["label_score"] = (
                player_label_score(group)
            )

            representatives = (
                group.sort_values(
                    "label_score",
                    ascending=False,
                )
                .head(labels_per_role)
            )

            for _, player in representatives.iterrows():
                pitch_axis.annotate(
                    str(player["player_name"]),
                    (
                        player["plot_x"],
                        player["plot_y"],
                    ),
                    xytext=(5, 5),
                    textcoords="offset points",
                    fontsize=7,
                    color="white",
                    bbox={
                        "boxstyle": "round,pad=0.15",
                        "facecolor": "#07160e",
                        "edgecolor": "none",
                        "alpha": 0.65,
                    },
                    zorder=6,
                )

    panel_axis.set_facecolor("#0a2115")
    panel_axis.set_xlim(0, 1)
    panel_axis.set_ylim(0, 1)
    panel_axis.axis("off")

    panel_axis.text(
        0.04,
        0.965,
        "ROLE INDEX",
        fontsize=14,
        fontweight="bold",
        color="#7ee2ad",
        va="top",
    )

    subtitle = (
        "Codes on the pitch represent weighted role centers."
    )

    if index_player_count > 0:
        subtitle += (
            " Representative players are listed below each role."
        )

    panel_axis.text(
        0.04,
        0.925,
        textwrap.fill(
            subtitle,
            width=55,
        ),
        fontsize=8.3,
        color="#9bb7a7",
        va="top",
    )

    rows = sorted(
        role_centers,
        key=lambda item: item["code"],
    )

    # Temsilci oyuncu sayÄ±sÄ± arttÄ±kÃ§a satÄ±r yÃ¼ksekliÄini artÄ±r.
    per_role_lines = (
        1.0
        + max(index_player_count, 0) * 0.55
    )

    row_height = min(
        0.052 * per_role_lines,
        0.82 / max(len(rows), 1),
    )

    y = 0.855

    for item in rows:
        panel_axis.scatter(
            [0.06],
            [y],
            s=90,
            marker="X",
            color=item["color"],
            edgecolor="black",
            linewidth=0.7,
        )

        panel_axis.text(
            0.11,
            y,
            item["code"],
            fontsize=9,
            fontweight="bold",
            color="white",
            va="center",
        )

        role_text = textwrap.fill(
            f"{item['role']} ({item['count']})",
            width=34,
        )

        panel_axis.text(
            0.21,
            y,
            role_text,
            fontsize=8.1,
            color="#e8fff2",
            va="center",
        )

        if item["representatives"]:
            representative_text = ", ".join(
                item["representatives"]
            )

            panel_axis.text(
                0.21,
                y - min(row_height * 0.42, 0.018),
                textwrap.fill(
                    representative_text,
                    width=39,
                ),
                fontsize=7.1,
                color="#85caa5",
                va="top",
                style="italic",
            )

        y -= row_height

    title_map = {
        "G": "Goalkeeper Role Map",
        "D": "Defender Role Map",
        "M": "Midfielder Role Map",
        "F": "Forward Role Map",
    }

    figure.text(
        0.035,
        0.965,
        "PLAYER ROLE MAP",
        fontsize=13,
        fontweight="bold",
        color="#7ee2ad",
        va="top",
    )

    figure.text(
        0.035,
        0.922,
        title_map[position],
        fontsize=27,
        fontweight="bold",
        color="white",
        va="top",
    )

    figure.text(
        0.035,
        0.875,
        (
            f"Players: {len(dataframe)}  |  "
            f"Roles: {dataframe['final_role'].nunique()}  |  "
            f"Minimum role size: {minimum_role_size}"
        ),
        fontsize=10,
        color="#b5d0c0",
    )



    figure.tight_layout(
        rect=[0.02, 0.045, 0.99, 0.86]
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
        "--position",
        choices=["G", "D", "M", "F"],
        default="M",
    )

    parser.add_argument(
        "--roles",
        type=Path,
        default=DEFAULT_ROLES,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )

    parser.add_argument(
        "--minimum-role-size",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--maximum-roles",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--labels-per-role",
        type=int,
        default=0,
        help=(
            "Saha iÃ§ine her rol iÃ§in yazÄ±lacak oyuncu sayÄ±sÄ±. "
            "KalabalÄ±k olmamasÄ± iÃ§in varsayÄ±lan 0."
        ),
    )

    parser.add_argument(
        "--index-player-count",
        type=int,
        default=0,
        choices=[0, 1, 2],
        help=(
            "Role Index iÃ§inde her rolÃ¼n altÄ±nda gÃ¶sterilecek "
            "temsilci oyuncu sayÄ±sÄ±."
        ),
    )

    return parser.parse_args()


def main():
    args = parse_args()

    roles = pd.read_csv(
        args.roles,
        low_memory=False,
    )

    suffix = (
        f"_index_players_{args.index_player_count}"
        if args.index_player_count > 0
        else ""
    )

    output_path = (
        args.output_dir
        / (
            f"{args.position.lower()}_role_map"
            f"{suffix}.png"
        )
    )

    draw_overview(
        roles=roles,
        position=args.position,
        output_path=output_path,
        minimum_role_size=args.minimum_role_size,
        maximum_roles=args.maximum_roles,
        labels_per_role=args.labels_per_role,
        index_player_count=args.index_player_count,
    )

    print(
        f"Role map oluÅturuldu: {output_path}"
    )


if __name__ == "__main__":
    main()
