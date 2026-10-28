"""Download wind actuals (FUELHH) and wind forecasts (WINDFOR) from the Elexon BMRS API.

Run `python -m app.elexon` from the backend folder to refresh the files in data/.
"""

import json
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

API = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ACTUALS_FILE = DATA_DIR / "actuals.json"
FORECASTS_FILE = DATA_DIR / "forecasts.json"

# Purchase decisions are made in January 2026, one day before delivery,
# so delivery days are 2 Jan .. 1 Feb 2026.
DELIVERY_FROM = date(2026, 1, 2)
DELIVERY_TO = date(2026, 2, 1)
# Forecasts published up to 48 h before the first decision are kept, so the
# horizon analysis has data for every target time.
FORECAST_PUBLISH_FROM = datetime(2025, 12, 29, tzinfo=timezone.utc)
FORECAST_PUBLISH_TO = datetime(2026, 2, 2, tzinfo=timezone.utc)


def _get(dataset, params):
    url = f"{API}/{dataset}/stream?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.load(resp)


def fetch_actuals():
    """Half-hourly wind generation, one row per settlement period."""
    rows = []
    day = DELIVERY_FROM - timedelta(days=1)
    while day <= DELIVERY_TO + timedelta(days=1):
        end = min(day + timedelta(days=6), DELIVERY_TO + timedelta(days=1))
        rows += _get("FUELHH", {
            "settlementDateFrom": day.isoformat(),
            "settlementDateTo": end.isoformat(),
            "fuelType": "WIND",
        })
        day = end + timedelta(days=1)
    by_time = {r["startTime"]: r["generation"] for r in rows if r["fuelType"] == "WIND"}
    return [{"startTime": t, "generation": g} for t, g in sorted(by_time.items())]


def fetch_forecasts():
    """Every published wind forecast point (publishTime, startTime, generation)."""
    rows = []
    start = FORECAST_PUBLISH_FROM
    while start < FORECAST_PUBLISH_TO:
        end = min(start + timedelta(days=3), FORECAST_PUBLISH_TO)
        rows += _get("WINDFOR", {
            "publishDateTimeFrom": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "publishDateTimeTo": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
        start = end
    unique = {(r["publishTime"], r["startTime"]): r["generation"] for r in rows}
    return [
        {"publishTime": p, "startTime": s, "generation": g}
        for (p, s), g in sorted(unique.items())
    ]


def download():
    DATA_DIR.mkdir(exist_ok=True)
    actuals = fetch_actuals()
    forecasts = fetch_forecasts()
    ACTUALS_FILE.write_text(json.dumps(actuals, separators=(",", ":")))
    FORECASTS_FILE.write_text(json.dumps(forecasts, separators=(",", ":")))
    return len(actuals), len(forecasts)


if __name__ == "__main__":
    n_actuals, n_forecasts = download()
    print(f"saved {n_actuals} actuals and {n_forecasts} forecast points to {DATA_DIR}")
