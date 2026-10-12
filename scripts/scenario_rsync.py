"""Scenario A: consistent rsync snapshot-only baseline (no WAL replay).

Steps: reset->verify 100/20 -> stop PG -> rsync snapshot -> restart ->
workload 20 -> verify 120/40 -> incident -> verify 0 Garba -> stop ->
restore snapshot -> restart -> verify 100/20 (20 new rows LOST).
"""
import argparse
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from safety import require_lab, validate_rsync_paths  # noqa: E402
from common import sh, db, counts, wait_app, wait_db, log_run  # noqa: E402

SNAP_SRC = "/var/lib/postgresql/data/pgdata"
SNAP_DST = "/snapshots/rsync-baseline"
APP_URL = os.environ.get("APP_URL", "http://localhost:8000")


def compose(*args):
    return sh("docker", "compose", *args)


def exec_tools(*args):
    return sh("docker", "compose", "exec", "-T", "backup-tools", *args)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default="rsync-run1")
    ap.add_argument("--batch", default="rsync-post-snap")
    args = ap.parse_args()
    require_lab()
    t_start = time.time()

    print("=== ensure db running ===", flush=True)
    compose("start", "db")
    if not wait_db(180):
        sys.exit("db did not start")
    print(f"=== Scenario A {args.run_id}: reset ===", flush=True)
    c = db()
    with open("sql/reset.sql") as f:
        with c.cursor() as cur:
            cur.execute(f.read())
    with open("sql/schema.sql") as f:
        with c.cursor() as cur:
            cur.execute(f.read())
    with open("sql/seed.sql") as f:
        with c.cursor() as cur:
            cur.execute(f.read())
    total, garba = counts(c)
    print(f"seed state: total={total} garba={garba}", flush=True)
    assert (total, garba) == (100, 20), f"seed invariant failed: {total}/{garba}"
    baseline_total, baseline_garba = total, garba

    print("=== stop PG for consistent snapshot ===", flush=True)
    compose("stop", "db")
    time.sleep(5)

    validate_rsync_paths(SNAP_SRC, SNAP_DST)
    snap_t0 = time.time()
    exec_tools("mkdir", "-p", SNAP_DST)
    # exact mirror copy preserving ownership/permissions
    exec_tools("rsync", "-aHAX", "--delete", SNAP_SRC + "/", SNAP_DST + "/")
    snap_dur = time.time() - snap_t0
    manifest = (f"scenario_id={args.run_id}\ndataset_version=seed-v1\nsnapshot_timestamp={time.strftime('%Y-%m-%dT%H:%M:%S')}\n"
                f"baseline_total={baseline_total}\nbaseline_garba={baseline_garba}\n"
                f"pg=17 snapshot_tool=rsync status=ok duration_s={snap_dur:.1f}\n")
    # write manifest OUTSIDE the PGDATA copy
    r = subprocess.run(["docker", "compose", "exec", "-T", "backup-tools", "tee",
                        "/snapshots/rsync-baseline.MANIFEST"], input=manifest,
                       capture_output=True, text=True)
    print(manifest, flush=True)
    assert r.returncode == 0

    print("=== restart PG ===", flush=True)
    compose("start", "db")
    assert wait_db(180), "db did not come back after snapshot"
    assert wait_app(180), "app not healthy after snapshot"
    c = db()
    total, garba = counts(c)
    assert (total, garba) == (100, 20), f"post-snapshot state wrong: {total}/{garba}"

    print("=== workload: 20 HTTP registrations ===", flush=True)
    r = subprocess.run([sys.executable, "scripts/workload.py", "--count", "20",
                        "--batch", args.batch, "--start-index", "101",
                        "--out", "results/registration_requests.csv",
                        "--scenario", args.run_id])
    if r.returncode != 0:
        sys.exit("workload failed — aborting (no fictional success values)")
    c = db()
    pre_total, pre_garba = counts(c)
    print(f"pre-incident: total={pre_total} garba={pre_garba}", flush=True)
    assert (pre_total, pre_garba) == (120, 40), f"pre-incident invariant failed: {pre_total}/{pre_garba}"
    with c.cursor() as cur:
        cur.execute("SELECT id FROM bookings WHERE simulation_batch_id=%s ORDER BY id", (args.batch,))
        new_ids = [row[0] for row in cur.fetchall()]
    assert len(new_ids) == 20, f"expected 20 new ids, got {len(new_ids)}"

    print("=== incident: delete Garba bookings ===", flush=True)
    incident_ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open("sql/incident.sql") as f:
        with c.cursor() as cur:
            cur.execute(f.read())
    total_i, garba_i = counts(c)
    print(f"post-incident: total={total_i} garba={garba_i}", flush=True)
    assert garba_i == 0, "incident did not zero Garba bookings"

    print("=== restore snapshot ===", flush=True)
    rec_t0 = time.time()
    compose("stop", "db")
    time.sleep(5)
    validate_rsync_paths(SNAP_DST + "/", SNAP_SRC)
    exec_tools("rsync", "-aHAX", "--delete", SNAP_DST + "/", SNAP_SRC + "/")
    compose("start", "db")
    assert wait_db(240), "db did not recover after snapshot restore"
    assert wait_app(240), "app not ready after snapshot restore"
    restore_dur = time.time() - rec_t0
    app_ready_dur = time.time() - rec_t0  # measured to verified usable service
    c = db()
    rec_total, rec_garba = counts(c)
    with c.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM bookings WHERE simulation_batch_id=%s", (args.batch,))
        recovered_new = cur.fetchone()[0]
    print(f"recovered: total={rec_total} garba={rec_garba} recovered_new={recovered_new}", flush=True)
    success = (rec_total, rec_garba, recovered_new) == (100, 20, 0)

    log_run({"scenario_id": args.run_id, "backup_method": "rsync-snapshot-only-no-wal",
             "backup_type": "full-filesystem-mirror", "dataset_version": "seed-v1",
             "baseline_booking_count": baseline_total, "pre_incident_booking_count": pre_total,
             "recovered_booking_count": rec_total, "recovered_new_registration_count": recovered_new,
             "backup_duration_seconds": round(snap_dur, 1), "backup_size_bytes": "",
             "restore_duration_seconds": round(restore_dur, 1),
             "application_ready_duration_seconds": round(app_ready_dur, 1),
             "incident_timestamp": incident_ts, "recovery_target": "snapshot-time (NOT PITR)",
             "recovery_success": success,
             "notes": f"post-snapshot rows lost={20 - recovered_new}; IDs={','.join(new_ids[:5])}..."})
    print(f"Scenario A {'PASS' if success else 'DONE-with-mismatch'} in {time.time()-t_start:.0f}s", flush=True)
    if not success:
        print("NOTE: recovered state differs from the 100/20 invariant — see log.", flush=True)


if __name__ == "__main__":
    main()
