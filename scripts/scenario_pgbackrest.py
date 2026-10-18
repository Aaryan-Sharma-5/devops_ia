"""Scenario B: pgBackRest + WAL + named PITR.

Steps: reset -> check -> full backup -> workload 20 -> restore point ->
verify WAL archived -> incident -> PITR restore --type=name -> verify 120/40.
"""
import argparse
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
from safety import require_lab  # noqa: E402
from common import sh, db, counts, wait_app, wait_db, log_run  # noqa: E402

STANZA = "stagepass"

# NOTE: pgBackRest control commands that need a live DB connection
# (stanza-create/check/backup/info) run via the db container (has the socket).
# `restore` needs no DB connection, so it runs via backup-tools (a RUNNING
# container sharing pgdata+repo) because `compose exec` cannot target the
# stopped db container.


def pgbackrest(*args):
    return sh("docker", "compose", "exec", "-T", "db", "su", "postgres", "-c",
              "pgbackrest --stanza=stagepass " + " ".join(args), capture=True)


def pgbackrest_restore(*args):
    return sh("docker", "compose", "exec", "-T", "backup-tools", "su", "postgres", "-c",
              "pgbackrest --stanza=stagepass " + " ".join(args), capture=True)


def parse_wal(fname: str):
    """Parse PostgreSQL 24-character hex WAL filename into (timeline, log_id, segment).

    WAL filenames are structured as:
      - Chars 0-7: Timeline ID (hex)
      - Chars 8-15: Log ID / logical xlog file (hex)
      - Chars 16-23: Segment ID within log (hex)
    Comparing integer tuples provides a timeline-aware and hexadecimal-safe
    ordering check across segment boundaries.
    """
    if not fname:
        return (0, 0, 0)
    clean_name = fname.strip().split(".")[0].split("-")[0]
    if len(clean_name) != 24:
        return (0, 0, 0)
    try:
        tli = int(clean_name[:8], 16)
        log = int(clean_name[8:16], 16)
        seg = int(clean_name[16:24], 16)
        return (tli, log, seg)
    except ValueError:
        return (0, 0, 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default="pgbackrest-run1")
    ap.add_argument("--batch", default="pbr-post-backup")
    args = ap.parse_args()
    require_lab()
    t_start = time.time()

    print("=== ensure db running ===", flush=True)
    sh("docker", "compose", "start", "db")
    if not wait_db(180):
        sys.exit("db did not start")
    print(f"=== Scenario B {args.run_id}: clean reset ===", flush=True)
    # wipe repo for a clean documented state (lab only)
    sh("docker", "compose", "exec", "-T", "backup-tools", "su", "postgres", "-c",
       "rm -rf /var/lib/pgbackrest/* && mkdir -p /var/lib/pgbackrest && chown postgres:postgres /var/lib/pgbackrest")
    c = db()
    for fn in ("sql/reset.sql", "sql/schema.sql", "sql/seed.sql"):
        with open(fn) as f:
            with c.cursor() as cur:
                cur.execute(f.read())
    total, garba = counts(c)
    assert (total, garba) == (100, 20), f"seed invariant failed: {total}/{garba}"

    print("=== B1: stanza-create + check ===", flush=True)
    sh("docker", "compose", "exec", "-T", "db", "su", "postgres", "-c",
       "pgbackrest --stanza=stagepass stanza-create", capture=True)
    chk = pgbackrest("check")
    print("check OK", flush=True)

    print("=== B2: full backup ===", flush=True)
    b_t0 = time.time()
    pgbackrest("--type=full", "backup")
    backup_dur = time.time() - b_t0
    info = pgbackrest("info", "--output=json")
    # info output is wrapped; extract json from captured stdout file? re-run capturing properly:
    r = subprocess.run(["docker", "compose", "exec", "-T", "db", "su", "postgres", "-c",
                        "pgbackrest --stanza=stagepass info --output=json"],
                       capture_output=True, text=True, timeout=120)
    try:
        # exec output may contain log prefix; find first '[' or '{'
        txt = r.stdout
        start = min([txt.find(x) for x in ("[{", "[") if txt.find(x) >= 0])
        meta = json.loads(txt[start:])
        binfo = meta[0]["backup"][-1]
        backup_id = binfo.get("label", "unknown")
    except Exception as e:  # noqa: BLE001
        print(f"info parse warning: {e}; raw tail: {r.stdout[-500:]}", flush=True)
        backup_id = "unknown"
    print(f"full backup id={backup_id} dur={backup_dur:.1f}s", flush=True)

    print("=== B3: workload 20 ===", flush=True)
    r = subprocess.run([sys.executable, "scripts/workload.py", "--count", "20",
                        "--batch", args.batch, "--start-index", "201",
                        "--out", "results/registration_requests.csv",
                        "--scenario", args.run_id])
    if r.returncode != 0:
        sys.exit("workload failed — aborting")
    c = db()
    pre_total, pre_garba = counts(c)
    assert (pre_total, pre_garba) == (120, 40), f"pre-incident invariant failed: {pre_total}/{pre_garba}"
    with c.cursor() as cur:
        cur.execute("SELECT id FROM bookings WHERE simulation_batch_id=%s ORDER BY id", (args.batch,))
        new_ids = [row[0] for row in cur.fetchall()]
    assert len(new_ids) == 20

    print("=== B4: named restore point + WAL archive verification ===", flush=True)
    rp_name = f"stagepass_before_incident_{args.run_id}".replace("-", "_")
    with c.cursor() as cur:
        cur.execute("SELECT pg_create_restore_point(%s)", (rp_name,))
        lsn = str(cur.fetchone()[0])
        cur.execute("SELECT now()")
        target_time = str(cur.fetchone()[0])
        # WAL file holding the restore-point record (must be archived before PITR).
        cur.execute("SELECT pg_walfile_name(%s::pg_lsn)", (lsn,))
        rp_walfile = str(cur.fetchone()[0])
        cur.execute("SELECT last_archived_wal, failed_count FROM pg_stat_archiver")
        _arch0, failed0 = cur.fetchone()
        cur.execute("SELECT pg_switch_wal()")
        switch_wal = str(cur.fetchone()[0])
    print(f"restore_point={rp_name} lsn={lsn} walfile={rp_walfile} time={target_time} switch={switch_wal}",
          flush=True)
    # WAIT until the segment containing the restore point is actually archived.
    # Check pg_stat_archiver using timeline-aware parsed WAL ordering AND verify
    # the exact segment exists in the pgBackRest archive directory.
    # Fail safely on timeout or on NEW archiver failures — never assume.
    deadline = time.time() + 240
    archived_ok = False
    rp_wal_tuple = parse_wal(rp_walfile)
    while time.time() < deadline:
        with c.cursor() as cur:
            cur.execute("SELECT last_archived_wal, last_archived_time, failed_count FROM pg_stat_archiver")
            wal, wtime, failed = cur.fetchone()
        # Verify exact target segment exists in pgBackRest archive path (handles .gz / suffixes)
        r3 = subprocess.run(["docker", "compose", "exec", "-T", "backup-tools", "su", "postgres", "-c",
                             f"find /var/lib/pgbackrest/archive/stagepass/17-1/ -name '*{rp_walfile}*' 2>/dev/null"],
                            capture_output=True, text=True, timeout=30)
        have_seg = bool((r3.stdout or "").strip())
        wal_tuple = parse_wal(wal)
        # Timeline-aware comparison: last archived WAL must be on the same timeline and >= target segment, or higher timeline
        wal_at_or_beyond = (wal_tuple[0] == rp_wal_tuple[0] and wal_tuple >= rp_wal_tuple) or (wal_tuple[0] > rp_wal_tuple[0])
        print(f"archiver: last={wal} (parsed={wal_tuple}) at={wtime} failed={failed}(was {failed0}) "
              f"target_wal={rp_walfile} (parsed={rp_wal_tuple}) have_seg={have_seg} wal_at_or_beyond={wal_at_or_beyond}",
              flush=True)
        if int(failed or 0) > int(failed0 or 0):
            sys.exit(f"REFUSED: NEW archive failures during wait (was {failed0}, now {failed}) — see db logs")
        if wal and wal_at_or_beyond and have_seg:
            archived_ok = True
            break
        time.sleep(5)
    if not archived_ok:
        sys.exit("REFUSED: required WAL not verified as archived before PITR — aborting (see archiver output above)")

    print("=== B5: incident ===", flush=True)
    incident_ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open("sql/incident.sql") as f:
        with c.cursor() as cur:
            cur.execute(f.read())
    total_i, garba_i = counts(c)
    assert garba_i == 0, "incident did not zero Garba"
    print(f"post-incident total={total_i} garba={garba_i} at {incident_ts}", flush=True)

    print("=== B6: PITR restore ===", flush=True)
    rec_t0 = time.time()
    sh("docker", "compose", "stop", "db")
    time.sleep(5)
    # Official restore procedure: clean the cluster directory first (pgBackRest
    # refuses to restore over existing files without --delta). Guard: exact
    # disposable lab PGDATA path only — never rm anywhere else.
    pgdata = "/var/lib/postgresql/data/pgdata"
    assert pgdata == "/var/lib/postgresql/data/pgdata", "refusing: unexpected PGDATA"
    sh("docker", "compose", "exec", "-T", "backup-tools", "su", "postgres", "-c",
       f"test \"{pgdata}\" != / -a \"{pgdata}\" != \"\" && rm -rf {pgdata}/* && mkdir -p {pgdata} && chown postgres:postgres {pgdata}")
    # pgBackRest restore with named target (official workflow); runs in
    # backup-tools (running container sharing pgdata+repo) since db is stopped.
    pgbackrest_restore(f"--type=name --target={rp_name} --target-action=promote restore")
    sh("docker", "compose", "start", "db")
    assert wait_db(300), "db did not come back after PITR"
    assert wait_app(300), "app not ready after PITR"
    restore_dur = time.time() - rec_t0
    # confirm recovery reached the named target via logs from current recovery run
    logs = subprocess.run(["docker", "compose", "logs", "db"], capture_output=True, text=True, timeout=60).stdout
    os.makedirs("results/logs", exist_ok=True)
    with open(f"results/logs/{args.run_id}-db-recovery.log", "w") as f:
        f.write(logs[-20000:])
    # Require explicit log evidence of stopping at/before the target named restore point
    target_stop_marker = f'recovery stopping at restore point "{rp_name}"'
    target_stop_before_marker = f'recovery stopping before restore point "{rp_name}"'
    hit = target_stop_marker in logs or target_stop_before_marker in logs
    print(f"recovery-target log evidence: {'found' if hit else 'NOT-FOUND (check log)'} for target '{rp_name}'", flush=True)
    assert hit, f"Target verification failed: log marker '{target_stop_marker}' not found in database logs"

    print("=== B7: verify ===", flush=True)
    c = db()
    rec_total, rec_garba = counts(c)
    with c.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM bookings WHERE simulation_batch_id=%s", (args.batch,))
        recovered_new = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM bookings b LEFT JOIN events e ON e.id=b.event_id WHERE e.id IS NULL")
        orphans = cur.fetchone()[0]
    print(f"recovered total={rec_total} garba={rec_garba} new={recovered_new} orphans={orphans}", flush=True)
    success = (rec_total, rec_garba, recovered_new, orphans) == (120, 40, 20, 0) and hit

    # repo size
    r3 = subprocess.run(["docker", "compose", "exec", "-T", "backup-tools", "su", "postgres", "-c",
                         "du -sb /var/lib/pgbackrest | cut -f1"],
                        capture_output=True, text=True, timeout=30)
    repo_bytes = (r3.stdout or "").strip().split()[0] if r3.stdout else ""
    log_run({"scenario_id": args.run_id, "backup_method": "pgbackrest+wal-pitr",
             "backup_type": "full+pitr-name", "dataset_version": "seed-v1",
             "baseline_booking_count": 100, "pre_incident_booking_count": pre_total,
             "recovered_booking_count": rec_total, "recovered_new_registration_count": recovered_new,
             "backup_duration_seconds": round(backup_dur, 1), "backup_size_bytes": repo_bytes,
             "restore_duration_seconds": round(restore_dur, 1),
             "application_ready_duration_seconds": round(restore_dur, 1),
             "incident_timestamp": incident_ts, "recovery_target": rp_name,
             "recovery_success": success,
             "notes": f"lsn={lsn} backup={backup_id} log_evidence={hit} new_ids_sample={','.join(new_ids[:5])}..."})
    print(f"Scenario B {'PASS' if success else 'DONE-with-mismatch — debug required'} in {time.time()-t_start:.0f}s",
          flush=True)
    assert success, f"Scenario B verification failed (counts={(rec_total, rec_garba, recovered_new, orphans)}, hit={hit})"


if __name__ == "__main__":
    main()
