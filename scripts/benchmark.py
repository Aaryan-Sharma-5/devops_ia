"""Experiment 2 (+3): backup-mode benchmarks + optional pg_dump comparison.

Sequence on a separate bench_payload table (default 20000 rows, --rows to reduce):
  full -> mutate ~5% -> differential -> mutate -> incremental.
Records durations, individual backup set sizes, cumulative repository sizes.
Optional --with-dump for pg_dump/pg_restore timing.
Trials: --trials N (default 1; report medians when 3).
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from safety import require_lab  # noqa: E402
from common import sh, db  # noqa: E402


def pbr(*args):
    r = subprocess.run(["docker", "compose", "exec", "-T", "db", "su", "postgres", "-c",
                        "pgbackrest --stanza=stagepass " + " ".join(args)],
                       capture_output=True, text=True, timeout=900)
    print(("+ pgbackrest " + " ".join(args))[-300:], flush=True)
    print((r.stdout or "")[-1500:], flush=True)
    if r.returncode != 0:
        raise RuntimeError(f"pgbackrest failed: {(r.stderr or '')[-1000:]}")
    return r.stdout


def repo_bytes():
    """Measure total cumulative repository size on disk."""
    r = subprocess.run(["docker", "compose", "exec", "-T", "backup-tools", "su", "postgres", "-c",
                        "du -sb /var/lib/pgbackrest | cut -f1"],
                       capture_output=True, text=True, timeout=60)
    return (r.stdout or "").strip().split()[0] if r.stdout else ""


def last_backup_info():
    """Extract individual backup delta size and backup set size from pgBackRest info."""
    r = subprocess.run(["docker", "compose", "exec", "-T", "db", "su", "postgres", "-c",
                        "pgbackrest --stanza=stagepass info --output=json"],
                       capture_output=True, text=True, timeout=120)
    txt = r.stdout
    idx = max(txt.find("["), 0)
    meta = json.loads(txt[idx:])
    b = meta[0]["backup"][-1]
    # backup_size is the individual compressed backup delta; size is total backup set
    b_info = b.get("info", {})
    backup_size = b_info.get("delta", b_info.get("size", 0))
    backup_set_size = b_info.get("size", backup_size)
    return b.get("label", ""), b.get("type", ""), backup_size, backup_set_size, b


def timed(fn):
    t0 = time.time()
    out = fn()
    return out, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=20000)
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--with-dump", action="store_true")
    ap.add_argument("--out", default="results/backup_benchmarks.csv")
    args = ap.parse_args()
    require_lab()
    os.makedirs("results", exist_ok=True)
    new = not os.path.exists(args.out)

    c = db()
    with open(args.out, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["trial", "backup_type", "rows", "duration_s", "backup_label",
                        "backup_size_bytes", "repository_total_bytes_after", "db_bytes", "notes"])
        for t in range(1, args.trials + 1):
            print(f"--- trial {t}: building {args.rows} bench rows ---", flush=True)
            with c.cursor() as cur:
                cur.execute("DROP TABLE IF EXISTS bench_payload")
                cur.execute("CREATE TABLE bench_payload(id SERIAL PRIMARY KEY, payload TEXT, updated INT DEFAULT 0)")
                cur.execute("INSERT INTO bench_payload(payload) SELECT repeat(md5(g::text),4) FROM generate_series(1,%s) g",
                            (args.rows,))
                cur.execute("SELECT pg_size_pretty(pg_total_relation_size('bench_payload'))")
                dbsize = cur.fetchone()[0]
                cur.execute("SELECT pg_total_relation_size('bench_payload')")
                dbbytes = cur.fetchone()[0]
            print(f"bench table size: {dbsize} ({dbbytes} bytes)", flush=True)

            (_, d_full), = [timed(lambda: pbr("--type=full", "backup"))]
            label, _bt, b_size, b_set_size, _info = last_backup_info()
            w.writerow([t, "full", args.rows, round(d_full, 1), label, b_size, repo_bytes(), dbbytes,
                        f"dbsize={dbsize}"])
            f.flush()

            with c.cursor() as cur:  # mutate ~5%
                cur.execute("UPDATE bench_payload SET payload=md5(payload||'d1'), updated=1 WHERE id % 20 = 0")
            (_, d_diff), = [timed(lambda: pbr("--type=diff", "backup"))]
            label, _bt, b_size, b_set_size, _info = last_backup_info()
            w.writerow([t, "differential", args.rows, round(d_diff, 1), label, b_size, repo_bytes(), dbbytes,
                        "mutated ~5% rows (id%20==0); page-level WAL means artifact ratio differs"])
            f.flush()

            with c.cursor() as cur:  # mutate another ~5%
                cur.execute("UPDATE bench_payload SET payload=md5(payload||'i1'), updated=2 WHERE id % 20 = 7")
            (_, d_incr), = [timed(lambda: pbr("--type=incr", "backup"))]
            label, _bt, b_size, b_set_size, _info = last_backup_info()
            w.writerow([t, "incremental", args.rows, round(d_incr, 1), label, b_size, repo_bytes(), dbbytes,
                        "mutated another ~5% (id%20==7)"])
            f.flush()
            print(f"trial {t} done: full={d_full:.1f}s diff={d_diff:.1f}s incr={d_incr:.1f}s", flush=True)

    if args.with_dump:
        print("--- pg_dump baseline ---", flush=True)
        t0 = time.time()
        sh("docker", "compose", "exec", "-T", "db", "su", "postgres", "-c",
           "pg_dump -Fc -d stagepass -f /tmp/stagepass.dump && ls -l /tmp/stagepass.dump", capture=True)
        dump_dur = time.time() - t0
        r = subprocess.run(["docker", "compose", "exec", "-T", "db", "su", "postgres", "-c",
                            "stat -c %s /tmp/stagepass.dump"], capture_output=True, text=True, timeout=60)
        dump_bytes = (r.stdout or "").strip()
        t0 = time.time()
        sh("docker", "compose", "exec", "-T", "db", "su", "postgres", "-c",
           "createdb stagepass_restore_test 2>/dev/null; pg_restore -d stagepass_restore_test --clean /tmp/stagepass.dump >/dev/null 2>&1; "
           "psql -d stagepass_restore_test -tAc 'SELECT COUNT(*) FROM bookings'", capture=True)
        restore_dur = time.time() - t0
        with open("results/recovery_benchmarks.csv", "a", newline="") as f:
            w = csv.writer(f)
            if os.path.getsize("results/recovery_benchmarks.csv") == 0:
                w.writerow(["method", "dump_duration_s", "artifact_bytes", "restore_duration_s", "selective_restore", "wal_replay"])
            w.writerow(["pg_dump-Fc", round(dump_dur, 1), dump_bytes, round(restore_dur, 1), "yes", "no-by-itself"])
        print(f"pg_dump: dump={dump_dur:.1f}s size={dump_bytes}B restore={restore_dur:.1f}s", flush=True)
    print("BENCHMARK OK", flush=True)


if __name__ == "__main__":
    main()
