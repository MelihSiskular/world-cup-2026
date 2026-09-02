from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import to_hex
from matplotlib.patches import Arc, Circle, Rectangle

"""
Final-role pitch maps and their web-readable role indexes.

Examples
--------
python -m src.player_roles.create_role_map --position D
python -m src.player_roles.create_role_map --position M
python -m src.player_roles.create_role_map --position F
"""

DEFAULT_ROLES = Path("data/processed/player_roles/player_roles.csv")
DEFAULT_OUTPUT_DIR = Path("docs/images/player_roles/role_maps")

PITCH_LENGTH = 105.0
PITCH_WIDTH = 68.0


def to_pitch_x(value: pd.Series) -> pd.Series:
    return pd.to_numeric(value, errors="coerce") / 100.0 * PITCH_LENGTH


def to_pitch_y(value: pd.Series) -> pd.Series:
    return pd.to_numeric(value, errors="coerce") / 100.0 * PITCH_WIDTH


def draw_pitch(axis) -> None:
    axis.set_xlim(-3, PITCH_LENGTH + 3)
    axis.set_ylim(-3, PITCH_WIDTH + 3)
    axis.set_aspect("equal")
    axis.set_facecolor("none")

    stripe_width = PITCH_LENGTH / 10
    stripe_colors = ("#0b632d", "#0e6d35")
    for index in range(10):
        axis.add_patch(
            Rectangle(
                (index * stripe_width, 0),
                stripe_width,
                PITCH_WIDTH,
                facecolor=stripe_colors[index % len(stripe_colors)],
                edgecolor="none",
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
    for x_value in (0, PITCH_LENGTH - 16.5):
        axis.add_patch(
            Rectangle(
                (x_value, penalty_y),
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
    for x_value in (0, PITCH_LENGTH - 5.5):
        axis.add_patch(
            Rectangle(
                (x_value, goal_area_y),
                5.5,
                goal_area_width,
                fill=False,
                linewidth=1.7,
                edgecolor="white",
                zorder=1,
            )
        )

    for x_value in (11, PITCH_LENGTH - 11):
        axis.add_patch(
            Circle(
                (x_value, PITCH_WIDTH / 2),
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
    for x_value in (-2, PITCH_LENGTH):
        axis.add_patch(
            Rectangle(
                (x_value, goal_y),
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


def weighted_role_center(group: pd.DataFrame) -> tuple[float, float]:
    weights = pd.to_numeric(group["total_position_points"], errors="coerce").fillna(1.0)
    x = pd.to_numeric(group["plot_x"], errors="coerce")
    y = pd.to_numeric(group["plot_y"], errors="coerce")
    valid = x.notna() & y.notna() & weights.gt(0)

    if not valid.any():
        return np.nan, np.nan

    return (
        float(np.average(x[valid], weights=weights[valid])),
        float(np.average(y[valid], weights=weights[valid])),
    )


def player_label_score(dataframe: pd.DataFrame) -> pd.Series:
    confidence = pd.to_numeric(dataframe["role_confidence_pct"], errors="coerce").fillna(0)
    rating = pd.to_numeric(dataframe["weighted_rating"], errors="coerce").fillna(0)
    minutes = pd.to_numeric(dataframe["minutes"], errors="coerce").fillna(0)

    return (
        confidence * 0.50
        + rating.div(10).mul(100) * 0.30
        + minutes.div(600).clip(0, 1).mul(100) * 0.20
    )


def prepare_position_data(
    roles: pd.DataFrame,
    position: str,
    minimum_role_size: int,
    maximum_roles: int | None,
) -> pd.DataFrame:
    dataframe = roles[roles["position"].eq(position)].copy()
    dataframe["plot_x"] = to_pitch_x(dataframe["weighted_mean_x"])
    dataframe["plot_y"] = to_pitch_y(dataframe["weighted_mean_y"])
    dataframe = dataframe[dataframe["plot_x"].notna() & dataframe["plot_y"].notna()].copy()

    counts = (
        dataframe.groupby("final_role", dropna=False)
        .size()
        .rename("player_count")
        .reset_index()
        .sort_values(
            ["player_count", "final_role"],
            ascending=[False, True],
        )
    )
    counts = counts[counts["player_count"].ge(minimum_role_size)]
    if maximum_roles is not None:
        counts = counts.head(maximum_roles)

    dataframe = dataframe[dataframe["final_role"].isin(counts["final_role"])].copy()
    if dataframe.empty:
        raise ValueError("Filtrelerden sonra çizilecek oyuncu kalmadı.")

    return dataframe


def create_role_codes(dataframe: pd.DataFrame, position: str) -> dict[str, str]:
    counts = (
        dataframe.groupby("final_role")
        .size()
        .rename("player_count")
        .reset_index()
        .sort_values(
            ["player_count", "final_role"],
            ascending=[False, True],
        )
    )
    return {
        role: f"{position}{index:02d}" for index, role in enumerate(counts["final_role"], start=1)
    }


def role_color_mapping(role_names: list[str]) -> dict[str, tuple]:
    palette = [
        *plt.get_cmap("tab20").colors,
        *plt.get_cmap("tab20b").colors,
        *plt.get_cmap("tab20c").colors,
    ]
    return {role: palette[index % len(palette)] for index, role in enumerate(role_names)}


def draw_overview(
    roles: pd.DataFrame,
    position: str,
    output_path: Path,
    minimum_role_size: int,
    maximum_roles: int | None,
    labels_per_role: int,
) -> None:
    dataframe = prepare_position_data(
        roles=roles,
        position=position,
        minimum_role_size=minimum_role_size,
        maximum_roles=maximum_roles,
    )
    codes = create_role_codes(dataframe, position)
    role_names = list(codes)
    colors = role_color_mapping(role_names)

    figure, pitch_axis = plt.subplots(
        figsize=(13.5, 8.7),
        facecolor="none",
    )
    draw_pitch(pitch_axis)
    role_index: list[dict[str, object]] = []

    for role_name in role_names:
        group = dataframe[dataframe["final_role"].eq(role_name)].copy()
        color = colors[role_name]
        pitch_axis.scatter(
            group["plot_x"],
            group["plot_y"],
            s=58,
            alpha=0.62,
            color=color,
            edgecolor="#07160e",
            linewidth=0.25,
            zorder=3,
        )
        center_x, center_y = weighted_role_center(group)
        pitch_axis.scatter(
            [center_x],
            [center_y],
            s=340,
            marker="X",
            color=color,
            edgecolor="#07160e",
            linewidth=1.35,
            zorder=7,
        )
        code_text = pitch_axis.text(
            center_x,
            center_y,
            codes[role_name],
            ha="center",
            va="center",
            fontsize=9.0,
            fontweight="bold",
            color="white",
            zorder=8,
        )
        code_text.set_path_effects(
            [
                path_effects.Stroke(linewidth=2.1, foreground="#07160e"),
                path_effects.Normal(),
            ]
        )

        if labels_per_role > 0:
            group["label_score"] = player_label_score(group)
            representatives = group.sort_values("label_score", ascending=False).head(
                labels_per_role
            )
            for _, player in representatives.iterrows():
                pitch_axis.annotate(
                    str(player["player_name"]),
                    (player["plot_x"], player["plot_y"]),
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

        role_index.append(
            {
                "code": codes[role_name],
                "name": role_name,
                "player_count": int(len(group)),
                "color": to_hex(color),
                "center_x_pct": round(center_x / PITCH_LENGTH * 100, 4),
                "center_y_pct": round(center_y / PITCH_WIDTH * 100, 4),
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.tight_layout(pad=0.15)
    figure.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight",
        pad_inches=0.03,
        transparent=True,
    )
    plt.close(figure)

    payload = {
        "position": position,
        "player_count": int(len(dataframe)),
        "role_count": int(len(role_index)),
        "minimum_role_size": minimum_role_size,
        "roles": role_index,
    }
    output_path.with_suffix(".json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--position", choices=["G", "D", "M", "F"], default="M")
    parser.add_argument("--roles", type=Path, default=DEFAULT_ROLES)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--minimum-role-size", type=int, default=1)
    parser.add_argument("--maximum-roles", type=int, default=None)
    parser.add_argument(
        "--labels-per-role",
        type=int,
        default=0,
        help="Saha içine her rol için yazılacak oyuncu sayısı.",
    )
    parser.add_argument(
        "--index-player-count",
        type=int,
        default=0,
        choices=[0, 1, 2],
        help="Geriye dönük uyumluluk için korunur; web rol indeksini etkilemez.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    roles = pd.read_csv(args.roles, low_memory=False)
    output_path = args.output_dir / f"{args.position.lower()}_role_map.png"
    draw_overview(
        roles=roles,
        position=args.position,
        output_path=output_path,
        minimum_role_size=args.minimum_role_size,
        maximum_roles=args.maximum_roles,
        labels_per_role=args.labels_per_role,
    )
    print(f"Role map oluşturuldu: {output_path}")
    print(f"Role index oluşturuldu: {output_path.with_suffix('.json')}")


if __name__ == "__main__":
    main()
