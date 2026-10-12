"""StagePass DB helper: request-scoped connections with retry (survives restores)."""
import os
import time
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://stagepass:stagepass@localhost:5433/stagepass")


def get_conn(retries: int = 12, delay: float = 2.0):
    last = None
    for _ in range(retries):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            conn.autocommit = False
            return conn
        except Exception as e:  # noqa: BLE001 - retry on any transient failure
            last = e
            time.sleep(delay)
    raise last


def query_all(sql: str, params=()):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return list(cur.fetchall())
    finally:
        conn.close()


def query_one(sql: str, params=()):
    rows = query_all(sql, params)
    return rows[0] if rows else None


def db_health():
    try:
        row = query_one("SELECT 1 AS ok, version() AS version")
        return {"status": "ok", "version": row["version"] if row else "unknown"}
    except Exception as e:  # noqa: BLE001
        return {"status": "unavailable", "error": str(e)[:300]}
