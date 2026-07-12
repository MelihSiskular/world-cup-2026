import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from playwright.sync_api import sync_playwright


TOURNAMENT_PAGE = "https://www.sofascore.com/football/tournament/world/world-championship/16#id:58210"
BASE_API = "https://www.sofascore.com/api/v1"
EVENT_IDS_FILE = "event_ids.txt"

OUTPUT_GOALS_CSV = "world_cup_2026_goals_sofascore.csv"
OUTPUT_SUMMARY_CSV = "goal_minute_distribution.csv"

COLUMNS = [
    "event_id",
    "match",
    "home_team",
    "away_team",
    "score",
    "status",
    "round",
    "round_name",
    "date_utc",
    "scoring_country",
    "scorer",
    "player_country",
    "assist",
    "minute",
    "added_time",
    "minute_display",
    "minute_abs",
    "minute_bucket",
    "own_goal",
    "penalty",
    "source_url",
]


def read_event_ids(file_path=EVENT_IDS_FILE):
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"{file_path} bulunamadı. Aynı klasörde olduğundan emin ol.")

    text = path.read_text(encoding="utf-8")

    ids = [int(x) for x in re.findall(r"\d+", text)]

    # Tekrar eden ID'leri temizle, sırayı koru
    seen = set()
    unique_ids = []

    for event_id in ids:
        if event_id not in seen:
            unique_ids.append(event_id)
            seen.add(event_id)

    return unique_ids


def browser_json(context, page, path):
    url = f"{BASE_API}{path}"

    response = context.request.get(
        url,
        headers={
            "Accept": "application/json",
            "Referer": TOURNAMENT_PAGE,
            "X-Requested-With": "XMLHttpRequest",
        },
        timeout=30000,
    )

    if response.status == 200:
        return response.json()

    # Eğer request 403 vb. dönerse endpoint'i browser tab'ında açmayı dene
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    time.sleep(1)

    body_text = page.locator("body").inner_text(timeout=15000).strip()

    if body_text.startswith("{") or body_text.startswith("["):
        return json.loads(body_text)

    raise RuntimeError(f"JSON alınamadı. Status: {response.status} | URL: {url}")


def get_match_detail(context, page, event_id):
    data = browser_json(context, page, f"/event/{event_id}")

    # Bazı cevaplar {"event": {...}} şeklinde, bazıları direkt event objesi olabilir
    if isinstance(data, dict) and "event" in data:
        return data["event"]

    if isinstance(data, dict) and "homeTeam" in data and "awayTeam" in data:
        return data

    return None


def get_incidents(context, page, event_id):
    data = browser_json(context, page, f"/event/{event_id}/incidents")
    return data.get("incidents", [])


def minute_display(minute, added_time=None):
    if minute is None:
        return None

    if added_time:
        return f"{minute}+{added_time}"

    return str(minute)


def minute_bucket(minute, added_time=None):
    """
    45+2 golü 46-60 değil, 31-45+ sayılır.
    90+4 golü 76-90+ sayılır.
    """

    if minute is None:
        return "Bilinmiyor"

    if minute <= 15:
        return "0-15"
    elif minute <= 30:
        return "16-30"
    elif minute <= 45:
        return "31-45+"
    elif minute <= 60:
        return "46-60"
    elif minute <= 75:
        return "61-75"
    elif minute <= 90:
        return "76-90+"
    elif minute <= 105:
        return "91-105"
    else:
        return "106-120+"


def get_assist_name(incident):
    possible_assist_keys = ["assist1", "assist", "assistPlayer"]

    for key in possible_assist_keys:
        assist = incident.get(key)

        if isinstance(assist, dict):
            return assist.get("name")

    return None


def get_goal_events(context, page, event):
    event_id = event["id"]

    home_team = event["homeTeam"]["name"]
    away_team = event["awayTeam"]["name"]

    home_score = event.get("homeScore", {}).get("current")
    away_score = event.get("awayScore", {}).get("current")

    status_type = event.get("status", {}).get("type")

    match_name = f"{home_team} - {away_team}"

    round_info = event.get("roundInfo", {})
    round_number = round_info.get("round")
    round_name = round_info.get("name")

    start_timestamp = event.get("startTimestamp")

    if start_timestamp:
        date_utc = datetime.fromtimestamp(
            start_timestamp,
            tz=timezone.utc
        ).date().isoformat()
    else:
        date_utc = None

    incidents = get_incidents(context, page, event_id)

    rows = []

    for incident in incidents:
        if incident.get("incidentType") != "goal":
            continue

        minute = incident.get("time")
        added_time = incident.get("addedTime")

        # Penaltı serisi gibi dakikasız olayları almıyoruz
        if minute is None:
            continue

        incident_class = incident.get("incidentClass")
        is_home_event = incident.get("isHome")

        player_name = (
            incident.get("player", {}).get("name")
            or incident.get("playerName")
            or "Bilinmiyor"
        )

        assist_name = get_assist_name(incident)

        is_own_goal = incident_class == "ownGoal"
        is_penalty = incident_class == "penalty"

        if is_own_goal:
            scoring_country = away_team if is_home_event else home_team
            player_country = home_team if is_home_event else away_team
        else:
            scoring_country = home_team if is_home_event else away_team
            player_country = scoring_country

        rows.append({
            "event_id": event_id,
            "match": match_name,
            "home_team": home_team,
            "away_team": away_team,
            "score": f"{home_score}-{away_score}",
            "status": status_type,
            "round": round_number,
            "round_name": round_name,
            "date_utc": date_utc,
            "scoring_country": scoring_country,
            "scorer": player_name,
            "player_country": player_country,
            "assist": assist_name,
            "minute": minute,
            "added_time": added_time,
            "minute_display": minute_display(minute, added_time),
            "minute_abs": minute + (added_time or 0),
            "minute_bucket": minute_bucket(minute, added_time),
            "own_goal": is_own_goal,
            "penalty": is_penalty,
            "source_url": f"https://www.sofascore.com/event/{event_id}",
        })

    return rows


