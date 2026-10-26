import json
from datetime import datetime, timedelta
from pathlib import Path
import requests

BASE = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)


def get(url, params):
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data["data"] if isinstance(data, dict) else data


# Actuals: decisions in January cover delivery from 2 Jan to 1 Feb
actuals = get(f"{BASE}/FUELHH/stream", {
    "settlementDateFrom": "2026-01-01",
    "settlementDateTo": "2026-02-01",
    "fuelType": "WIND",
})
actuals = sorted(
    {a["startTime"]: {"startTime": a["startTime"], "generation": a["generation"]} for a in actuals}.values(),
    key=lambda x: x["startTime"],
)

# Forecasts: pulled in weekly chunks by publish time
forecasts = {}
start, end = datetime(2025, 12, 30), datetime(2026, 2, 2)
while start < end:
    stop = min(start + timedelta(days=7), end)
    rows = get(f"{BASE}/WINDFOR/stream", {
        "publishDateTimeFrom": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "publishDateTimeTo": stop.strftime("%Y-%m-%dT%H:%M:%SZ"),
    })
    for f in rows:
        key = (f["startTime"], f["publishTime"])
        forecasts[key] = {"startTime": f["startTime"], "publishTime": f["publishTime"], "generation": f["generation"]}
    start = stop

forecasts = sorted(forecasts.values(), key=lambda x: (x["startTime"], x["publishTime"]))

(OUT / "actuals.json").write_text(json.dumps(actuals))
(OUT / "forecasts.json").write_text(json.dumps(forecasts))

print("actuals:", len(actuals), "first:", actuals[0], "last:", actuals[-1])
print("forecasts:", len(forecasts), "first:", forecasts[0], "last:", forecasts[-1])