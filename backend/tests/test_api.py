from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_meta():
    assert client.get("/api/meta").json() == {
        "firstDay": "2026-01-02",
        "lastDay": "2026-02-01",
        "defaultDecision": "09:50",
    }


def test_day():
    body = client.get("/api/day", params={"date": "2026-01-15"}).json()
    assert len(body["rows"]) == 48
    assert body["decisionTime"] == "2026-01-14T09:50:00Z"
    assert body["metrics"]["count"] == 24


def test_day_validation():
    assert client.get("/api/day", params={"date": "2026-03-01"}).status_code == 400
    assert client.get("/api/day", params={"date": "nope"}).status_code == 400
    assert client.get("/api/accuracy", params={"decision": "25:00"}).status_code == 400


def test_accuracy_covers_whole_month():
    body = client.get("/api/accuracy").json()
    assert body["days"] == 31
    assert body["metrics"]["count"] == 31 * 24
    assert len(body["byHour"]) == 24
    assert sum(b["count"] for b in body["histogram"]) == body["metrics"]["count"]


def test_horizon():
    body = client.get("/api/horizon").json()
    assert [h["hours"] for h in body] == list(range(1, 49))
