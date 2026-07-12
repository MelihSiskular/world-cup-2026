"""
SofaScore Dünya Kupası oyuncu-maç istatistiklerini indirir.

Girdi:
    event_ids.txt

Çıktılar:
    world_cup_data/raw/<event_id>.json
    world_cup_data/matches.csv
    world_cup_data/player_match_stats.csv
    world_cup_data/player_stats_long.csv
    world_cup_data/player_tournament_summary.csv

Kurulum:
    pip install pandas playwright pyarrow
    playwright install chromium
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
from playwright.sync_api import sync_playwright


TOURNAMENT_ID = 16
SEASON_ID = 58210
TOURNAMENT_PAGE = (
    "https://www.sofascore.com/football/tournament/"
    "world/world-championship/16#id:58210"
)
BASE_API = "https://www.sofascore.com/api/v1"

EVENT_IDS_FILE = Path("../../data/event_ids.txt")
OUTPUT_DIR = Path("../world_cup_data")
RAW_DIR = OUTPUT_DIR / "raw"

REQUEST_DELAY = 0.8
MAX_RETRIES = 3
FORCE_REFRESH = False

ISTANBUL = ZoneInfo("Europe/Istanbul")


def prepare_directories():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)


def read_event_ids():
    if not EVENT_IDS_FILE.exists():
        raise FileNotFoundError(f"Bulunamadı: {EVENT_IDS_FILE}")

    ids = []
    for line_no, line in enumerate(
        EVENT_IDS_FILE.read_text(encoding="utf-8").splitlines(), start=1
    ):
        value = line.strip()
        if not value or value.startswith("#"):
            continue
        try:
            ids.append(int(value))
        except ValueError as exc:
            raise ValueError(
                f"{EVENT_IDS_FILE}, satır {line_no} geçersiz: {value}"
            ) from exc

    return list(dict.fromkeys(ids))


def browser_json(context, page, path):
    """Önce request context, 403 olursa gerçek tarayıcı sekmesi."""
    url = f"{BASE_API}{path}"
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = context.request.get(
                url,
                headers={
                    "Accept": "application/json",
                    "Referer": TOURNAMENT_PAGE,
                    "X-Requested-With": "XMLHttpRequest",
                },
                timeout=30_000,
            )

            if response.status == 200:
                return response.json()

            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            time.sleep(1)
            text = page.locator("body").inner_text(timeout=15_000).strip()

            if text.startswith("{") or text.startswith("["):
                return json.loads(text)

            raise RuntimeError(f"HTTP {response.status}: {url}")

        except Exception as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(attempt * 2)

    raise RuntimeError(f"JSON alınamadı: {url}") from last_error


def flatten_dict(data, parent="", separator="_"):
    """İç içe statistics alanlarını CSV kolonlarına çevirir."""
    result = {}

    for key, value in data.items():
        new_key = f"{parent}{separator}{key}" if parent else key

        if isinstance(value, dict):
            result.update(flatten_dict(value, new_key, separator))
        elif isinstance(value, list):
            result[new_key] = json.dumps(value, ensure_ascii=False)
        else:
            result[new_key] = value

    return result


def iso_time(timestamp, tz):
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp, tz=tz).isoformat()


def get_cached_payload(event_id):
    path = RAW_DIR / f"{event_id}.json"

    if FORCE_REFRESH or not path.exists():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    event = payload.get("event", {})
    lineups = payload.get("lineups", {})

    if (
        event.get("status", {}).get("type") == "finished"
        and lineups.get("confirmed") is True
        and lineups.get("home")
        and lineups.get("away")
    ):
        return payload

    return None


def fetch_payload(context, page, event_id):
    cached = get_cached_payload(event_id)
    if cached:
        print("  Önbellekten okundu.")
        return cached

    event_json = browser_json(context, page, f"/event/{event_id}")
    lineups_json = browser_json(context, page, f"/event/{event_id}/lineups")

    event = event_json.get("event")
    if not event:
        raise ValueError("event nesnesi bulunamadı")

    payload = {
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "lineups": lineups_json,
    }

    path = RAW_DIR / f"{event_id}.json"
    temp = path.with_suffix(".tmp")
    temp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temp.replace(path)

    return payload


def make_match_row(event):
    tournament = event.get("tournament", {}).get("uniqueTournament", {})
    season = event.get("season", {})
    round_info = event.get("roundInfo", {})
    home = event.get("homeTeam", {})
    away = event.get("awayTeam", {})
    home_score = event.get("homeScore", {})
    away_score = event.get("awayScore", {})
    venue = event.get("venue", {})
    referee = event.get("referee", {})
    ts = event.get("startTimestamp")

    return {
        "event_id": event.get("id"),
        "start_timestamp": ts,
        "start_time_utc": iso_time(ts, timezone.utc),
        "start_time_istanbul": iso_time(ts, ISTANBUL),
        "status": event.get("status", {}).get("type"),
        "status_description": event.get("status", {}).get("description"),
        "tournament_id": tournament.get("id"),
        "season_id": season.get("id"),
        "round_number": round_info.get("round"),
        "round_name": round_info.get("name"),
        "home_team_id": home.get("id"),
        "home_team_name": home.get("name"),
        "away_team_id": away.get("id"),
        "away_team_name": away.get("name"),
        "home_score": home_score.get("current"),
        "away_score": away_score.get("current"),
        "home_score_normal_time": home_score.get("normaltime"),
        "away_score_normal_time": away_score.get("normaltime"),
        "home_score_overtime": home_score.get("overtime"),
        "away_score_overtime": away_score.get("overtime"),
        "home_score_penalties": home_score.get("penalties"),
        "away_score_penalties": away_score.get("penalties"),
        "venue_name": venue.get("name"),
        "venue_city": venue.get("city", {}).get("name"),
        "attendance": event.get("attendance"),
        "referee_name": referee.get("name"),
        "has_player_statistics": event.get("hasEventPlayerStatistics"),
        "has_xg": event.get("hasXg"),
    }


def appearance_type(is_substitute, stats):
    minutes = stats.get("minutesPlayed")

    if not is_substitute:
        return "starter"
    if isinstance(minutes, (int, float)) and minutes > 0:
        return "used_substitute"
    return "unused_substitute"


def make_player_rows(event, lineups):
    """Bir satır = bir oyuncunun bir maçtaki kaydı."""
    match = make_match_row(event)
    wide_rows = []
    long_rows = []

    side_teams = {
        "home": event.get("homeTeam", {}),
        "away": event.get("awayTeam", {}),
    }
    opponents = {
        "home": event.get("awayTeam", {}),
        "away": event.get("homeTeam", {}),
    }

    for side in ("home", "away"):
        side_data = lineups.get(side, {})
        national_team = side_teams[side]
        opponent = opponents[side]

        for entry in side_data.get("players", []):
            player = entry.get("player", {})
            stats = entry.get("statistics") or {}
            flat_stats = flatten_dict(stats)
            is_sub = bool(entry.get("substitute", False))

            base = {
                "event_id": event.get("id"),
                "start_time_utc": match["start_time_utc"],
                "start_time_istanbul": match["start_time_istanbul"],
                "round_number": match["round_number"],
                "round_name": match["round_name"],
                "match_status": match["status"],
                "home_team_name": match["home_team_name"],
                "away_team_name": match["away_team_name"],
                "home_score": match["home_score"],
                "away_score": match["away_score"],
                "side": side,
                "national_team_id": national_team.get("id"),
                "national_team_name": national_team.get("name"),
                "opponent_team_id": opponent.get("id"),
                "opponent_team_name": opponent.get("name"),

                # Dikkat: Bu alan millî takım değil, oyuncunun kulüp ID'si olabilir.
                "club_team_id_snapshot": entry.get("teamId"),

                "formation": side_data.get("formation"),
                "lineup_confirmed": lineups.get("confirmed"),
                "player_id": player.get("id"),
                "player_name": player.get("name"),
                "player_short_name": player.get("shortName"),
                "player_slug": player.get("slug"),
                "player_sofascore_id": player.get("sofascoreId"),
                "player_primary_position": player.get("position"),
                "lineup_position": entry.get("position"),
                "shirt_number": entry.get("shirtNumber"),
                "jersey_number": entry.get("jerseyNumber"),
                "is_starter": not is_sub,
                "is_substitute": is_sub,
                "appearance_type": appearance_type(is_sub, stats),
                "captain": bool(entry.get("captain", False)),
                "height_cm": player.get("height"),
                "country_alpha3": player.get("country", {}).get("alpha3"),
                "country_name": player.get("country", {}).get("name"),
                "date_of_birth_timestamp": player.get("dateOfBirthTimestamp"),
                "date_of_birth_utc": iso_time(
                    player.get("dateOfBirthTimestamp"), timezone.utc
                ),
                "market_value": player.get(
                    "proposedMarketValueRaw", {}
                ).get("value"),
                "market_value_currency": player.get(
                    "proposedMarketValueRaw", {}
                ).get("currency")
                or player.get("marketValueCurrency"),
            }

            wide = dict(base)
            wide.update({f"stat_{k}": v for k, v in flat_stats.items()})
            wide_rows.append(wide)

            for stat_name, stat_value in flat_stats.items():
                is_numeric = (
                    isinstance(stat_value, (int, float))
                    and not isinstance(stat_value, bool)
                )

                long_rows.append(
                    {
                        "event_id": event.get("id"),
                        "player_id": player.get("id"),
                        "player_name": player.get("name"),
                        "national_team_name": national_team.get("name"),
                        "opponent_team_name": opponent.get("name"),
                        "round_name": match["round_name"],
                        "stat_name": stat_name,
                        "stat_value_numeric": stat_value if is_numeric else None,
                        "stat_value_text": (
                            None
                            if is_numeric or stat_value is None
                            else str(stat_value)
                        ),
                    }
                )

    return wide_rows, long_rows


def ensure_numeric_columns(df, columns):
    for column in columns:
        if column not in df.columns:
            df[column] = 0
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)


def make_summary(player_match_df):
    if player_match_df.empty:
        return pd.DataFrame()

    df = player_match_df.copy()

    numeric = [
        "stat_minutesPlayed",
        "stat_rating",
        "stat_goals",
        "stat_goalAssist",
        "stat_expectedGoals",
        "stat_expectedAssists",
        "stat_totalShots",
        "stat_onTargetScoringAttempt",
        "stat_totalPass",
        "stat_accuratePass",
        "stat_totalTackle",
        "stat_interceptionWon",
        "stat_saves",
        "stat_goalsPrevented",
    ]
    ensure_numeric_columns(df, numeric)

    df["played"] = (df["stat_minutesPlayed"] > 0).astype(int)
    df["started"] = (
        df["is_starter"].fillna(False).astype(bool)
        & (df["stat_minutesPlayed"] > 0)
    ).astype(int)
    df["rating_minutes"] = (
        df["stat_rating"] * df["stat_minutesPlayed"]
    )

    summary = (
        df.groupby(
            [
                "player_id",
                "player_name",
                "national_team_id",
                "national_team_name",
            ],
            dropna=False,
            as_index=False,
        )
        .agg(
            squad_entries=("event_id", "nunique"),
            appearances=("played", "sum"),
            starts=("started", "sum"),
            minutes=("stat_minutesPlayed", "sum"),
            goals=("stat_goals", "sum"),
            assists=("stat_goalAssist", "sum"),
            xg=("stat_expectedGoals", "sum"),
            xa=("stat_expectedAssists", "sum"),
            shots=("stat_totalShots", "sum"),
            shots_on_target=("stat_onTargetScoringAttempt", "sum"),
            passes=("stat_totalPass", "sum"),
            accurate_passes=("stat_accuratePass", "sum"),
            tackles=("stat_totalTackle", "sum"),
            interceptions=("stat_interceptionWon", "sum"),
            saves=("stat_saves", "sum"),
            goals_prevented=("stat_goalsPrevented", "sum"),
            rating_minutes=("rating_minutes", "sum"),
        )
    )

    # pd.NA bazı pandas sürümlerinde object dtype oluşturduğu için
    # Series.round() sırasında TypeError verebilir. Burada float NaN kullanıyoruz.
    nonzero_minutes = (
        pd.to_numeric(summary["minutes"], errors="coerce")
        .astype("float64")
        .mask(lambda values: values.eq(0))
    )

    nonzero_passes = (
        pd.to_numeric(summary["passes"], errors="coerce")
        .astype("float64")
        .mask(lambda values: values.eq(0))
    )

    summary["weighted_rating"] = (
        pd.to_numeric(summary["rating_minutes"], errors="coerce")
        .astype("float64")
        .div(nonzero_minutes)
        .round(2)
    )

    summary["pass_accuracy_pct"] = (
        pd.to_numeric(summary["accurate_passes"], errors="coerce")
        .astype("float64")
        .mul(100)
        .div(nonzero_passes)
        .round(2)
    )

    summary["goals_per_90"] = (
        pd.to_numeric(summary["goals"], errors="coerce")
        .astype("float64")
        .mul(90)
        .div(nonzero_minutes)
        .round(3)
    )

    summary["assists_per_90"] = (
        pd.to_numeric(summary["assists"], errors="coerce")
        .astype("float64")
        .mul(90)
        .div(nonzero_minutes)
        .round(3)
    )

    summary["xg_per_90"] = (
        pd.to_numeric(summary["xg"], errors="coerce")
        .astype("float64")
        .mul(90)
        .div(nonzero_minutes)
        .round(3)
    )

    summary["xa_per_90"] = (
        pd.to_numeric(summary["xa"], errors="coerce")
        .astype("float64")
        .mul(90)
        .div(nonzero_minutes)
        .round(3)
    )

    return (
        summary.drop(columns="rating_minutes")
        .sort_values(
            ["national_team_name", "minutes"],
            ascending=[True, False],
        )
        .reset_index(drop=True)
    )


def save_table(df, name):
    csv_path = OUTPUT_DIR / f"{name}.csv"
    parquet_path = OUTPUT_DIR / f"{name}.parquet"

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"Yazıldı: {csv_path} ({len(df)} satır)")

    try:
        df.to_parquet(parquet_path, index=False)
        print(f"Yazıldı: {parquet_path}")
    except (ImportError, ModuleNotFoundError):
        print("Parquet atlandı. Kurulum: pip install pyarrow")


def main():
    prepare_directories()
    event_ids = read_event_ids()

    match_rows = []
    player_rows = []
    long_rows = []
    errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=30)

        context = browser.new_context(
            locale="tr-TR",
            timezone_id="Europe/Istanbul",
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
        )

        page = context.new_page()
        page.goto(
            TOURNAMENT_PAGE,
            wait_until="domcontentloaded",
            timeout=60_000,
        )
        time.sleep(4)

        for index, event_id in enumerate(event_ids, start=1):
            print(f"\n[{index}/{len(event_ids)}] Event {event_id}")

            try:
                payload = fetch_payload(context, page, event_id)
                event = payload["event"]
                lineups = payload["lineups"]

                tournament_id = (
                    event.get("tournament", {})
                    .get("uniqueTournament", {})
                    .get("id")
                )
                event_season_id = event.get("season", {}).get("id")

                if tournament_id != TOURNAMENT_ID:
                    print("  Dünya Kupası event'i değil, atlandı.")
                    continue

                if (
                    event_season_id is not None
                    and event_season_id != SEASON_ID
                ):
                    print("  Farklı sezon, atlandı.")
                    continue

                match_rows.append(make_match_row(event))

                if not lineups.get("home") or not lineups.get("away"):
                    print("  Lineup henüz bulunmuyor.")
                    continue

                wide, long = make_player_rows(event, lineups)
                player_rows.extend(wide)
                long_rows.extend(long)

                print(
                    f"  {len(wide)} oyuncu-maç satırı alındı."
                )

            except Exception as exc:
                print(f"  HATA: {exc}")
                errors.append(
                    {
                        "event_id": event_id,
                        "error": str(exc),
                        "time_utc": datetime.now(timezone.utc).isoformat(),
                    }
                )

            time.sleep(REQUEST_DELAY)

        browser.close()

    matches_df = pd.DataFrame(match_rows)
    players_df = pd.DataFrame(player_rows)
    long_df = pd.DataFrame(long_rows)

    if not matches_df.empty:
        matches_df = (
            matches_df
            .drop_duplicates("event_id", keep="last")
            .sort_values(["start_timestamp", "event_id"])
        )

    if not players_df.empty:
        players_df = (
            players_df
            .drop_duplicates(["event_id", "player_id"], keep="last")
            .sort_values(
                [
                    "start_time_utc",
                    "event_id",
                    "side",
                    "is_substitute",
                    "shirt_number",
                ]
            )
        )

    if not long_df.empty:
        long_df = (
            long_df
            .drop_duplicates(
                ["event_id", "player_id", "stat_name"],
                keep="last",
            )
            .sort_values(["event_id", "player_id", "stat_name"])
        )

    summary_df = make_summary(players_df)

    save_table(matches_df, "matches")
    save_table(players_df, "player_match_stats")
    save_table(long_df, "player_stats_long")
    save_table(summary_df, "player_tournament_summary")

    (OUTPUT_DIR / "errors.json").write_text(
        json.dumps(errors, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nTamamlandı. Hata sayısı: {len(errors)}")


if __name__ == "__main__":
    main()