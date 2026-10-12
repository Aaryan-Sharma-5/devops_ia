"""Shared helpers for scenario scripts (host-side)."""
import csv
import json
import os
import subprocess
import time
import urllib.request

import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://stagepass:stagepass@localhost:5433/stagepass")
APP_URL = os.environ.get("APP_URL", "http://localhost:8000")
COMPOSE = ["docker", "compose"]


def sh(*cmd, check=True, capture=False, timeout=600):
    print("+ " + " ".join(cmd), flush=True)
    r = subprocess.run(cmd, capture_output=capture, text=True, timeout=timeout)
    if capture:
        print(r.stdout[-2000:] if r.stdout else "", flush=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"command failed {r.returncode}: {' '.join(cmd)}\n{(r.stderr or '')[-2000:]}")
    return r


def db():
    for _ in range(30):
        try:
            c = psycopg2.connect(DATABASE_URL)
            c.autocommit = True
            return c
        except Exception:
            time.sleep(2)
    raise RuntimeError("cannot connect to database")


def counts(c):
    with c.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM bookings")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM bookings b JOIN events e ON e.id=b.event_id WHERE e.slug='kjsce-garba-eve'")
        garba = cur.fetchone()[0]
    return total, garba


def wait_app(timeout=180):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with urllib.request.urlopen(f"{APP_URL}/api/health", timeout=5) as r:
                d = json.loads(r.read().decode())
                if d.get("db", {}).get("status") == "ok":
                    return True
        except Exception:
            pass
        time.sleep(3)
    return False


def wait_db(timeout=180):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            c = psycopg2.connect(DATABASE_URL)
            c.close()
            return True
        except Exception:
            time.sleep(3)
    return False


def log_run(row: dict, path="results/experiment_runs.csv"):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if new:
            w.writeheader()
        w.writerow(row)
