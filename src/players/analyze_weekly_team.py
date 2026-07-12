"""
Dünya Kupası oyuncu-maç verisinden:

- Her aşama ve pozisyon için en yüksek ratingli ilk N oyuncuyu çıkarır.
- Farklı formasyonlara göre aşamanın takımını oluşturur.
- Sonuçları CSV olarak kaydeder.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


POSITIONS = ["G", "D", "M", "F"]

# Veride yalnızca G/D/M/F bulunduğu için formasyonlar bu dört kullandım
FORMATIONS = {
    "4-3-3": {"G": 1, "D": 4, "M": 3, "F": 3},
    "4-4-2": {"G": 1, "D": 4, "M": 4, "F": 2},
    "4-2-3-1": {"G": 1, "D": 4, "M": 2, "F": 4},
    "3-4-3": {"G": 1, "D": 3, "M": 4, "F": 3},
    "3-5-2": {"G": 1, "D": 3, "M": 5, "F": 2},
    "5-3-2": {"G": 1, "D": 5, "M": 3, "F": 2},
    "4-5-1": {"G": 1, "D": 4, "M": 5, "F": 1},
}


def clean_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def resolve_stage(round_number, round_name):
    """

    Sofascore üzerinden gelenleri sıraladım:
        1  -> Grup 1. maç
        2  -> Grup 2. maç
        3  -> Grup 3. maç
        6  -> Son 32
        5  -> Son 16
        27 -> Çeyrek final
        28 -> Yarı final
        50 -> Üçüncülük maçı
        29 -> Final
    """
    try:
        number = int(float(round_number))
    except (TypeError, ValueError):
        number = -1

    name = clean_text(round_name)
    normalized_name = name.casefold()

    if not name and number in {1, 2, 3}:
        return number, f"GROUP_MD{number}", f"Grup {number}. Maçları"

    named_stages = {
        "round of 32": (4, "R32", "Son 32"),
        "round of 16": (5, "R16", "Son 16"),
        "quarterfinals": (6, "QF", "Çeyrek Final"),
        "semifinals": (7, "SF", "Yarı Final"),
        "match for 3rd place": (8, "THIRD_PLACE", "Üçüncülük Maçı"),
        "final": (9, "FINAL", "Final"),
    }

    if normalized_name in named_stages:
        return named_stages[normalized_name]

    # Yeni veya beklenmeyen bir aşama gelirse veri kaybolmasın.
    fallback_label = name or f"Round {number}"
    return 90 + max(number, 0), f"UNKNOWN_{number}", fallback_label


def load_and_prepare(input_file: Path, min_minutes: float) -> pd.DataFrame:
    df = pd.read_csv(input_file, low_memory=False)

    required_columns = {
        "event_id",
        "player_id",
        "player_name",
        "round_number",
        "round_name",
        "match_status",
        "national_team_name",
        "opponent_team_name",
        "stat_rating",
        "stat_minutesPlayed",
    }

    missing = sorted(required_columns.difference(df.columns))
    if missing:
        raise ValueError(
            "Gerekli kolonlar eksik: " + ", ".join(missing)
        )


    numeric_columns = [
        "event_id",
        "player_id",
        "round_number",
        "stat_rating",
        "stat_minutesPlayed",
        "stat_goals",
        "stat_goalAssist",
        "stat_expectedGoals",
        "stat_expectedAssists",
    ]

    for column in numeric_columns:
        if column not in df.columns:
            df[column] = 0
        df[column] = pd.to_numeric(df[column], errors="coerce")


    lineup_position = (
        df["lineup_position"]
        if "lineup_position" in df.columns
        else pd.Series(index=df.index, dtype="object")
    )
    primary_position = (
        df["player_primary_position"]
        if "player_primary_position" in df.columns
        else pd.Series(index=df.index, dtype="object")
    )

    df["analysis_position"] = (
        lineup_position
        .fillna(primary_position)
        .astype("string")
        .str.strip()
        .str.upper()
    )

    stage_values = df.apply(
        lambda row: resolve_stage(
            row["round_number"],
            row["round_name"],
        ),
        axis=1,
        result_type="expand",
    )
    stage_values.columns = [
        "stage_order",
        "stage_code",
        "stage_label",
    ]

    df = pd.concat([df, stage_values], axis=1)

    # Aynı event-oyuncu kaydı yanlışlıkla iki kere varsa tekilleştir.
    df = df.drop_duplicates(
        subset=["event_id", "player_id"],
        keep="last",
    )

    # Sadece tamamlanmış maçlar ve gerçekten süre alan oyuncular.
    pool = df[
        df["match_status"].astype(str).str.lower().eq("finished")
        & df["analysis_position"].isin(POSITIONS)
        & df["stat_rating"].notna()
        & df["stat_minutesPlayed"].fillna(0).ge(min_minutes)
        & df["stat_minutesPlayed"].fillna(0).gt(0)
    ].copy()

    for column in [
        "stat_goals",
        "stat_goalAssist",
        "stat_expectedGoals",
        "stat_expectedAssists",
    ]:
        pool[column] = pool[column].fillna(0)

    return pool


def sort_player_pool(df: pd.DataFrame) -> pd.DataFrame:

    return df.sort_values(
        by=[
            "stage_order",
            "analysis_position",
            "stat_rating",
            "stat_minutesPlayed",
            "stat_goals",
            "stat_goalAssist",
            "player_name",
        ],
        ascending=[
            True,
            True,
            False,
            False,
            False,
            False,
            True,
        ],
        kind="stable",
    )


def create_top_candidates(
    player_pool: pd.DataFrame,
    top_n: int,
) -> pd.DataFrame:
    ordered = sort_player_pool(player_pool)

    top = (
        ordered
        .groupby(
            ["stage_order", "stage_code", "stage_label", "analysis_position"],
            sort=False,
            group_keys=False,
        )
        .head(top_n)
        .copy()
    )

    top["position_rank"] = (
        top
        .groupby(
            ["stage_order", "analysis_position"],
            sort=False,
        )
        .cumcount()
        .add(1)
    )

    selected_columns = [
        "stage_order",
        "stage_code",
        "stage_label",
        "round_number",
        "round_name",
        "analysis_position",
        "position_rank",
        "event_id",
        "player_id",
        "player_name",
        "national_team_name",
        "opponent_team_name",
        "home_team_name",
        "away_team_name",
        "home_score",
        "away_score",
        "appearance_type",
        "is_starter",
        "stat_minutesPlayed",
        "stat_rating",
        "stat_goals",
        "stat_goalAssist",
        "stat_expectedGoals",
        "stat_expectedAssists",
    ]

    existing_columns = [
        column for column in selected_columns if column in top.columns
    ]

    return top[existing_columns].reset_index(drop=True)


def create_formation_teams(
    player_pool: pd.DataFrame,
) -> pd.DataFrame:
    ordered = sort_player_pool(player_pool)
    rows = []

    stage_columns = ["stage_order", "stage_code", "stage_label"]

    for stage_values, stage_df in ordered.groupby(stage_columns, sort=True):
        stage_order, stage_code, stage_label = stage_values

        for formation_name, requirements in FORMATIONS.items():
            for position in POSITIONS:
                needed = requirements[position]

                selected = (
                    stage_df[
                        stage_df["analysis_position"].eq(position)
                    ]
                    .head(needed)
                    .copy()
                )

                for slot_number, (_, player) in enumerate(
                    selected.iterrows(),
                    start=1,
                ):
                    rows.append(
                        {
                            "stage_order": stage_order,
                            "stage_code": stage_code,
                            "stage_label": stage_label,
                            "formation": formation_name,
                            "formation_slot": f"{position}{slot_number}",
                            "position": position,
                            "position_order": POSITIONS.index(position) + 1,
                            "event_id": player["event_id"],
                            "player_id": player["player_id"],
                            "player_name": player["player_name"],
                            "national_team_name": player["national_team_name"],
                            "opponent_team_name": player["opponent_team_name"],
                            "minutes_played": player["stat_minutesPlayed"],
                            "rating": player["stat_rating"],
                            "goals": player["stat_goals"],
                            "assists": player["stat_goalAssist"],
                            "xg": player["stat_expectedGoals"],
                            "xa": player["stat_expectedAssists"],
                        }
                    )

    teams = pd.DataFrame(rows)

    if teams.empty:
        return teams

    return teams.sort_values(
        [
            "stage_order",
            "formation",
            "position_order",
            "rating",
        ],
        ascending=[True, True, True, False],
    ).reset_index(drop=True)


def create_formation_summary(
    formation_teams: pd.DataFrame,
) -> pd.DataFrame:
    if formation_teams.empty:
        return pd.DataFrame()

    summary = (
        formation_teams
        .groupby(
            [
                "stage_order",
                "stage_code",
                "stage_label",
                "formation",
            ],
            as_index=False,
        )
        .agg(
            selected_player_count=("player_id", "count"),
            average_rating=("rating", "mean"),
            total_rating=("rating", "sum"),
            total_goals=("goals", "sum"),
            total_assists=("assists", "sum"),
            total_xg=("xg", "sum"),
            total_xa=("xa", "sum"),
        )
    )

    summary["average_rating"] = summary["average_rating"].round(3)
    summary["total_rating"] = summary["total_rating"].round(2)
    summary["total_xg"] = summary["total_xg"].round(3)
    summary["total_xa"] = summary["total_xa"].round(3)

    return summary.sort_values(
        ["stage_order", "average_rating"],
        ascending=[True, False],
    ).reset_index(drop=True)


def create_stage_summary(
    player_pool: pd.DataFrame,
) -> pd.DataFrame:
    if player_pool.empty:
        return pd.DataFrame()

    event_summary = (
        player_pool
        .groupby(
            [
                "stage_order",
                "stage_code",
                "stage_label",
                "round_number",
                "round_name",
            ],
            dropna=False,
            as_index=False,
        )
        .agg(
            finished_match_count=("event_id", "nunique"),
            rated_player_count=("player_id", "count"),
            unique_player_count=("player_id", "nunique"),
            average_rating=("stat_rating", "mean"),
        )
    )

    event_summary["average_rating"] = (
        event_summary["average_rating"].round(3)
    )

    return event_summary.sort_values("stage_order").reset_index(drop=True)


def save_outputs(
    output_dir: Path,
    stage_summary: pd.DataFrame,
    top_candidates: pd.DataFrame,
    formation_teams: pd.DataFrame,
    formation_summary: pd.DataFrame,
):
    output_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "stage_summary.csv": stage_summary,
        "top_players_by_stage_position.csv": top_candidates,
        "teams_by_formation.csv": formation_teams,
        "formation_summary.csv": formation_summary,
    }

    for filename, dataframe in files.items():
        path = output_dir / filename
        dataframe.to_csv(
            path,
            index=False,
            encoding="utf-8-sig",
        )
        print(f"Yazıldı: {path} ({len(dataframe)} satır)")


def print_example(
    top_candidates: pd.DataFrame,
    stage_order: int = 1,
    position: str = "D",
):
    example = top_candidates[
        top_candidates["stage_order"].eq(stage_order)
        & top_candidates["analysis_position"].eq(position)
    ]

    columns = [
        "position_rank",
        "player_name",
        "national_team_name",
        "opponent_team_name",
        "stat_minutesPlayed",
        "stat_rating",
    ]

    print(
        f"\nÖrnek — Aşama {stage_order}, pozisyon {position}:"
    )

    if example.empty:
        print("Kayıt bulunamadı.")
    else:
        print(example[columns].to_string(index=False))


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        type=Path,
        default=Path("../../data/processed/player_matches_analysis/player_match_stats.csv"),
        help="player_match_stats.csv dosyasının yolu",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("../../data/processed/weekly_team_analysis"),
        help="Çıktı klasörü",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=10,
        help="Her aşama ve pozisyon için aday sayısı",
    )
    parser.add_argument(
        "--min-minutes",
        type=float,
        default=1,
        help=(
            "Oyuncunun aday havuzuna girebilmesi için minimum dakika. "
            "Daha dengeli seçim için 30 veya 45 kullanılabilir."
        ),
    )

    return parser.parse_args()


def main():
    args = parse_args()

    player_pool = load_and_prepare(
        args.input,
        min_minutes=args.min_minutes,
    )

    stage_summary = create_stage_summary(player_pool)
    top_candidates = create_top_candidates(
        player_pool,
        top_n=args.top_n,
    )
    formation_teams = create_formation_teams(player_pool)
    formation_summary = create_formation_summary(formation_teams)

    save_outputs(
        args.output,
        stage_summary,
        top_candidates,
        formation_teams,
        formation_summary,
    )

    print_example(
        top_candidates,
        stage_order=1,
        position="D",
    )


if __name__ == "__main__":
    main()