"""Forecast selection and accuracy metrics.

Main rule: for a delivery day D, the buyer decides on day D-1 at the decision
time (UK local time). For every target time in D we use the latest forecast
published at or before that moment.
"""

import bisect
import math
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

UK = ZoneInfo("Europe/London")
HORIZONS = list(range(1, 49))


def parse_time(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def delivery_window(day):
    """UTC start (inclusive) and end (exclusive) of a UK delivery day."""
    start = datetime.combine(day, time(0), UK)
    end = datetime.combine(day + timedelta(days=1), time(0), UK)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def decision_moment(day, decision):
    """The moment the buyer decides for delivery `day`: D-1 at `decision` UK time."""
    return datetime.combine(day - timedelta(days=1), decision, UK).astimezone(timezone.utc)


def percentile(values, p):
    """Linear-interpolation percentile, p in 0..100."""
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * p / 100
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


class WindData:
    def __init__(self, actuals, forecasts):
        self.actuals = {parse_time(r["startTime"]): r["generation"] for r in actuals}
        # target time -> publish times (sorted) and generation values in the same order
        by_target = defaultdict(list)
        for r in forecasts:
            by_target[parse_time(r["startTime"])].append((parse_time(r["publishTime"]), r["generation"]))
        self.forecasts = {}
        for target, versions in by_target.items():
            versions.sort()
            self.forecasts[target] = ([p for p, _ in versions], [g for _, g in versions])

    def forecast_as_of(self, target, moment):
        """Latest forecast for `target` published at or before `moment`: (publishTime, MW) or None."""
        entry = self.forecasts.get(target)
        if not entry:
            return None
        publishes, values = entry
        i = bisect.bisect_right(publishes, moment) - 1
        if i < 0:
            return None
        return publishes[i], values[i]

    def day(self, day, decision):
        """Half-hourly actuals with the forecast available at decision time."""
        start, end = delivery_window(day)
        moment = decision_moment(day, decision)
        rows, used = [], set()
        t = start
        while t < end:
            f = self.forecast_as_of(t, moment)
            # the latest forecast published before the target time, for comparison
            latest = self.forecast_as_of(t, t)
            if f:
                used.add(f[0])
            rows.append({
                "time": iso(t),
                "actual": self.actuals.get(t),
                "forecast": f[1] if f else None,
                "latestForecast": latest[1] if latest else None,
            })
            t += timedelta(minutes=30)
        pairs = [(r["forecast"], r["actual"]) for r in rows
                 if r["forecast"] is not None and r["actual"] is not None]
        return {
            "date": day.isoformat(),
            "decisionTime": iso(moment),
            "forecastPublishTimes": sorted(iso(p) for p in used),
            "rows": rows,
            "metrics": error_metrics(pairs),
        }

    def pairs(self, days, decision):
        """(target, forecast, actual) for every target time where both exist."""
        out = []
        for d in days:
            start, end = delivery_window(d)
            moment = decision_moment(d, decision)
            t = start
            while t < end:
                f = self.forecast_as_of(t, moment)
                a = self.actuals.get(t)
                if f and a is not None:
                    out.append((t, f[1], a))
                t += timedelta(minutes=30)
        return out

    def accuracy(self, days, decision):
        pairs = self.pairs(days, decision)
        errors = [f - a for _, f, a in pairs]

        by_hour = defaultdict(list)
        by_day = defaultdict(list)
        for t, f, a in pairs:
            local = t.astimezone(UK)
            by_hour[local.hour].append((f, a))
            by_day[local.date()].append((f, a))

        start, end = delivery_window(days[0])[0], delivery_window(days[-1])[1]
        actual_values = [v for t, v in self.actuals.items() if start <= t < end]
        return {
            "decision": decision.strftime("%H:%M"),
            "days": len(days),
            "metrics": error_metrics([(f, a) for _, f, a in pairs]),
            # Shortfall buffer: forecast minus actual is positive when wind under-delivers.
            # "p90" means wind delivered at least (forecast - buffer) in 90% of periods.
            "shortfallBuffer": {p: round(percentile(errors, p)) for p in (80, 90, 95, 99)} if errors else {},
            "byHour": [{"hour": h, **error_metrics(by_hour[h])} for h in sorted(by_hour)],
            "byDay": [{"date": d.isoformat(), **error_metrics(by_day[d])} for d in sorted(by_day)],
            "histogram": histogram(errors, 1000),
            "actualPercentiles": {p: round(percentile(actual_values, p)) for p in (10, 50, 90)}
            if actual_values else {},
        }

    def horizon(self, days):
        """MAE and bias by how many hours before the target time the forecast was published."""
        start, end = delivery_window(days[0])[0], delivery_window(days[-1])[1]
        targets = sorted(t for t in self.forecasts if start <= t < end and t in self.actuals)
        out = []
        for h in HORIZONS:
            pairs = []
            for t in targets:
                f = self.forecast_as_of(t, t - timedelta(hours=h))
                if f:
                    pairs.append((f[1], self.actuals[t]))
            out.append({"hours": h, **error_metrics(pairs)})
        return out


def error_metrics(pairs):
    """Error statistics for (forecast, actual) pairs. Error = forecast - actual, in MW."""
    if not pairs:
        return {"count": 0}
    errors = [f - a for f, a in pairs]
    abs_errors = [abs(e) for e in errors]
    mean_actual = sum(a for _, a in pairs) / len(pairs)
    mae = sum(abs_errors) / len(errors)
    return {
        "count": len(errors),
        "mae": round(mae),
        "rmse": round(math.sqrt(sum(e * e for e in errors) / len(errors))),
        "bias": round(sum(errors) / len(errors)),
        "maxAbs": max(abs_errors),
        "p50Abs": round(percentile(abs_errors, 50)),
        "p90Abs": round(percentile(abs_errors, 90)),
        "p99Abs": round(percentile(abs_errors, 99)),
        "meanActual": round(mean_actual),
        "maePct": round(100 * mae / mean_actual, 1) if mean_actual else None,
    }


def histogram(values, width):
    if not values:
        return []
    counts = defaultdict(int)
    for v in values:
        counts[math.floor(v / width)] += 1
    lo, hi = min(counts), max(counts)
    return [{"from": b * width, "to": (b + 1) * width, "count": counts.get(b, 0)} for b in range(lo, hi + 1)]


def delivery_days(first, last):
    out, d = [], first
    while d <= last:
        out.append(d)
        d += timedelta(days=1)
    return out


def parse_decision(s):
    try:
        return datetime.strptime(s, "%H:%M").time()
    except ValueError:
        raise ValueError("decision must look like HH:MM") from None


def parse_day(s):
    try:
        return date.fromisoformat(s)
    except ValueError:
        raise ValueError("date must look like YYYY-MM-DD") from None
