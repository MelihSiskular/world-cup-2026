# -*- coding: utf-8 -*-
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


INPUT_FILE = Path(
    "/Users/melihsiskular/PycharmProjects/wc2026/data/processed/goal_minute_analysis/world_cup_2026_goals_sofascore.csv"
)

OUTPUT_TABLE = Path(
    "/Users/melihsiskular/PycharmProjects/wc2026/data/processed/goal_minute_analysis/"
    "team_goal_buckets.csv"
)

OUTPUT_CHART = Path(
    "/Users/melihsiskular/PycharmProjects/wc2026/docs/images/goal_minute/"
    "team_goal_buckets_chart.png"
)

MINUTE_INTERVALS = [
    (0, 10, "0-10"),
    (11, 20, "11-20"),
    (21, 30, "21-30"),
    (31, 40, "31-40"),
    (41, 45, "41-45+"),
    (46, 56, "46-56"),
    (57, 67, "57-67"),
    (68, 78, "68-78"),
    (79, 90, "79-90+"),
    (91, 105, "91-105+"),
    (106, 120, "106-120+"),
]


def assign_minute_bucket(
    minute: float | int | None,
) -> str:
    if pd.isna(minute):
        return "Bilinmiyor"

    minute = int(minute)

    for start, end, label in MINUTE_INTERVALS:
        if start <= minute <= end:
            return label

    return "Bilinmiyor"


def create_team_goal_bucket_table(
    goals_df: pd.DataFrame,
) -> pd.DataFrame:
    goals_df = goals_df.copy()

    goals_df["minute_bucket"] = (
        goals_df["minute"]
        .apply(assign_minute_bucket)
    )

    bucket_labels = [
        label
        for _, _, label in MINUTE_INTERVALS
    ]

    pivot = pd.crosstab(
        goals_df["scoring_country"],
        goals_df["minute_bucket"],
    )

    pivot = pivot.reindex(
        columns=bucket_labels,
        fill_value=0,
    )

    pivot["Toplam"] = pivot.sum(axis=1)

    return pivot.sort_values(
        by=["Toplam", "scoring_country"],
        ascending=[False, True],
    )


def create_team_goal_bucket_chart(
    pivot: pd.DataFrame,
) -> None:
    OUTPUT_CHART.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    plot_df = pivot.drop(
        columns="Toplam"
    )

    figure_height = max(
        11,
        len(plot_df) * 0.38,
    )

    figure, axis = plt.subplots(
        figsize=(17, figure_height)
    )

    left_values = pd.Series(
        0,
        index=plot_df.index,
        dtype=float,
    )

    for bucket in plot_df.columns:
        values = plot_df[bucket]

        bars = axis.barh(
            plot_df.index,
            values,
            left=left_values,
            label=bucket,
        )

        for bar, value in zip(
            bars,
            values,
        ):
            if value <= 0:
                continue

            axis.text(
                bar.get_x()
                + bar.get_width() / 2,
                bar.get_y()
                + bar.get_height() / 2,
                str(int(value)),
                ha="center",
                va="center",
                fontsize=8,
                fontweight="bold",
            )

        left_values = (
            left_values + values
        )

    axis.invert_yaxis()

    axis.set_title(
        (
            "2026 Dünya Kupası - "
            "Takımların Gol Dakikası Dağılımı"
        ),
        fontsize=18,
        fontweight="bold",
        pad=18,
    )

    axis.set_xlabel(
        "Gol Sayısı",
        fontsize=12,
    )

    axis.set_ylabel(
        "Takım",
        fontsize=12,
    )

    axis.grid(
        axis="x",
        linestyle="--",
        alpha=0.35,
    )

    axis.legend(
        title="Dakika Aralığı",
        bbox_to_anchor=(1.01, 1),
        loc="upper left",
    )

    for row_index, total in enumerate(
        pivot["Toplam"]
    ):
        axis.text(
            total + 0.15,
            row_index,
            f"Toplam: {int(total)}",
            va="center",
            fontsize=9,
            fontweight="bold",
        )

    max_total = pivot["Toplam"].max()

    axis.set_xlim(
        0,
        max_total + 4,
    )

    figure.tight_layout()

    figure.savefig(
        OUTPUT_CHART,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close(figure)


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Girdi dosyası bulunamadı: {INPUT_FILE}"
        )

    goals_df = pd.read_csv(
        INPUT_FILE,
        low_memory=False,
    )

    required_columns = {
        "scoring_country",
        "minute",
    }

    missing_columns = (
        required_columns
        .difference(goals_df.columns)
    )

    if missing_columns:
        raise ValueError(
            "Eksik kolonlar: "
            + ", ".join(
                sorted(missing_columns)
            )
        )

    pivot = (
        create_team_goal_bucket_table(
            goals_df
        )
    )

    OUTPUT_TABLE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    pivot.to_csv(
        OUTPUT_TABLE,
        encoding="utf-8-sig",
    )

    create_team_goal_bucket_chart(
        pivot
    )

    print("\nEn çok gol atan takımlar:")
    print(
        pivot.head(15).to_string()
    )

    print("\nDosyalar oluşturuldu:")
    print(f"- {OUTPUT_TABLE}")
    print(f"- {OUTPUT_CHART}")


if __name__ == "__main__":
    main()