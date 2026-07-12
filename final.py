import pandas as pd
import matplotlib.pyplot as plt


CSV_FILE = "world_cup_2026_goals_sofascore.csv"

df = pd.read_csv(CSV_FILE)


# =========================
# DAKİKA ARALIĞI AYARI
# =========================

# Burayı istediğin gibi değiştirebilirsin.
# Bu aralıklar "ana dakika" üzerinden çalışır.
intervals = [
    (0, 10, "0-10"),
    (11, 20, "11-20"),
    (21, 30, "21-30"),
    (31, 40, "31-40"),
    (41, 45, "41-45+"),
    (46, 56, "46-56"),
    (57, 67, "57-67"),
    (68, 78, "68-78"),
    (79, 90, "79-90"),
    (91, 100, "91-100"),
    (101, 105, "101-105+"),
    (106, 116, "106-116"),
    (117, 120, "117-120+"),
]


def assign_bucket(row):
    minute = row["minute"]

    if pd.isna(minute):
        return "Bilinmiyor"

    minute = int(minute)

    for start, end, label in intervals:
        if start <= minute <= end:
            return label

    return "Bilinmiyor"


df["custom_minute_bucket"] = df.apply(assign_bucket, axis=1)

labels = [label for _, _, label in intervals]

summary = (
    df["custom_minute_bucket"]
    .value_counts()
    .reindex(labels)
    .fillna(0)
    .astype(int)
    .reset_index()
)

summary.columns = ["minute_bucket", "goal_count"]

summary["percentage"] = (
    summary["goal_count"] / summary["goal_count"].sum() * 100
).round(2)

print("\nDakika aralığı dağılımı:")
print(summary)

summary.to_csv(
    "custom_goal_minute_distribution.csv",
    index=False,
    encoding="utf-8-sig"
)


# =========================
# GRAFİK
# =========================

plt.figure(figsize=(12, 7))

bars = plt.bar(
    summary["minute_bucket"],
    summary["goal_count"]
)

plt.title(
    "2026 Dünya Kupası Gol Dakikası Dağılımı",
    fontsize=16,
    fontweight="bold"
)

plt.xlabel("Dakika Aralığı", fontsize=12)
plt.ylabel("Gol Sayısı", fontsize=12)

plt.grid(axis="y", linestyle="--", alpha=0.45)

max_goal = summary["goal_count"].max()
plt.ylim(0, max_goal + max(8, max_goal * 0.18))

plt.xticks(rotation=30)

for bar, goal, pct in zip(
    bars,
    summary["goal_count"],
    summary["percentage"]
):
    height = bar.get_height()

    if goal > 0:
        # Bar içindeki gol sayısı
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height / 2,
            f"{goal}",
            ha="center",
            va="center",
            fontsize=12,
            fontweight="bold",
            color="white"
        )

        # Bar üstündeki yüzde
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height + max_goal * 0.025,
            f"%{pct:.2f}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold"
        )

plt.tight_layout()

# savefig, show'dan önce olmalı
plt.savefig(
    "world_cup_data/goal_minute_distribution_chart.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()