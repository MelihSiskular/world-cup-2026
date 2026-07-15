# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


DEFAULT_ARCHETYPES = Path(
    "/Users/melihsiskular/PycharmProjects/wc2026/data/processed/player_archetypes/player_archetypes.csv"
)

DEFAULT_OUTPUT_DIR = Path(
    "/Users/melihsiskular/PycharmProjects/wc2026/docs/images/player_archetypes"
)


def create_archetype_map(
    dataframe: pd.DataFrame,
    position: str,
    output_path: Path,
    label_top_n: int = 3,
) -> None:
    position_df = dataframe[
        dataframe["position"].eq(position)
    ].copy()

    if position_df.empty:
        raise ValueError(
            f"{position} pozisyonunda oyuncu bulunamadı."
        )

    required = {
        "archetype_pca_1",
        "archetype_pca_2",
        "archetype",
        "player_name",
        "minutes",
        "weighted_rating",
    }

    missing = required.difference(
        position_df.columns
    )

    if missing:
        raise ValueError(
            "Eksik kolonlar: "
            + ", ".join(sorted(missing))
        )

    figure, axis = plt.subplots(
        figsize=(15, 10)
    )

    for archetype, group in position_df.groupby(
        "archetype"
    ):
        axis.scatter(
            group["archetype_pca_1"],
            group["archetype_pca_2"],
            s=55,
            alpha=0.72,
            label=f"{archetype} ({len(group)})",
        )

        # Her archetype için merkez
        center_x = group[
            "archetype_pca_1"
        ].mean()
        center_y = group[
            "archetype_pca_2"
        ].mean()

        axis.scatter(
            center_x,
            center_y,
            s=240,
            marker="X",
            edgecolor="black",
            linewidth=1.1,
            zorder=5,
        )

        axis.annotate(
            archetype,
            (center_x, center_y),
            xytext=(7, 7),
            textcoords="offset points",
            fontsize=10,
            fontweight="bold",
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": "white",
                "alpha": 0.85,
                "edgecolor": "gray",
            },
            zorder=6,
        )

        # Rating ve dakikaya göre öne çıkan oyuncuları etiketle
        label_group = (
            group.sort_values(
                [
                    "weighted_rating",
                    "minutes",
                ],
                ascending=[False, False],
            )
            .head(label_top_n)
        )

        for _, player in label_group.iterrows():
            axis.annotate(
                str(player["player_name"]),
                (
                    player["archetype_pca_1"],
                    player["archetype_pca_2"],
                ),
                xytext=(4, -10),
                textcoords="offset points",
                fontsize=8,
                alpha=0.9,
            )

    position_titles = {
        "G": "Goalkeeper Archetype Map",
        "D": "Defender Archetype Map",
        "M": "Midfielder Archetype Map",
        "F": "Forward Archetype Map",
    }

    axis.set_title(
        position_titles.get(
            position,
            f"{position} Archetype Map",
        ),
        fontsize=18,
        fontweight="bold",
        pad=18,
    )

    axis.set_xlabel(
        "PCA Component 1",
        fontsize=11,
    )

    axis.set_ylabel(
        "PCA Component 2",
        fontsize=11,
    )

    axis.grid(
        linestyle="--",
        alpha=0.28,
    )

    axis.legend(
        title="Archetypes",
        bbox_to_anchor=(1.02, 1),
        loc="upper left",
        fontsize=9,
    )

    figure.text(
        0.5,
        0.015,
        (
            "Each point represents one player. "
            "X markers show archetype centers. "
            "PCA is used only for two-dimensional visualization."
        ),
        ha="center",
        fontsize=9,
        color="dimgray",
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    figure.tight_layout(
        rect=[0, 0.035, 0.82, 1]
    )

    figure.savefig(
        output_path,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(figure)


def create_all_maps(
    dataframe: pd.DataFrame,
    output_dir: Path,
    label_top_n: int,
) -> None:
    filenames = {
        "G": "goalkeeper_archetype_map.png",
        "D": "defender_archetype_map.png",
        "M": "midfielder_archetype_map.png",
        "F": "forward_archetype_map.png",
    }

    for position, filename in filenames.items():
        if not dataframe[
            "position"
        ].eq(position).any():
            continue

        output_path = output_dir / filename

        create_archetype_map(
            dataframe=dataframe,
            position=position,
            output_path=output_path,
            label_top_n=label_top_n,
        )

        print(
            f"{position} haritası oluşturuldu: "
            f"{output_path}"
        )


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--position",
        choices=["G", "D", "M", "F", "ALL"],
        default="ALL",
    )

    parser.add_argument(
        "--label-top-n",
        type=int,
        default=3,
        help=(
            "Her archetype içinde grafikte "
            "etiketlenecek oyuncu sayısı."
        ),
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

    return parser.parse_args()


def main():
    args = parse_args()

    dataframe = pd.read_csv(
        args.archetypes,
        low_memory=False,
    )

    if args.position == "ALL":
        create_all_maps(
            dataframe=dataframe,
            output_dir=args.output_dir,
            label_top_n=args.label_top_n,
        )
        return

    filename = {
        "G": "goalkeeper_archetype_map.png",
        "D": "defender_archetype_map.png",
        "M": "midfielder_archetype_map.png",
        "F": "forward_archetype_map.png",
    }[args.position]

    output_path = (
        args.output_dir / filename
    )

    create_archetype_map(
        dataframe=dataframe,
        position=args.position,
        output_path=output_path,
        label_top_n=args.label_top_n,
    )

    print(
        f"Harita oluşturuldu: {output_path}"
    )


if __name__ == "__main__":
    main()