def analyze_goals(df):
    bucket_order = [
        "0-15",
        "16-30",
        "31-45+",
        "46-60",
        "61-75",
        "76-90+",
        "91-105",
        "106-120+",
    ]

    distribution = (
        df["minute_bucket"]
        .value_counts()
        .reindex(bucket_order)
        .fillna(0)
        .astype(int)
    )

    summary = distribution.reset_index()
    summary.columns = ["minute_bucket", "goal_count"]

    total_goals = summary["goal_count"].sum()

    if total_goals > 0:
        summary["percentage"] = summary["goal_count"] / total_goals * 100
        summary["percentage"] = summary["percentage"].round(2)
    else:
        summary["percentage"] = 0

    return summary


def main():
    event_ids = read_event_ids(EVENT_IDS_FILE)

    print(f"{len(event_ids)} event ID okundu.")
    print("Sofascore turnuva sayfası açılıyor...")

    goal_rows = []
    failed_ids = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=50,
        )

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
        page.goto(TOURNAMENT_PAGE, wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)

        for i, event_id in enumerate(event_ids, start=1):
            print(f"{i}/{len(event_ids)} - event_id={event_id}")

            try:
                event = get_match_detail(context, page, event_id)

                if not event:
                    print(f"   Maç detayı alınamadı: {event_id}")
                    failed_ids.append(event_id)
                    continue

                status_type = event.get("status", {}).get("type")

                if status_type not in ["finished", "inprogress"]:
                    home = event["homeTeam"]["name"]
                    away = event["awayTeam"]["name"]
                    print(f"   Atlandı: {home} vs {away} | status={status_type}")
                    continue

                home = event["homeTeam"]["name"]
                away = event["awayTeam"]["name"]

                home_score = event.get("homeScore", {}).get("current")
                away_score = event.get("awayScore", {}).get("current")

                print(f"   {home} {home_score}-{away_score} {away} | {status_type}")

                goals = get_goal_events(context, page, event)
                goal_rows.extend(goals)

                print(f"   Gol sayısı: {len(goals)}")

            except Exception as e:
                print(f"   Hata: {event_id} -> {e}")
                failed_ids.append(event_id)

            time.sleep(0.7)

        browser.close()

    df = pd.DataFrame(goal_rows, columns=COLUMNS)

    df.to_csv(
        OUTPUT_GOALS_CSV,
        index=False,
        encoding="utf-8-sig",
    )

    print("\nToplam gol kaydı:", len(df))

    if df.empty:
        print("\nHiç gol verisi çekilemedi.")
        print("event_ids.txt içindeki ID'lerin Sofascore maç ID'si olduğundan emin ol.")
        return

    summary = analyze_goals(df)

    summary.to_csv(
        OUTPUT_SUMMARY_CSV,
        index=False,
        encoding="utf-8-sig",
    )

    print("\nDakika aralığı dağılımı:")
    print(summary)

    late_goals = df[df["minute_bucket"] == "76-90+"]
    late_goal_rate = len(late_goals) / len(df) * 100

    print(f"\n76-90+ gol sayısı: {len(late_goals)} / {len(df)}")
    print(f"76-90+ gol oranı: %{late_goal_rate:.2f}")

    print("\nEn çok geç gol atan ülkeler:")
    print(
        late_goals["scoring_country"]
        .value_counts()
        .head(10)
    )

    print("\nEn geç gelen 10 gol:")
    print(
        df.sort_values("minute_abs", ascending=False)[
            ["match", "scoring_country", "scorer", "minute_display", "minute_bucket"]
        ].head(10)
    )

    if failed_ids:
        print("\nAlınamayan event ID'ler:")
        print(failed_ids)

    print("\nDosyalar oluşturuldu:")
    print(f"- {OUTPUT_GOALS_CSV}")
    print(f"- {OUTPUT_SUMMARY_CSV}")


if __name__ == "__main__":
    main()