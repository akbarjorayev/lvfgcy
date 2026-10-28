from datetime import date, time

from app.analysis import WindData, decision_moment, delivery_window, error_metrics, iso, percentile


def make_data():
    actuals = [
        {"startTime": "2026-01-10T00:00:00Z", "generation": 1000},
        {"startTime": "2026-01-10T00:30:00Z", "generation": 1100},
        {"startTime": "2026-01-10T01:00:00Z", "generation": 1200},
    ]
    forecasts = [
        # older forecast
        {"publishTime": "2026-01-09T07:30:00Z", "startTime": "2026-01-10T00:00:00Z", "generation": 800},
        {"publishTime": "2026-01-09T07:30:00Z", "startTime": "2026-01-10T01:00:00Z", "generation": 900},
        # the one available at a 09:50 decision
        {"publishTime": "2026-01-09T09:30:00Z", "startTime": "2026-01-10T00:00:00Z", "generation": 1300},
        {"publishTime": "2026-01-09T09:30:00Z", "startTime": "2026-01-10T01:00:00Z", "generation": 1000},
        # published after the decision: must not be used
        {"publishTime": "2026-01-09T11:30:00Z", "startTime": "2026-01-10T00:00:00Z", "generation": 1000},
    ]
    return WindData(actuals, forecasts)


def test_uses_latest_forecast_published_before_decision():
    day = make_data().day(date(2026, 1, 10), time(9, 50))
    assert day["decisionTime"] == "2026-01-09T09:50:00Z"
    assert day["forecastPublishTimes"] == ["2026-01-09T09:30:00Z"]
    rows = {r["time"]: r for r in day["rows"]}
    assert rows["2026-01-10T00:00:00Z"]["forecast"] == 1300
    assert rows["2026-01-10T00:30:00Z"]["forecast"] is None  # forecasts are hourly
    assert rows["2026-01-10T01:00:00Z"]["forecast"] == 1000


def test_earlier_decision_uses_older_forecast():
    rows = {r["time"]: r for r in make_data().day(date(2026, 1, 10), time(8, 0))["rows"]}
    assert rows["2026-01-10T00:00:00Z"]["forecast"] == 800


def test_no_forecast_before_any_publish():
    rows = make_data().day(date(2026, 1, 10), time(6, 0))["rows"]
    assert all(r["forecast"] is None for r in rows)


def test_day_metrics():
    m = make_data().day(date(2026, 1, 10), time(9, 50))["metrics"]
    # errors: 1300-1000 = 300, 1000-1200 = -200
    assert m["count"] == 2
    assert m["mae"] == 250
    assert m["bias"] == 50
    assert m["maxAbs"] == 300


def test_delivery_day_uses_uk_local_time():
    # 29 March 2026 is the clock change: 23 hours, starting at 00:00 GMT
    start, end = delivery_window(date(2026, 3, 29))
    assert (iso(start), iso(end)) == ("2026-03-29T00:00:00Z", "2026-03-29T23:00:00Z")
    # summer decision at 09:50 BST is 08:50 UTC
    assert iso(decision_moment(date(2026, 7, 2), time(9, 50))) == "2026-07-01T08:50:00Z"


def test_percentile_and_empty_metrics():
    assert percentile([1, 2, 3, 4], 50) == 2.5
    assert percentile([], 50) is None
    assert error_metrics([]) == {"count": 0}
