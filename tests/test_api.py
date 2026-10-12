"""API + seed + safety tests (run against live `make up` stack)."""
import json
import os
import urllib.request

import psycopg2
import pytest

APP = os.environ.get("APP_URL", "http://localhost:8000")
DBURL = os.environ.get("DATABASE_URL", "postgresql://stagepass:stagepass@localhost:5433/stagepass")


def api(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(APP + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read().decode())
    except Exception as e:  # noqa: BLE001
        try:
            return e.code, json.loads(e.read().decode())  # type: ignore[attr-defined]
        except Exception:
            pytest.fail(f"API {method} {path} unreachable: {e}")


def db():
    c = psycopg2.connect(DBURL)
    c.autocommit = True
    return c


def test_health():
    st, d = api("GET", "/api/health")
    assert st == 200 and d["db"]["status"] == "ok"


def test_events_listed():
    st, d = api("GET", "/api/events")
    assert st == 200
    slugs = {e["slug"] for e in d["events"]}
    assert {"kjsce-garba-eve", "maker-weekend", "open-air-cinema"} <= slugs
    garba = next(e for e in d["events"] if e["slug"] == "kjsce-garba-eve")
    assert garba["title"] == "KJSCE Garba Eve — 12 October"


def test_register_creates_real_row():
    c = db()
    with c.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM bookings")
        before = cur.fetchone()[0]
    st, d = api("POST", "/api/events/kjsce-garba-eve/register",
                {"name": "Test User", "email": "pytest-smoke@example.test", "tickets": 2})
    assert st == 200 and d.get("booking_id"), d
    with c.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM bookings WHERE id=%s", (d["booking_id"],))
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*) FROM bookings")
        assert cur.fetchone()[0] == before + 1


def test_register_validation():
    st, d = api("POST", "/api/events/kjsce-garba-eve/register",
                {"name": "x", "email": "not-an-email", "tickets": 99})
    assert st == 400


def test_dashboard_summary_live_counts():
    st, d = api("GET", "/api/dashboard/summary")
    assert st == 200, d
    assert d["total_bookings"] >= 100
    assert d["garba_bookings"] >= 0
    slugs = {r["slug"] for r in d["per_event"]}
    assert {"kjsce-garba-eve", "maker-weekend", "open-air-cinema"} <= slugs
    # cross-check against SQL, not hardcoded values
    c = db()
    with c.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM bookings")
        assert d["total_bookings"] == cur.fetchone()[0]


def test_seed_idempotent_and_counts():
    c = db()
    for fn in ("sql/schema.sql", "sql/seed.sql", "sql/seed.sql"):
        with open(fn) as f:
            with c.cursor() as cur:
                cur.execute(f.read())
    with c.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM bookings")
        assert cur.fetchone()[0] >= 100  # seed rerunnable; smoke test may add rows


def test_safety_refuses_bad_paths():
    import sys
    sys.path.insert(0, "scripts")
    from safety import validate_rsync_paths
    with pytest.raises(SystemExit):
        validate_rsync_paths("", "/snapshots/x")
    with pytest.raises(SystemExit):
        validate_rsync_paths("/a", "/")


def test_safety_requires_lab(monkeypatch):
    import sys
    sys.path.insert(0, "scripts")
    import safety
    monkeypatch.setenv("STAGEPASS_LAB", "0")
    safety.LAB_FLAG = "0"
    with pytest.raises(SystemExit):
        safety.require_lab()
    monkeypatch.setenv("STAGEPASS_LAB", "1")
    safety.LAB_FLAG = "1"
