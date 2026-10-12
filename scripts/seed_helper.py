"""Idempotent seed helper used by `make seed` (host-side)."""
import os
import psycopg2

URL = os.environ.get("DATABASE_URL", "postgresql://stagepass:stagepass@localhost:5433/stagepass")

c = psycopg2.connect(URL)
c.autocommit = True
for fn in ("sql/schema.sql", "sql/seed.sql"):
    with open(fn) as f:
        with c.cursor() as cur:
            cur.execute(f.read())
with c.cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM bookings")
    print("total bookings:", cur.fetchone()[0])
print("SEED OK")
