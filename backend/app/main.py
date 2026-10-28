"""FastAPI app: JSON API under /api and the built React app at /."""

import json
import os
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import elexon
from .analysis import WindData, delivery_days, parse_day, parse_decision

DEFAULT_DECISION = "09:50"  # N2EX GB day-ahead auction gate closure (UK time)
FIRST_DAY, LAST_DAY = elexon.DELIVERY_FROM, elexon.DELIVERY_TO
STATIC_DIR = Path(os.environ.get("STATIC_DIR", Path(__file__).resolve().parent.parent / "static"))


def load_data():
    if not (elexon.ACTUALS_FILE.exists() and elexon.FORECASTS_FILE.exists()):
        elexon.download()
    return WindData(
        json.loads(elexon.ACTUALS_FILE.read_text()),
        json.loads(elexon.FORECASTS_FILE.read_text()),
    )


app = FastAPI(title="Wind forecast monitor")
app.state.data = None


def data():
    if app.state.data is None:
        app.state.data = load_data()
    return app.state.data


def decision_param(value):
    try:
        return parse_decision(value)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/meta")
def meta():
    return {
        "firstDay": FIRST_DAY.isoformat(),
        "lastDay": LAST_DAY.isoformat(),
        "defaultDecision": DEFAULT_DECISION,
    }


@app.get("/api/day")
def day(date: str, decision: str = DEFAULT_DECISION):
    try:
        d = parse_day(date)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not FIRST_DAY <= d <= LAST_DAY:
        raise HTTPException(400, f"date must be between {FIRST_DAY} and {LAST_DAY}")
    return data().day(d, decision_param(decision))


@app.get("/api/accuracy")
def accuracy(decision: str = DEFAULT_DECISION):
    return cached_accuracy(decision_param(decision))


@app.get("/api/horizon")
def horizon():
    return cached_horizon()


@lru_cache(maxsize=64)
def cached_accuracy(decision):
    return data().accuracy(delivery_days(FIRST_DAY, LAST_DAY), decision)


@lru_cache(maxsize=1)
def cached_horizon():
    return data().horizon(delivery_days(FIRST_DAY, LAST_DAY))


if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        file = STATIC_DIR / path
        if path and file.is_file() and STATIC_DIR in file.resolve().parents:
            return FileResponse(file)
        return FileResponse(STATIC_DIR / "index.html")
