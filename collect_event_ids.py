import json
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright


TOURNAMENT_ID = 16
SEASON_ID = 58210

TOURNAMENT_PAGE = "https://www.sofascore.com/football/tournament/world/world-championship/16#id:58210"
BASE_API = "https://www.sofascore.com/api/v1"

OUTPUT_FILE = "event_ids.txt"


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

    # Request 403 verirse gerçek browser tab'ında dene
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    time.sleep(1)

    body_text = page.locator("body").inner_text(timeout=15000).strip()

    if body_text.startswith("{") or body_text.startswith("["):
        return json.loads(body_text)

    raise RuntimeError(f"JSON alınamadı. Status: {response.status} | URL: {url}")


def is_world_cup_event(event):
    tournament = event.get("tournament", {})
    unique_tournament = tournament.get("uniqueTournament", {})
    season = event.get("season", {})

    unique_tournament_id = unique_tournament.get("id")
    season_id = season.get("id")

    if unique_tournament_id != TOURNAMENT_ID:
        return False

    # Bazı response'larda season.id gelmeyebilir.
    # Gelirse kontrol ediyoruz, gelmezse elemek için kullanmıyoruz.
    if season_id is not None and season_id != SEASON_ID:
        return False

    return True


def event_date(event):
    ts = event.get("startTimestamp")

    if not ts:
        return ""

    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


def collect_from_last_pages(context, page, max_pages=20):
    """
    Geçmiş / oynanmış maçları sayfa sayfa çeker.
    Bu, DOM'dan link toplamaktan çok daha sağlam.
    """

    events = []
    empty_count = 0

    for page_number in range(max_pages):
        path = f"/unique-tournament/{TOURNAMENT_ID}/season/{SEASON_ID}/events/last/{page_number}"

        try:
            data = browser_json(context, page, path)
            page_events = data.get("events", [])

            valid_events = [e for e in page_events if is_world_cup_event(e)]

            print(
                f"last/{page_number}: {len(page_events)} event geldi, "
                f"{len(valid_events)} Dünya Kupası event'i"
            )

            if valid_events:
                events.extend(valid_events)
                empty_count = 0
            else:
                empty_count += 1

            # Art arda boş gelirse dur
            if empty_count >= 3:
                break

        except Exception as e:
            print(f"last/{page_number}: alınamadı -> {e}")
            empty_count += 1

            if empty_count >= 3:
                break

        time.sleep(0.5)

    return events


def collect_from_next_pages(context, page, max_pages=5):
    """
    Canlı / yaklaşan maçlar için.
    Senin analizinde scheduled maçlar zaten main.py'de atlanacak,
    ama canlı maç varsa yakalamak için burada topluyoruz.
    """

    events = []

    for page_number in range(max_pages):
        path = f"/unique-tournament/{TOURNAMENT_ID}/season/{SEASON_ID}/events/next/{page_number}"

        try:
            data = browser_json(context, page, path)
            page_events = data.get("events", [])

            valid_events = [e for e in page_events if is_world_cup_event(e)]

            print(
                f"next/{page_number}: {len(page_events)} event geldi, "
                f"{len(valid_events)} Dünya Kupası event'i"
            )

            events.extend(valid_events)

        except Exception as e:
            print(f"next/{page_number}: alınamadı -> {e}")

        time.sleep(0.5)

    return events


def collect_from_rounds(context, page, max_round=20):
    """
    Yedek yöntem.
    last/next az veri döndürürse round endpointlerini dener.
    """

    events = []

    for round_number in range(1, max_round + 1):
        path = f"/unique-tournament/{TOURNAMENT_ID}/season/{SEASON_ID}/events/round/{round_number}"

        try:
            data = browser_json(context, page, path)
            round_events = data.get("events", [])

            valid_events = [e for e in round_events if is_world_cup_event(e)]

            print(
                f"round/{round_number}: {len(round_events)} event geldi, "
                f"{len(valid_events)} Dünya Kupası event'i"
            )

            events.extend(valid_events)

        except Exception as e:
            print(f"round/{round_number}: alınamadı -> {e}")

        time.sleep(0.5)

    return events


def deduplicate_events(events):
    unique = {}

    for event in events:
        event_id = event.get("id")

        if event_id:
            unique[event_id] = event

    return list(unique.values())


def main():
    all_events = []

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

        print("Sofascore turnuva sayfası açılıyor...")
        page.goto(TOURNAMENT_PAGE, wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)

        print("\nGeçmiş maçlar çekiliyor...\n")
        all_events.extend(collect_from_last_pages(context, page, max_pages=25))

        print("\nYaklaşan / canlı maçlar çekiliyor...\n")
        all_events.extend(collect_from_next_pages(context, page, max_pages=5))

        # Eğer hâlâ az event varsa round endpointlerini dene
        unique_events = deduplicate_events(all_events)

        if len(unique_events) < 50:
            print("\nEvent sayısı az görünüyor. Round endpointleri deneniyor...\n")
            all_events.extend(collect_from_rounds(context, page, max_round=25))

        browser.close()

    unique_events = deduplicate_events(all_events)

    # Tarihe göre sırala
    unique_events.sort(key=lambda e: e.get("startTimestamp", 0))

    print("\nBulunan Dünya Kupası eventleri:")
    for event in unique_events:
        event_id = event.get("id")
        home = event.get("homeTeam", {}).get("name")
        away = event.get("awayTeam", {}).get("name")
        status = event.get("status", {}).get("type")
        score_home = event.get("homeScore", {}).get("current")
        score_away = event.get("awayScore", {}).get("current")
        date_str = event_date(event)

        print(
            f"{event_id} | {date_str} | {home} {score_home}-{score_away} {away} | {status}"
        )

    event_ids = [event["id"] for event in unique_events]

    Path(OUTPUT_FILE).write_text(
        "\n".join(str(event_id) for event_id in event_ids),
        encoding="utf-8"
    )

    print(f"\nToplam {len(event_ids)} event ID yazıldı: {OUTPUT_FILE}")

    print("\nPython listesi:")
    print("EVENT_IDS = [")
    for event_id in event_ids:
        print(f"    {event_id},")
    print("]")


if __name__ == "__main__":
    main()