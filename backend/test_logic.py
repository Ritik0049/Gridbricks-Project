from datetime import datetime, timedelta, timezone

from logic import pick_forecast

T = datetime(2026, 1, 10, 12, tzinfo=timezone.utc)


def hours_before(h):
    return T - timedelta(hours=h)


ROWS = [(hours_before(30), 100), (hours_before(10), 200), (hours_before(3), 300)]


def test_picks_latest_forecast_before_cutoff():
    assert pick_forecast(ROWS, T, 4) == 200


def test_zero_horizon_uses_newest_forecast():
    assert pick_forecast(ROWS, T, 0) == 300


def test_forecast_published_exactly_at_cutoff_counts():
    assert pick_forecast(ROWS, T, 10) == 200


def test_returns_none_when_nothing_old_enough():
    assert pick_forecast(ROWS, T, 40) is None


def test_ignores_forecasts_older_than_48h():
    assert pick_forecast([(hours_before(50), 999)], T, 4) is None