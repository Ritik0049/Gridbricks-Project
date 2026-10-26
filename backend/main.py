from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from logic import build_series, compute_metrics, horizon_curve, load_data

app = FastAPI(title="Wind Forecast Monitor")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

ACTUALS, FORECASTS = load_data()


def to_range(start, end):
    s = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
    e = datetime.fromisoformat(end).replace(tzinfo=timezone.utc) + timedelta(days=1)
    return s, e


@app.get("/api/series")
def series(
    start: str = "2026-01-02",
    end: str = "2026-01-08",
    horizon: float = Query(4, ge=0, le=48),
):
    s, e = to_range(start, end)
    points = build_series(ACTUALS, FORECASTS, s, e, horizon)
    return {"points": points, "metrics": compute_metrics(points)}


@app.get("/api/horizon-curve")
def curve(start: str = "2026-01-02", end: str = "2026-02-01"):
    s, e = to_range(start, end)
    return horizon_curve(ACTUALS, FORECASTS, s, e)