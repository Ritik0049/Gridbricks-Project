import json
import math
from bisect import bisect_right
from datetime import datetime, timedelta
from pathlib import Path

DATA = Path(__file__).parent / "data"
MAX_HORIZON_H = 48
HORIZONS = [0, 1, 2, 4, 6, 8, 12, 18, 24, 30, 36, 42, 48]


def parse(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def load_data():
    """Returns actuals {time: MW} and forecasts {time: [(publishTime, MW), ...] sorted}."""
    actuals = {
        parse(a["startTime"]): a["generation"]
        for a in json.loads((DATA / "actuals.json").read_text())
    }
    forecasts = {}
    for f in json.loads((DATA / "forecasts.json").read_text()):
        forecasts.setdefault(parse(f["startTime"]), []).append(
            (parse(f["publishTime"]), f["generation"])
        )
    for rows in forecasts.values():
        rows.sort()
    return actuals, forecasts


def pick_forecast(rows, target, horizon_h):
    """Latest forecast for `target` published at least `horizon_h` hours before it.
    Ignores forecasts older than 48h. Returns None if nothing qualifies."""
    cutoff = target - timedelta(hours=horizon_h)
    earliest = target - timedelta(hours=MAX_HORIZON_H)
    i = bisect_right(rows, (cutoff, float("inf")))
    if i == 0:
        return None
    publish_time, generation = rows[i - 1]
    if publish_time < earliest:
        return None
    return generation


def build_series(actuals, forecasts, start, end, horizon_h):
    points = []
    for t in sorted(actuals):
        if not (start <= t < end):
            continue
        rows = forecasts.get(t)
        f = pick_forecast(rows, t, horizon_h) if rows else None
        points.append({"time": t.isoformat(), "actual": actuals[t], "forecast": f})
    return points


def compute_metrics(points):
    pairs = [(p["actual"], p["forecast"]) for p in points if p["forecast"] is not None]
    if not pairs:
        return None
    errors = [f - a for a, f in pairs]
    abs_err = sorted(abs(e) for e in errors)
    n = len(errors)
    mae = sum(abs_err) / n
    mean_actual = sum(a for a, _ in pairs) / n
    return {
        "n": n,
        "mae": round(mae),
        "rmse": round(math.sqrt(sum(e * e for e in errors) / n)),
        "bias": round(sum(errors) / n),
        "p90_abs_error": round(abs_err[int(0.9 * (n - 1))]),
        "mae_pct": round(100 * mae / mean_actual, 1),
    }


def horizon_curve(actuals, forecasts, start, end):
    out = []
    for h in HORIZONS:
        m = compute_metrics(build_series(actuals, forecasts, start, end, h))
        if m:
            out.append({"horizon": h, "mae": m["mae"], "p90": m["p90_abs_error"]})
    return out